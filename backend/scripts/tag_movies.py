import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Movie


MOOD_KEYWORDS = {
    "funny": ["comedy", "comic", "hilarious", "funny", "laugh"],
    "romantic": ["romance", "romantic", "love", "relationship", "wedding"],
    "dark": ["dark", "murder", "crime", "violent", "killer", "death"],
    "suspenseful": ["thriller", "suspense", "mystery", "danger", "secret"],
    "emotional": ["drama", "family", "loss", "grief", "heartbreaking"],
    "action-packed": ["action", "fight", "battle", "war", "mission", "hero"],
    "scary": ["horror", "haunted", "demon", "ghost", "terrifying"],
    "lighthearted": ["comedy", "family", "adventure", "fun", "charming"],
    "inspiring": ["inspire", "dream", "hope", "journey", "true story"],
    "mind-bending": ["sci-fi", "science fiction", "time", "reality", "dream"],
}


ENDING_RULES = {
    "happy": ["comedy", "romance", "family", "animation", "adventure"],
    "sad": ["tragedy", "loss", "grief", "death"],
    "ambiguous": ["thriller", "mystery", "psychological"],
    "bittersweet": ["drama", "war", "history"],
}


def normalize_text(movie: Movie) -> str:
    return f"""
    {movie.title}
    {movie.overview}
    {movie.genres}
    """.lower()


def infer_mood_tags(movie: Movie) -> str:
    text = normalize_text(movie)
    tags = []

    for mood, keywords in MOOD_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                tags.append(mood)
                break

    if not tags:
        tags.append("general")

    return ", ".join(tags[:5])


def infer_ending_type(movie: Movie) -> str:
    text = normalize_text(movie)

    for ending, keywords in ENDING_RULES.items():
        for keyword in keywords:
            if keyword in text:
                return ending

    return "unknown"


def tag_movies():
    db = SessionLocal()
    movies = db.query(Movie).all()

    print(f"Found {len(movies)} movies.")

    updated_count = 0

    for movie in movies:
        old_mood = movie.mood_tags
        old_ending = movie.ending_type

        movie.mood_tags = infer_mood_tags(movie)
        movie.ending_type = infer_ending_type(movie)

        db.add(movie)
        db.commit()

        updated_count += 1

        print(
            f"Tagged: {movie.title} | "
            f"mood: {old_mood} -> {movie.mood_tags} | "
            f"ending: {old_ending} -> {movie.ending_type}"
        )

    db.close()
    print(f"Done. Tagged {updated_count} movies.")


if __name__ == "__main__":
    tag_movies()