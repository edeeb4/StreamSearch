#SQLAlchemy models used by the recommendation service

from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True)
    title = Column(String, index=True)
    overview = Column(Text)
    genres = Column(String)
    runtime = Column(Integer)
    release_year = Column(Integer)
    poster_url = Column(String)
    streaming_providers = Column(String)
    mood_tags = Column(String)
    ending_type = Column(String)
    embedding = Column(Text)