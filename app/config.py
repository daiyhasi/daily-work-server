from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="http://cloud.omnimind.com.cn/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-5.5", alias="OPENAI_MODEL")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    cors_origins_value: str = Field(default="*", alias="CORS_ORIGINS")

    ai_timeout_seconds: float = Field(default=90, alias="AI_TIMEOUT_SECONDS")
    ai_http_retries: int = Field(default=1, alias="AI_HTTP_RETRIES")
    ai_max_tokens: int = Field(default=12000, alias="AI_MAX_TOKENS")
    rate_limit_per_minute: int = Field(default=10, alias="RATE_LIMIT_PER_MINUTE")

    @property
    def cors_origins(self) -> List[str]:
        return [item.strip() for item in self.cors_origins_value.split(",") if item.strip()]

    @property
    def chat_completions_url(self) -> str:
        return self.openai_base_url.rstrip("/") + "/chat/completions"


@lru_cache
def get_settings() -> Settings:
    return Settings()
