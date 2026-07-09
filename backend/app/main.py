from fastapi import FastAPI

from app.database import engine
from app.models import Base
from app.routes import movies, recommend

Base.metadata.create_all(bind=engine)

app = FastAPI(title="StreamSage API")

app.include_router(movies.router, prefix="/api/movies", tags=["movies"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["recommend"])


@app.get("/")
def root():
    return {"message": "StreamSage API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}