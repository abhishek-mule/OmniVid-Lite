from sqlmodel import create_engine, Session
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.models import SQLModel

# SQLite sync URL for simplicity
DATABASE_URL = f"sqlite:///{settings.BASE_DIR / 'omnivid_lite.db'}"

engine = create_engine(DATABASE_URL, echo=False)

session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    session = session_local()
    try:
        yield session
    finally:
        session.close()

def create_tables():
    SQLModel.metadata.create_all(bind=engine)

AsyncSessionLocal = async_session