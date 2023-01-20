from sqlalchemy import create_engine, Column, Integer, String, Identity,MetaData, Sequence, ForeignKey, Date, Float
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
import os
from typing import Dict

# Create a sqlite engine instance
engine = create_engine("sqlite:///url_crawl.db")
# Create a DeclarativeMeta instance
Base = declarative_base()

# Define To Do class inheriting from Base
class WebPageDB(Base):
    __tablename__ = 'webpages'
    url = Column(String(256),nullable=False,primary_key=True)
    creation_date = Column(Date,nullable=True)

def init_db():
    Base.metadata.create_all(engine)