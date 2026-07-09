from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.tmdb import get_popular_movies
from app.database import get_db
from app.models import Movie

router = APIRouter()


class MovieCreate(BaseModel):
    tmdb_id: int
    title: str
    overview: str | None = None
    genres: str | None = None
    runtime: int | None = None
    release_year: int | None = None
    poster_url: str | None = None
    streaming_providers: str | None = None
    mood_tags: str | None = None
    ending_type: str | None = "unknown"


class MovieResponse(BaseModel):
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

    class Config:
        from_attributes = True


@router.post("/", response_model=MovieResponse)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    new_movie = Movie(
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
        embedding=None,
    )

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return new_movie


@router.get("/", response_model=list[MovieResponse])
def get_movies(db: Session = Depends(get_db)):
    movies = db.query(Movie).all()
    return movies

@router.get("/tmdb/popular")
def test_tmdb_popular():
    data = get_popular_movies(page=1)
    return data