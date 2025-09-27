from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configurations.config import config
import logging

logger = logging.getLogger(__name__)

# Create PostgreSQL engine
try:
    engine = create_engine(
        config.POSTGRESQL_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # Set to True for SQL query logging
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
