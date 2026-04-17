from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from schemas.draft import CitationItem

ALLOWED_QA_ISSUE_TYPES = {
    "factual",
    "citation_missing",
    "grammar",
    "clarity",
}


class QAFlag(BaseModel):
    """Represents a single issue identified during QA review."""

    section_number: int = Field(ge=1)
    issue_type: str
    description: str
    resolved: bool
    original_text: str
    corrected_text: str | None = None

    @field_validator("issue_type", "description", "original_text")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        """Reject blank QA flag text fields."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("value must not be blank")
        return cleaned_value

    @field_validator("issue_type")
    @classmethod
    def validate_issue_type(cls, value: str) -> str:
        """Restrict issue types to the supported QA taxonomy."""
        if value not in ALLOWED_QA_ISSUE_TYPES:
            raise ValueError(
                f"issue_type must be one of {sorted(ALLOWED_QA_ISSUE_TYPES)}"
            )
        return value

    @field_validator("corrected_text")
    @classmethod
    def normalize_corrected_text(cls, value: str | None) -> str | None:
        """Normalize optional corrected text values."""
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class FinalReport(BaseModel):
    """Validated output returned by the QA agent."""

    topic: str
    report_type: str
    executive_summary: str
    markdown_output: str
    total_word_count: int = Field(ge=1)
    all_citations: list[CitationItem] = Field(default_factory=list)
    qa_flags: list[QAFlag] = Field(default_factory=list)
    qa_passed: bool
    quality_score: float
    job_id: str | None = None
    timestamp: datetime

    @field_validator("topic", "report_type", "executive_summary", "markdown_output")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        """Reject blank string values for required text fields."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("value must not be blank")
        return cleaned_value

    @field_validator("quality_score")
    @classmethod
    def validate_quality_score(cls, value: float) -> float:
        """Ensure the QA quality score is normalized between 0 and 1."""
        if not 0.0 <= value <= 1.0:
            raise ValueError("quality_score must be between 0.0 and 1.0")
        return value

    @field_validator("job_id")
    @classmethod
    def normalize_job_id(cls, value: str | None) -> str | None:
        """Normalize optional job identifiers."""
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None

    @model_validator(mode="after")
    def validate_report_integrity(self) -> "FinalReport":
        """Ensure QA pass/fail state matches the unresolved flag set."""
        has_unresolved_flags = any(not flag.resolved for flag in self.qa_flags)
        if has_unresolved_flags:
            self.qa_passed = False
        return self
