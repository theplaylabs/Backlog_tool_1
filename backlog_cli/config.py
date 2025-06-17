"""Configuration dataclass (placeholder)."""
from dataclasses import dataclass


@dataclass
class Config:  # noqa: D401
    """Placeholder config class."""

    model: str = "gpt-3.5-turbo"
    verbose: bool = False
