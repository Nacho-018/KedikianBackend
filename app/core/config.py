from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int  # Para JWT tokens de usuarios

    # JWT para API Externa
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    EXTERNAL_SHARED_SECRET: str

    class Config:
        env_file = ".env"

settings = Settings()