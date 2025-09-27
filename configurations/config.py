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
    


config = Config()
