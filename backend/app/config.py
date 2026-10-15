"""GeneGraph backend application configuration."""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Literal
import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Neo4j
    neo4j_uri: str = Field(default="neo4j://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password")
    neo4j_database: str = Field(default="neo4j")

    # LLM
    llm_provider: Literal["anthropic", "openai", "gemini", "groq"] = Field(default="groq")
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    gemini_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")

    # PubMed
    pubmed_api_key: str = Field(default="")
    pubmed_email: str = Field(default="")

    # MongoDB
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = Field(default="genegraph")

    # JWT Auth
    jwt_secret: str = Field(default="genegraph-super-secret-key-change-in-production")
    jwt_expiry_hours: int = Field(default=24)

    # App
    backend_port: int = Field(default=8000)
    cors_origins: str = Field(default="http://localhost:5173")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
