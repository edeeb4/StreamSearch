#Seed the local movie database with popular titles and metadata from TMDB.

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, Movie
from app.tmdb import (
    get_popular_movies,
    get_movie_details,
    get_movie_watch_providers,
    build_poster_url,
)

Base.metadata.create_all(bind=engine)

db = SessionLocal()


def get_us_streaming_providers(tmdb_id: int) -> str:
    try:
        data = get_movie_watch_providers(tmdb_id)
        us_data = data.get("results", {}).get("US", {})
        flatrate = us_data.get("flatrate", [])

        provider_names = [provider["provider_name"] for provider in flatrate]

        return ", ".join(provider_names)

    except Exception as error:
        print(f"Could not get streaming providers for TMDB ID {tmdb_id}: {error}")
        return ""


def seed_movies():
    total_added = 0

    for page in range(1, 6):
        print(f"Fetching popular movies page {page}...")

        popular_data = get_popular_movies(page=page)
        movies = popular_data.get("results", [])

        for item in movies:
            tmdb_id = item.get("id")

            existing_movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()

            if existing_movie:
                print(f"Skipping existing movie: {existing_movie.title}")
                continue

            try:
                details = get_movie_details(tmdb_id)

                genres = ", ".join(
                    [genre["name"] for genre in details.get("genres", [])]
                )

                release_date = details.get("release_date")
                release_year = None

                if release_date:
                    release_year = int(release_date[:4])

                providers = get_us_streaming_providers(tmdb_id)

                movie = Movie(
                    tmdb_id=tmdb_id,
                    title=details.get("title"),
                    overview=details.get("overview"),
                    genres=genres,
                    runtime=details.get("runtime"),
                    release_year=release_year,
                    poster_url=build_poster_url(details.get("poster_path")),
                    streaming_providers=providers,
                    mood_tags="",
                    ending_type="unknown",
                    embedding=None,
                )

                db.add(movie)
                db.commit()
                db.refresh(movie)

                total_added += 1
                print(f"Added: {movie.title}")

            except Exception as error:
                print(f"Error adding movie with TMDB ID {tmdb_id}: {error}")

    db.close()
    print(f"Done. Added {total_added} new movies.")


if __name__ == "__main__":
    seed_movies()