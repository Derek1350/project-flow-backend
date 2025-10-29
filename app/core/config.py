from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Loads and validates application settings from the environment.
    """
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

# Create a single, reusable instance of the settings
settings = Settings()