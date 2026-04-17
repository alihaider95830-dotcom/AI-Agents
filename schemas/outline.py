from __future__ import annotations

import math
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


class SectionItem(BaseModel):
    """Represents a single section in the generated report outline."""

    section_number: int = Field(ge=1)
    title: str
    argument: str
    key_points: list[str] = Field(min_length=3, max_length=5)
    suggested_sources: list[str] = Field(default_factory=list)
    target_word_count: int = Field(ge=100)

    @field_validator("title", "argument")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        """Reject blank section metadata."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("value must not be blank")
        return cleaned_value

    @field_validator("key_points")
    @classmethod
    def validate_key_points(cls, value: list[str]) -> list[str]:
        """Normalize key points while enforcing non-empty entries."""
        cleaned_points = [item.strip() for item in value if item and item.strip()]
        if len(cleaned_points) != len(value):
            raise ValueError("key_points must not contain blank entries")
        return cleaned_points

    @field_validator("suggested_sources")
    @classmethod
    def validate_suggested_sources(cls, value: list[str]) -> list[str]:
        """Normalize suggested sources and validate URL format."""
        cleaned_sources: list[str] = []
        seen_sources: set[str] = set()

        for item in value:
            url = item.strip()
            if not url:
                raise ValueError("suggested_sources must not contain blank entries")

            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("suggested_sources must contain valid http or https URLs")

            if url not in seen_sources:
                cleaned_sources.append(url)
                seen_sources.add(url)

        return cleaned_sources


class ReportOutline(BaseModel):
    """Validated output returned by the Planner agent."""

    topic: str
    report_type: str
    executive_summary: str
    sections: list[SectionItem] = Field(min_length=4, max_length=8)
    total_target_words: int = Field(ge=400)
    estimated_read_time_minutes: int = Field(ge=1)
    timestamp: datetime

    @field_validator("topic", "report_type", "executive_summary")
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        """Reject blank string values for required fields."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("value must not be blank")
        return cleaned_value

    @model_validator(mode="after")
    def validate_outline_integrity(self) -> "ReportOutline":
        """Ensure derived fields and section titles are internally consistent."""
        computed_total_words = sum(
            section.target_word_count for section in self.sections
        )
        if self.total_target_words != computed_total_words:
            raise ValueError(
                "total_target_words must equal the sum of all section target_word_count values"
            )

        expected_read_time = max(1, math.ceil(computed_total_words / 200))
        if self.estimated_read_time_minutes != expected_read_time:
            raise ValueError(
                "estimated_read_time_minutes must equal ceil(total_target_words / 200)"
            )

        normalized_titles = [section.title.strip().casefold() for section in self.sections]
        if len(normalized_titles) != len(set(normalized_titles)):
            raise ValueError("section titles must be unique")

        return self
