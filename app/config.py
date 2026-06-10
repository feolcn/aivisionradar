from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AIVisionRadar"
    DATABASE_URL: str = "sqlite:///./data/aivisionradar.db"
    ENABLE_SCHEDULER: bool = False

    GITHUB_TOKEN: str = ""
    AI_BASE_URL: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"

    ENABLE_TRANSLATION: bool = False

    CRAWL_INTERVAL_HOURS: int = 6
    DAILY_REPORT_HOUR: int = 8

    HTTP_TIMEOUT: int = 30
    MAX_ITEMS_PER_SOURCE: int = 50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
