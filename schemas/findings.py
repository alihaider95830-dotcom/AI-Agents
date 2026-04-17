from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

SOURCE_SNIPPET_MAX_LENGTH = 300


class SourceItem(BaseModel):
    """Represents a single researched source."""

    url: str
    title: str
    snippet: str
    scrape_success: bool

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        """Ensure URLs use the http or https scheme."""
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be a valid http or https URL")
        return value

    @field_validator("snippet")
    @classmethod
    def validate_snippet(cls, value: str) -> str:
        """Keep source snippets short and deterministic."""
        return value[:SOURCE_SNIPPET_MAX_LENGTH]


class FindingsOutput(BaseModel):
    """Validated output returned by the Researcher agent."""

    query: str
    sources: list[SourceItem]
    key_facts: list[str]
    faiss_index_path: str
    total_chunks_stored: int = Field(ge=0)
    timestamp: datetime

    @field_validator("query", "faiss_index_path")
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        """Reject blank string values for required string fields."""
        if not value or not value.strip():
            raise ValueError("value must not be blank")
        return value

    @field_validator("key_facts")
    @classmethod
    def validate_key_facts(cls, value: list[str]) -> list[str]:
        """Remove blank facts while preserving order."""
        cleaned_facts: list[str] = []
        for item in value:
            if item and item.strip():
                cleaned_facts.append(item.strip())
        return cleaned_facts

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Preserve standard behaviour while keeping an explicit return type."""
        return super().model_dump(*args, **kwargs)
