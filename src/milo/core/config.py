"""Configuration management using pydantic settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Project paths
    project_root_dir: Path = Path(__file__).parent.parent.parent.parent
    OPENAI_API_KEY: str
    OPENAI_MODEL: str

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

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Create global settings instance
settings = Settings()
