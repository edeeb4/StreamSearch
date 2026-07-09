import numpy as np
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity

from app.database import get_db
from app.embeddings import create_embedding, embedding_from_json
from app.models import Movie

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


def metadata_bonus(movie: Movie, request: RecommendRequest) -> tuple[float, list[str]]:
    bonus = 0
    reasons = []

    if request.genre and contains_text(movie.genres, request.genre):
        bonus += 0.10
        reasons.append(f"matches the {request.genre} genre")

    if request.provider and contains_text(movie.streaming_providers, request.provider):
        bonus += 0.10
        reasons.append(f"is available on {request.provider}")

    if request.max_runtime and movie.runtime:
        if movie.runtime <= request.max_runtime:
            bonus += 0.07
            reasons.append(f"is under {request.max_runtime} minutes")

    if request.mood and contains_text(movie.mood_tags, request.mood):
        bonus += 0.08
        reasons.append(f"matches the mood '{request.mood}'")

    if request.ending_type and contains_text(movie.ending_type, request.ending_type):
        bonus += 0.08
        reasons.append(f"has a {request.ending_type} ending")

    return bonus, reasons


@router.post("/", response_model=list[MovieRecommendation])
def recommend_movies(request: RecommendRequest, db: Session = Depends(get_db)):
    user_embedding = create_embedding(request.prompt)
    user_vector = np.array(user_embedding).reshape(1, -1)

    movies = db.query(Movie).filter(Movie.embedding.isnot(None)).all()

    recommendations = []

    for movie in movies:
        movie_embedding = embedding_from_json(movie.embedding)
        movie_vector = np.array(movie_embedding).reshape(1, -1)

        similarity = cosine_similarity(user_vector, movie_vector)[0][0]

        bonus, reasons = metadata_bonus(movie, request)

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