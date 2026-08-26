# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import declarative_base, sessionmaker
import os

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tariff.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB Atlas Integration
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb+srv://thenna44ck_db_user:2dWQ2jrV762IvKs6@cluster0.phdzsgq.mongodb.net/a3_express?retryWrites=true&w=majority&appName=Cluster0"
)

_mongo_client = None

def get_mongo_db():
    global _mongo_client
    if MongoClient is None:
        return None
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGODB_URL)
    return _mongo_client["a3_express"]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
