import re


GENRE_KEYWORDS = {
    "action": "Action",
    "adventure": "Adventure",
    "animation": "Animation",
    "animated": "Animation",
    "comedy": "Comedy",
    "funny": "Comedy",
    "romance": "Romance",
    "romantic": "Romance",
    "love": "Romance",
    "drama": "Drama",
    "horror": "Horror",
    "scary": "Horror",
    "thriller": "Thriller",
    "mystery": "Mystery",
    "crime": "Crime",
    "fantasy": "Fantasy",
    "sci-fi": "Science Fiction",
    "science fiction": "Science Fiction",
    "documentary": "Documentary",
    "family": "Family",
    "war": "War",
    "history": "History",
    "musical": "Music",
}


MOOD_KEYWORDS = {
    "funny": "funny",
    "cozy": "lighthearted",
    "comfort": "lighthearted",
    "comforting": "lighthearted",
    "lighthearted": "lighthearted",
    "feel good": "lighthearted",
    "feel-good": "lighthearted",
    "romantic": "romantic",
    "love": "romantic",
    "dark": "dark",
    "intense": "suspenseful",
    "suspenseful": "suspenseful",
    "emotional": "emotional",
    "sad": "emotional",
    "cry": "emotional",
    "scary": "scary",
    "creepy": "scary",
    "inspiring": "inspiring",
    "mind bending": "mind-bending",
    "mind-bending": "mind-bending",
}


ENDING_KEYWORDS = {
    "happy ending": "happy",
    "good ending": "happy",
    "ends well": "happy",
    "sad ending": "sad",
    "bittersweet": "bittersweet",
    "ambiguous": "ambiguous",
    "open ending": "ambiguous",
}


PROVIDER_KEYWORDS = {
    "netflix": "Netflix",
    "hulu": "Hulu",
    "disney": "Disney Plus",
    "disney+": "Disney Plus",
    "prime": "Amazon Prime Video",
    "amazon": "Amazon Prime Video",
    "max": "Max",
    "hbo": "Max",
    "paramount": "Paramount Plus",
    "peacock": "Peacock",
    "apple": "Apple TV Plus",
}


def extract_runtime(prompt: str) -> int | None:
    text = prompt.lower()

    if "under 2 hours" in text or "less than 2 hours" in text:
        return 120

    if "under two hours" in text or "less than two hours" in text:
        return 120

    minute_match = re.search(r"under (\d+) minutes", text)
    if minute_match:
        return int(minute_match.group(1))

    hour_match = re.search(r"under (\d+) hours?", text)
    if hour_match:
        return int(hour_match.group(1)) * 60

    return None


def extract_from_prompt(prompt: str) -> dict:
    text = prompt.lower()

    detected_genres = []
    detected_moods = []
    detected_ending_type = None
    detected_provider = None
    detected_max_runtime = extract_runtime(prompt)

    for keyword, genre in GENRE_KEYWORDS.items():
        if keyword in text and genre not in detected_genres:
            detected_genres.append(genre)

    for keyword, mood in MOOD_KEYWORDS.items():
        if keyword in text and mood not in detected_moods:
            detected_moods.append(mood)

    for keyword, ending_type in ENDING_KEYWORDS.items():
        if keyword in text:
            detected_ending_type = ending_type
            break

    for keyword, provider in PROVIDER_KEYWORDS.items():
        if keyword in text:
            detected_provider = provider
            break

    return {
        "genres": detected_genres,
        "moods": detected_moods,
        "ending_type": detected_ending_type,
        "provider": detected_provider,
        "max_runtime": detected_max_runtime,
    }