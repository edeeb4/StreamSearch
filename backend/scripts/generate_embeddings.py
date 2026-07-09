import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Movie
from app.embeddings import create_movie_text, create_embedding, embedding_to_json


def generate_embeddings():
    db = SessionLocal()

    movies = db.query(Movie).all()

    print(f"Found {len(movies)} movies.")

    updated_count = 0

    for movie in movies:
        if movie.embedding:
            print(f"Skipping existing embedding: {movie.title}")
            continue

        movie_text = create_movie_text(movie)
        embedding = create_embedding(movie_text)

        movie.embedding = embedding_to_json(embedding)

        db.add(movie)
        db.commit()

        updated_count += 1
        print(f"Generated embedding for: {movie.title}")

    db.close()

    print(f"Done. Generated {updated_count} embeddings.")


if __name__ == "__main__":
    generate_embeddings()