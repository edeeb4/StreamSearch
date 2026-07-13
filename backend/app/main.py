from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base
from app.routes import movies, recommend

Base.metadata.create_all(bind=engine)

app = FastAPI(title="StreamSage API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://*.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router, prefix="/api/movies", tags=["movies"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["recommend"])


@app.get("/")
def root():
    return {"message": "StreamSage API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}