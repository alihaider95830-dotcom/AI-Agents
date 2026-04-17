from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator


def count_words(text: str) -> int:
    """Return a simple whitespace-based word count for markdown content."""
    return len(text.split())


class CitationItem(BaseModel):
    """Represents a single citation used in the drafted report."""

    index: int = Field(ge=1)
    url: str
    title: str
    inline_reference: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        """Ensure citation URLs use the http or https scheme."""
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be a valid http or https URL")
        return value

    @field_validator("title", "inline_reference")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        """Reject blank citation text fields."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("value must not be blank")
        return cleaned_value

    @model_validator(mode="after")
    def validate_inline_reference(self) -> "CitationItem":
        """Ensure the inline reference includes the citation index, title, and URL."""
        reference = self.inline_reference
        if f"[{self.index}]" not in reference:
            raise ValueError("inline_reference must include the citation index")
        if self.title not in reference:
            raise ValueError("inline_reference must include the citation title")
        if self.url not in reference:
            raise ValueError("inline_reference must include the citation URL")
        return self


class SectionDraft(BaseModel):
    """Represents a single drafted section in the report."""

    section_number: int = Field(ge=1)
    title: str
    content: str
    word_count: int = Field(ge=1)
    citations: list[CitationItem] = Field(default_factory=list)
    within_word_target: bool

    @field_validator("title", "content")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        """Reject blank section text fields."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("value must not be blank")
        return cleaned_value

    @model_validator(mode="after")
    def validate_section_integrity(self, info: ValidationInfo) -> "SectionDraft":
        """Ensure section content, citations, and word target flags are consistent."""
        actual_word_count = count_words(self.content)
        if self.word_count != actual_word_count:
            raise ValueError("word_count must equal the actual word count of content")

        for citation in self.citations:
            if f"[{citation.index}]" not in self.content:
                raise ValueError("content must include an inline citation marker for each citation")

        target_word_count = _resolve_target_word_count(self, info.context)
        tolerance = _resolve_tolerance(info.context)
        if target_word_count is not None:
            minimum_words = target_word_count * (1 - tolerance)
            maximum_words = target_word_count * (1 + tolerance)
            expected_flag = minimum_words <= self.word_count <= maximum_words
            if self.within_word_target != expected_flag:
                raise ValueError(
                    "within_word_target must reflect whether word_count is within tolerance"
                )

        return self


class ReportDraft(BaseModel):
    """Validated output returned by the Writer agent."""

    topic: str
    report_type: str
    executive_summary: str
    sections: list[SectionDraft] = Field(min_length=1)
    total_word_count: int = Field(ge=1)
    all_citations: list[CitationItem] = Field(default_factory=list)
    markdown_output: str
    timestamp: datetime

    @field_validator("topic", "report_type", "executive_summary", "markdown_output")
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        """Reject blank string values for required fields."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("value must not be blank")
        return cleaned_value

    @model_validator(mode="after")
    def validate_report_integrity(self) -> "ReportDraft":
        """Ensure the draft is internally consistent and fully assembled."""
        computed_total_words = sum(section.word_count for section in self.sections)
        if self.total_word_count != computed_total_words:
            raise ValueError("total_word_count must equal the sum of all section word_count values")

        citation_urls = [citation.url for citation in self.all_citations]
        if len(citation_urls) != len(set(citation_urls)):
            raise ValueError("all_citations must not contain duplicate URLs")

        expected_indexes = list(range(1, len(self.all_citations) + 1))
        actual_indexes = [citation.index for citation in self.all_citations]
        if actual_indexes != expected_indexes:
            raise ValueError("all_citations indexes must be sequential starting from 1")

        for section in self.sections:
            heading = f"## {section.title}"
            if heading not in self.markdown_output:
                raise ValueError("markdown_output must contain all section titles as ## headings")

        citation_lookup = {citation.url: citation for citation in self.all_citations}
        for section in self.sections:
            for citation in section.citations:
                master_citation = citation_lookup.get(citation.url)
                if master_citation is None:
                    raise ValueError("section citations must also exist in all_citations")
                if citation.index != master_citation.index:
                    raise ValueError(
                        "section citation indexes must match the master all_citations index"
                    )

        return self

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Preserve standard behaviour while keeping an explicit return type."""
        return super().model_dump(*args, **kwargs)


def _resolve_target_word_count(
    section: SectionDraft,
    context: Any,
) -> int | None:
    """Resolve the target word count for a section from Pydantic validation context."""
    if not isinstance(context, dict):
        return None

    target_word_count = context.get("target_word_count")
    if isinstance(target_word_count, int):
        return target_word_count

    section_targets = context.get("section_targets")
    if isinstance(section_targets, dict):
        resolved_target = section_targets.get(section.section_number)
        if isinstance(resolved_target, int):
            return resolved_target

    return None


def _resolve_tolerance(context: Any) -> float:
    """Resolve the configured word count tolerance from validation context."""
    if not isinstance(context, dict):
        return 0.20

    tolerance = context.get("word_count_tolerance", 0.20)
    if isinstance(tolerance, (int, float)):
        return float(tolerance)

    return 0.20
