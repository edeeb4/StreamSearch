

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def tmdb_get(endpoint: str, params=None):
    if params is None:
        params = {}

    if not TMDB_API_KEY:
        raise ValueError("TMDB_API_KEY is missing. Check your .env file.")

    params["api_key"] = TMDB_API_KEY

    response = requests.get(f"{BASE_URL}{endpoint}", params=params)
    response.raise_for_status()

    return response.json()


def get_popular_movies(page: int = 1):
    return tmdb_get("/movie/popular", {"page": page, "language": "en-US"})


def get_movie_details(movie_id: int):
    return tmdb_get(f"/movie/{movie_id}", {"language": "en-US"})


def get_movie_watch_providers(movie_id: int):
    return tmdb_get(f"/movie/{movie_id}/watch/providers")


def build_poster_url(poster_path):
    if not poster_path:
        return ""
    return f"{IMAGE_BASE_URL}{poster_path}"