import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, Movie
from scripts.seed_movies import seed_movies
from scripts.tag_movies import tag_movies
from scripts.generate_embeddings import generate_embeddings


def database_has_movies() -> bool:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        count = db.query(Movie).count()
        return count > 0
    finally:
        db.close()


if __name__ == "__main__":
    if database_has_movies():
        print("Database already has movies. Skipping setup.")
    else:
        print("Setting up production database...")
        seed_movies()
        tag_movies()
        generate_embeddings()
        print("Production setup complete.")