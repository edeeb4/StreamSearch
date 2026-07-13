import numpy as np
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity

from app.database import get_db
from app.embeddings import create_embedding, embedding_from_json
from app.models import Movie
from app.prompt_parser import extract_from_prompt

router = APIRouter() #this router is mounted at /recommend in app.main


class RecommendRequest(BaseModel):
    #input accepted by the recommendation endpoint. The prompt is required, while other fields are optional.
    prompt: str
    genre: str | None = None
    provider: str | None = None
    max_runtime: int | None = None
    mood: str | None = None
    ending_type: str | None = None


class MovieRecommendation(BaseModel):
    #public representation of a ranked movie recommendation, including the score and explanation for why it was recommended.
    id: int
    tmdb_id: int
    title: str
    overview: str | None = None
    genres: str | None = None
    runtime: int | None = None
    release_year: int | None = None
    poster_url: str | None = None
    streaming_providers: str | None = None
    mood_tags: str | None = None
    ending_type: str | None = None
    score: float
    explanation: str

    class Config:
        #allows Pydantic to read data from SQLAlchemy models directly
        from_attributes = True


def contains_text(source: str | None, target: str | None) -> bool:
    #Return whether ``target`` appears inside ``source``, ignoring case
    if not source or not target:
        return False

    return target.lower() in source.lower()


def build_search_terms(request: RecommendRequest) -> dict:
    #Merge inferred prompt filters with explicitly supplied request filters.
    extracted = extract_from_prompt(request.prompt)

    #copy these lists because they may be extended with explicit filters
    genres = extracted["genres"]
    moods = extracted["moods"]

    #prevents duplicate values when the explicit filter was already detected
    if request.genre and request.genre not in genres:
        genres.append(request.genre)

    if request.mood and request.mood not in moods:
        moods.append(request.mood)

    #explicit form values overried inferred values from natural languae
    provider = request.provider or extracted["provider"]
    max_runtime = request.max_runtime or extracted["max_runtime"]
    ending_type = request.ending_type or extracted["ending_type"]

    return {
        "genres": genres,
        "moods": moods,
        "provider": provider,
        "max_runtime": max_runtime,
        "ending_type": ending_type,
    }


def metadata_score(movie: Movie, search_terms: dict) -> tuple[float, list[str]]:
    #calculate the metadata adjustment applied to semantic similarity
    score = 0.0
    reasons = []

    genres = search_terms["genres"]
    moods = search_terms["moods"]
    provider = search_terms["provider"]
    max_runtime = search_terms["max_runtime"]
    ending_type = search_terms["ending_type"]

    #a rquest can contain more than one genre or mood, so collect every matching value rather than stopping after first math.
    matched_genres = [
        genre for genre in genres
        if contains_text(movie.genres, genre)
    ]

    matched_moods = [
        mood for mood in moods
        if contains_text(movie.mood_tags, mood)
    ]

    #genre natch recieve a relatively strong bonus because genre is often one the clearest indicators of what the user wants to watch
    for genre in matched_genres:
        score += 0.16
        reasons.append(f"matches the {genre} genre")

    # mood matches are usful but slightly less specific than genre matches, so they receive a smaller bonus
    for mood in matched_moods:
        score += 0.10
        reasons.append(f"matches the mood '{mood}'")

    # provider matching only affects the score when the user requested one
    if provider and contains_text(movie.streaming_providers, provider):
        score += 0.10
        reasons.append(f"is available on {provider}")

    if max_runtime and movie.runtime:
        if movie.runtime <= max_runtime: #reward movies that satifsy the users max runtime
            score += 0.07
            reasons.append(f"is under {max_runtime} minutes")
        else: # a movie can still appear when it exceeds the limit, but the penalty makes it less likely to be recommended
            score -= 0.08

    if ending_type and contains_text(movie.ending_type, ending_type):
        score += 0.12
        reasons.append(f"has a {ending_type} ending")

    # Important penalty:
    # If the prompt asked for romance but the movie is not romance/romantic, push it down. This prevents Toy Story-type results from winning.
    wants_romance = "Romance" in genres or "romantic" in moods
    movie_is_romantic = (
        contains_text(movie.genres, "Romance")
        or contains_text(movie.mood_tags, "romantic")
    )

    if wants_romance and not movie_is_romantic:
        score -= 0.25

    # Similar penalty for horror/scary searches.
    wants_horror = "Horror" in genres or "scary" in moods
    movie_is_horror = (
        contains_text(movie.genres, "Horror")
        or contains_text(movie.mood_tags, "scary")
    )

    if wants_horror and not movie_is_horror:
        score -= 0.20

    return score, reasons


@router.post("/", response_model=list[MovieRecommendation])
def recommend_movies(request: RecommendRequest, db: Session = Depends(get_db)):
    search_terms = build_search_terms(request)

    #include extracted filters in the text sent to the embedding model. gives semantic model clearer contected than the raw prompt alone, which improves the quality of the embedding and the resulting recommendations.
    enhanced_prompt = f"""
    User request: {request.prompt}
    Desired genres: {", ".join(search_terms["genres"])}
    Desired moods: {", ".join(search_terms["moods"])}
    Desired provider: {search_terms["provider"]}
    Desired runtime: {search_terms["max_runtime"]}
    Desired ending: {search_terms["ending_type"]}
    """

    # scikit-learn expected a 2D array containing one or more samples, so we reshape the 1D embedding into a 2D array with one row and many columns.
    user_embedding = create_embedding(enhanced_prompt)
    user_vector = np.array(user_embedding).reshape(1, -1)

    #ignore movies that have not yet been embedded, since they cannot be compared to the user request. This is a temporary measure until all movies are embedded.
    movies = db.query(Movie).filter(Movie.embedding.isnot(None)).all()

    recommendations = []

    for movie in movies:
        #convert the movie's embedding from JSON to a numpy array and reshape it into a 2D array for similarity comparison
        movie_embedding = embedding_from_json(movie.embedding)
        movie_vector = np.array(movie_embedding).reshape(1, -1)

        # cosine similarity returns a 2D array of shape (n_samples_1, n_samples_2), so we extract the single value from the resulting array.
        similarity = cosine_similarity(user_vector, movie_vector)[0][0]

        bonus, reasons = metadata_score(movie, search_terms)

        final_score = float(similarity + bonus)

        #some movies may match semantically without matching any of the metadata filters, so provide a fallback explanation for why the movie was recommended.
        if not reasons:
            reasons.append("semantically matches your request")

        recommendations.append(
            MovieRecommendation(
                id=movie.id,
                tmdb_id=movie.tmdb_id,
                title=movie.title,
                overview=movie.overview,
                genres=movie.genres,
                runtime=movie.runtime,
                release_year=movie.release_year,
                poster_url=movie.poster_url,
                streaming_providers=movie.streaming_providers,
                mood_tags=movie.mood_tags,
                ending_type=movie.ending_type,
                score=round(final_score, 4),
                explanation="This movie " + ", ".join(reasons) + ".",
            )
        )

    recommendations.sort(key=lambda movie: movie.score, reverse=True) #rank from the strongest to weakest combinded similarity score.

    return recommendations[:10] #limit the response so the frontend recieves a manageable result set