from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings
from config import get_settings

settings = get_settings()
print("DATABASE_URL being used:", settings.database_url)

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
