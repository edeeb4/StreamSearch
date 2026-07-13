#Utilities for creating and serializing semantic movie embeddings

#movie metadata is converted into a decriptive text block before being encoded byt he shared sentence transformer model. The resulting embedding is stored in the database as a JSON string.

import json
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def create_movie_text(movie):
    return f"""
    Title: {movie.title}
    Overview: {movie.overview}
    Genres: {movie.genres}
    Runtime: {movie.runtime} minutes
    Release year: {movie.release_year}
    Streaming providers: {movie.streaming_providers}
    Mood tags: {movie.mood_tags}
    Ending type: {movie.ending_type}
    """


def create_embedding(text: str) -> list[float]:
    embedding = model.encode(text)
    return embedding.tolist()


def embedding_to_json(embedding: list[float]) -> str:
    return json.dumps(embedding)


def embedding_from_json(embedding_json: str) -> list[float]:
    return json.loads(embedding_json)