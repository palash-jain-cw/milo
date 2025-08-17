"""Configuration management using pydantic settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Project paths
    project_root_dir: Path = Path(__file__).parent.parent.parent.parent

    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_SCHEMA: str

    # OpenAI settings
    OPENAI_API_KEY: str
    OPENAI_MODEL_SMALL: str
    OPENAI_MODEL_MEDIUM: str
    OPENAI_MODEL_LARGE: str

    # Computed properties
    @property
    def log_dir(self) -> Path:
        """Directory for log files."""
        return self.project_root_dir / "logs"

    @property
    def data_dir(self) -> Path:
        """Directory for data files."""
        return self.project_root_dir / "data"

    @property
    def rough_dir(self) -> Path:
        """Directory for rough work and notebooks."""
        return self.project_root_dir / "rough"

    @property
    def database_url(self) -> str:
        """Database URL for the application."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Create global settings instance
settings = Settings()
