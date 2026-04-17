from __future__ import annotations


class ResearcherError(Exception):
    """Raised when the researcher pipeline fails."""


class PlannerError(Exception):
    """Raised when the planner pipeline fails."""


class WriterError(Exception):
    """Raised when the writer pipeline fails."""


class QAError(Exception):
    """Raised when the QA pipeline fails."""


class PipelineError(Exception):
    """Raised when the end-to-end agent pipeline fails."""
