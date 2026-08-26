import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    postgres_user: str = "lenny"
    postgres_password: str = "lenny_password"
    postgres_db: str = "lennys_podcast"
    postgres_port: int = 5435
    postgres_host: str = "localhost"
    
    ollama_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen2.5-coder:7b"
    ollama_embed_model: str = "nomic-embed-text"
    
    openai_api_key: Optional[str] = None
    openai_chat_model: str = "gpt-4o"
    
    anthropic_api_key: Optional[str] = None
    anthropic_chat_model: str = "claude-3-5-sonnet-20241022"
    
    default_llm_provider: str = "ollama"  # "ollama", "openai", "anthropic"
    
    # Allows reading from .env file inside lenny-growth-assistant directory or parents
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

settings = Settings()
