from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "GTA Shorts AI Factory"
    database_url: str = "sqlite:///./gta_shorts.db"
    youtube_api_key: str | None = None
    allowed_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
