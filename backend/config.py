from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514", env="ANTHROPIC_MODEL")

    app_env: str = Field(default="development", env="APP_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    max_tokens: int = Field(default=4096, env="MAX_TOKENS")
    temperature: float = Field(default=0.2, env="TEMPERATURE")

    db_path: str = Field(default="./risk_assessor.db", env="DB_PATH")
    log_dir: str = Field(default="./logs", env="LOG_DIR")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
