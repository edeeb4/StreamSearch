from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes import movies, recommend


Base.metadata.create_all(bind=engine)

app = FastAPI(title="StreamSearch API")


# Permit the local React/Vite development server to communicate with FastAPI.
# localhost and 127.0.0.1 count as different origins, so both are included.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    movies.router,
    prefix="/api/movies",
    tags=["movies"],
)

app.include_router(
    recommend.router,
    prefix="/api/recommend",
    tags=["recommendations"],
)


@app.get("/")
def root():
    """Return a basic status message showing that the API is running."""

    return {"message": "StreamSearch API is running"}