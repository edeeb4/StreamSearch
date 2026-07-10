import { useState } from "react";
import "./App.css";

type MovieRecommendation = {
  id: number;
  tmdb_id: number;
  title: string;
  overview: string | null;
  genres: string | null;
  runtime: number | null;
  release_year: number | null;
  poster_url: string | null;
  streaming_providers: string | null;
  mood_tags: string | null;
  ending_type: string | null;
  score: number;
  explanation: string;
};

function App() {
  const [prompt, setPrompt] = useState("");
  const [genre, setGenre] = useState("");
  const [provider, setProvider] = useState("");
  const [maxRuntime, setMaxRuntime] = useState("");
  const [mood, setMood] = useState("");
  const [endingType, setEndingType] = useState("");
  const [movies, setMovies] = useState<MovieRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function getRecommendations() {
    setLoading(true);
    setError("");
    setMovies([]);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/recommend/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
          genre: genre || null,
          provider: provider || null,
          max_runtime: maxRuntime ? Number(maxRuntime) : null,
          mood: mood || null,
          ending_type: endingType || null,
        }),
      });

      if (!response.ok) {
        throw new Error("Something went wrong while getting recommendations.");
      }

      const data = await response.json();
      setMovies(data);
    } catch (err) {
      setError("Could not connect to the backend. Make sure FastAPI is running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app">
      <section className="hero">
        <p className="eyebrow">AI Movie Recommendation Chatbot</p>
        <h1>StreamSage</h1>
        <p className="subtitle">
          Describe what you want to watch and get movie recommendations
          with posters, mood tags, ending types, and explainable scores.
        </p>
      </section>

      <section className="search-panel">
        <label>
          What do you want to watch?
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Example: I want a funny romantic movie with a happy ending"
          />
        </label>

        <div className="filters">
          <label>
            Genre
            <input
              value={genre}
              onChange={(event) => setGenre(event.target.value)}
              placeholder="Comedy"
            />
          </label>

          <label>
            Streaming Provider
            <input
              value={provider}
              onChange={(event) => setProvider(event.target.value)}
              placeholder="Netflix"
            />
          </label>

          <label>
            Max Runtime
            <input
              value={maxRuntime}
              onChange={(event) => setMaxRuntime(event.target.value)}
              placeholder="120"
              type="number"
            />
          </label>

          <label>
            Mood
            <input
              value={mood}
              onChange={(event) => setMood(event.target.value)}
              placeholder="lighthearted"
            />
          </label>

          <label>
            Ending Type
            <input
              value={endingType}
              onChange={(event) => setEndingType(event.target.value)}
              placeholder="happy"
            />
          </label>
        </div>

        <button onClick={getRecommendations} disabled={loading || !prompt}>
          {loading ? "Finding movies..." : "Recommend Movies"}
        </button>

        {error && <p className="error">{error}</p>}
      </section>

      <section className="results">
        {movies.map((movie) => (
          <article className="movie-card" key={movie.id}>
            {movie.poster_url ? (
              <img src={movie.poster_url} alt={`${movie.title} poster`} />
            ) : (
              <div className="poster-placeholder">No Poster</div>
            )}

            <div className="movie-info">
              <div className="movie-header">
                <h2>{movie.title}</h2>
                <span>{Math.round(movie.score * 100)}%</span>
              </div>

              <p className="meta">
                {movie.release_year || "Unknown year"} ·{" "}
                {movie.runtime ? `${movie.runtime} min` : "Unknown runtime"}
              </p>

              <p className="overview">{movie.overview}</p>

              <div className="tags">
                {movie.genres && <span>{movie.genres}</span>}
                {movie.mood_tags && <span>{movie.mood_tags}</span>}
                {movie.ending_type && <span>{movie.ending_type} ending</span>}
              </div>

              {movie.streaming_providers && (
                <p className="providers">
                  <strong>Streaming:</strong> {movie.streaming_providers}
                </p>
              )}

              <p className="explanation">{movie.explanation}</p>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

export default App;