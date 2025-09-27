from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
load_dotenv()


class Config(BaseSettings):
    """It will automatically read environment variables into fields.
    """

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY","")
    POSTGRESQL_URL: str = os.getenv("POSTGRESQL_URL","")
    MONGODB_URI: str = os.getenv("MONGODB_URI","")
    HOST: str = os.getenv("HOST","")
    PORT: str = os.getenv("PORT","")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY","")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM","")
    SOURCE_FILENAME_MEDICAL: str = os.getenv("SOURCE_FILENAME_MEDICAL","medical_data.txt")
    SOURCE_FILENAME_POLICE: str = os.getenv("SOURCE_FILENAME_POLICE","police_data.txt")
    SOURCE_FILENAME_ELECTRICITY: str = os.getenv("SOURCE_FILENAME_ELECTRICITY","electricity_data.txt")
    SOURCE_FILENAME_FIRE: str = os.getenv("SOURCE_FILENAME_FIRE","fire_data.txt")
    
    # SMTP Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST","smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT","587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME","")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD","")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS","true").lower() == "true"
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL","false").lower() == "true"
    EMAIL_FROM: str = os.getenv("EMAIL_FROM","")
    


config = Config()
