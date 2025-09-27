from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configurations.config import config
import logging

logger = logging.getLogger(__name__)

# Create PostgreSQL engine
try:
    # Ensure we use psycopg2-binary driver
    postgres_url = config.POSTGRESQL_URL
    if not postgres_url.startswith("postgresql+psycopg2://"):
        postgres_url = postgres_url.replace("postgresql://", "postgresql+psycopg2://")
    
    engine = create_engine(
        postgres_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False,  # Set to True for SQL query logging
        connect_args={"options": "-c timezone=utc"}
    )
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info("PostgreSQL database connection established successfully")
    
except Exception as e:
    logger.error(f"Failed to establish PostgreSQL database connection: {e}")
    raise

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
