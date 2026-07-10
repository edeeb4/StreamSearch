import numpy as np
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity

from app.database import get_db
from app.embeddings import create_embedding, embedding_from_json
from app.models import Movie
from app.prompt_parser import extract_from_prompt

router = APIRouter()


class RecommendRequest(BaseModel):
    prompt: str
    genre: str | None = None
    provider: str | None = None
    max_runtime: int | None = None
    mood: str | None = None
    ending_type: str | None = None


class MovieRecommendation(BaseModel):
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
        from_attributes = True


def contains_text(source: str | None, target: str | None) -> bool:
    if not source or not target:
        return False

    return target.lower() in source.lower()


def build_search_terms(request: RecommendRequest) -> dict:
    extracted = extract_from_prompt(request.prompt)

    genres = extracted["genres"]
    moods = extracted["moods"]

    if request.genre and request.genre not in genres:
        genres.append(request.genre)

    if request.mood and request.mood not in moods:
        moods.append(request.mood)

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
    score = 0.0
    reasons = []

    genres = search_terms["genres"]
    moods = search_terms["moods"]
    provider = search_terms["provider"]
    max_runtime = search_terms["max_runtime"]
    ending_type = search_terms["ending_type"]

    matched_genres = [
        genre for genre in genres
        if contains_text(movie.genres, genre)
    ]

    matched_moods = [
        mood for mood in moods
        if contains_text(movie.mood_tags, mood)
    ]

    for genre in matched_genres:
        score += 0.16
        reasons.append(f"matches the {genre} genre")

    for mood in matched_moods:
        score += 0.10
        reasons.append(f"matches the mood '{mood}'")

    if provider and contains_text(movie.streaming_providers, provider):
        score += 0.10
        reasons.append(f"is available on {provider}")

    if max_runtime and movie.runtime:
        if movie.runtime <= max_runtime:
            score += 0.07
            reasons.append(f"is under {max_runtime} minutes")
        else:
            score -= 0.08

    if ending_type and contains_text(movie.ending_type, ending_type):
        score += 0.12
        reasons.append(f"has a {ending_type} ending")

    # Important penalty:
    # If the prompt asked for romance but the movie is not romance/romantic,
    # push it down. This prevents Toy Story-type results from winning.
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

    enhanced_prompt = f"""
    User request: {request.prompt}
    Desired genres: {", ".join(search_terms["genres"])}
    Desired moods: {", ".join(search_terms["moods"])}
    Desired provider: {search_terms["provider"]}
    Desired runtime: {search_terms["max_runtime"]}
    Desired ending: {search_terms["ending_type"]}
    """

    user_embedding = create_embedding(enhanced_prompt)
    user_vector = np.array(user_embedding).reshape(1, -1)

    movies = db.query(Movie).filter(Movie.embedding.isnot(None)).all()

    recommendations = []

    for movie in movies:
        movie_embedding = embedding_from_json(movie.embedding)
        movie_vector = np.array(movie_embedding).reshape(1, -1)

        similarity = cosine_similarity(user_vector, movie_vector)[0][0]

        bonus, reasons = metadata_score(movie, search_terms)

        final_score = float(similarity + bonus)

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

    recommendations.sort(key=lambda movie: movie.score, reverse=True)

    return recommendations[:10]