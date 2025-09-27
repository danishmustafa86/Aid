from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.health_check_routes import health_check_router
from routes.medical_emergency_routes import medical_emergency_router
from routes.electricity_emergency_routes import electricity_emergency_router
from routes.police_emergency_routes import police_emergency_router
from routes.triage_routes import triage_router
from routes.authority_routes import authority_router
from routes.notification_routes import notification_router
from routes.followup_routes import followup_router
from models.database_models import Base
from configurations.postgres_db import engine
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Application shutting down")

app.include_router(health_check_router)
app.include_router(medical_emergency_router)
app.include_router(electricity_emergency_router)
app.include_router(police_emergency_router)
app.include_router(triage_router)
app.include_router(authority_router)
app.include_router(notification_router)
app.include_router(followup_router)