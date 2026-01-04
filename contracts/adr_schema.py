"""ADR schema contracts for AI Development Workflow.

Per ADR-0006: 3-Tier Document Model.

This module defines the Pydantic schemas for ADRs (T1), the architectural
decision records that capture WHY decisions were made.
"""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

__version__ = "2025.12.01"


class ProvenanceEntry(BaseModel):
    """Record of a change to the ADR."""

    at: str = Field(..., description="Date in YYYY-MM-DD format")
    by: str = Field(..., description="Who made the change")
    note: str = Field(..., description="Description of the change")


class AlternativeConsidered(BaseModel):
    """An alternative that was evaluated but not chosen."""

    name: str = Field(..., description="Name of the alternative")
    pros: str = Field(..., description="Advantages of this alternative")
    cons: str = Field(..., description="Disadvantages of this alternative")
    rejected_reason: str = Field(..., description="Why this was rejected")


class Guardrail(BaseModel):
    """A guardrail introduced by this ADR."""

    id: str = Field(..., description="Unique identifier for this guardrail")
    rule: str = Field(..., description="The rule to be enforced")
    enforcement: str = Field(..., description="How the rule is enforced")
    scope: str = Field(..., description="Where this guardrail applies")


class DecisionDetails(BaseModel):
    """Detailed breakdown of the decision."""

    approach: str | None = Field(None, description="High-level approach description")
    constraints: list[str] = Field(default_factory=list, description="Technical constraints")
    implementation_specs: list[str] = Field(
        default_factory=list, description="Related spec documents"
    )
    migration_strategy: str | None = Field(None, description="Migration approach if applicable")
    rollback_plan: str | None = Field(None, description="Rollback strategy if needed")


class ADRSchema(BaseModel):
    """Schema for Architecture Decision Records (T1 artifacts).

    ADRs capture WHY architectural decisions were made.
    They are immutable once active and provide rationale for design choices.
    """

    schema_type: Literal["adr"] = Field(default="adr", description="Schema type identifier")
    id: str = Field(..., description="Unique ADR identifier (e.g., ADR-0001_Short-Title)")
    title: str = Field(..., min_length=10, description="Descriptive title for the ADR")
    status: Literal["draft", "active", "deprecated", "superseded"] = Field(
        ..., description="Current status of the ADR"
    )
    date: str = Field(..., description="Date created in YYYY-MM-DD format")
    review_date: str | None = Field(None, description="Next review date in YYYY-MM-DD format")
    author: str = Field(..., description="Who made or approved this decision")
    scope: str = Field(..., description="Scope of impact (e.g., core, knowledge, workflow)")
    provenance: list[ProvenanceEntry] = Field(
        default_factory=list, description="History of changes to this ADR"
    )
    context: str = Field(
        ..., min_length=50, description="Background and problem statement (minimum 50 chars)"
    )
    decision_primary: str = Field(
        ..., min_length=50, description="The primary decision made (minimum 50 chars)"
    )
    decision_details: DecisionDetails = Field(
        default_factory=DecisionDetails, description="Detailed decision breakdown"
    )
    consequences: list[str] = Field(default_factory=list, description="Known consequences")
    alternatives_considered: list[AlternativeConsidered] = Field(
        default_factory=list, description="Other options that were evaluated"
    )
    tradeoffs: str | None = Field(None, description="Key tradeoffs made in this decision")
    guardrails: list[Guardrail] = Field(
        default_factory=list, description="Specific guardrails introduced by this ADR"
    )
    cross_cutting_guardrails: list[str] = Field(
        default_factory=list, description="References to guardrails from other ADRs"
    )
    references: list[str] = Field(
        default_factory=list, description="Related files, documents, or resources"
    )
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    affected_components: list[str] = Field(
        default_factory=list, description="Components impacted by this decision"
    )

    @field_validator("date", "review_date")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate date is in YYYY-MM-DD format."""
        if v is None:
            return v
        try:
            parts = v.split("-")
            if len(parts) != 3:
                raise ValueError("Date must be in YYYY-MM-DD format")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            date(year, month, day)
            return v
        except (ValueError, IndexError):
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD")

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Validate ADR ID format."""
        if not v.startswith("ADR-"):
            raise ValueError("ADR ID must start with 'ADR-'")
        return v

    model_config = {"extra": "forbid", "str_strip_whitespace": True}


class ADRCreateRequest(BaseModel):
    """Request to create a new ADR."""

    adr_data: dict = Field(..., description="Full ADR data conforming to ADRSchema")
    folder: str = Field(default="core", description="Folder to store the ADR in")


class ADRFieldValidationRequest(BaseModel):
    """Request to validate a single ADR field in real-time."""

    field_name: str = Field(..., description="Name of the field to validate")
    field_value: Any = Field(..., description="Value of the field")
    context: dict = Field(default_factory=dict, description="Additional context for validation")


class ADRFieldValidationResponse(BaseModel):
    """Response from ADR field validation."""

    valid: bool = Field(..., description="Whether the field value is valid")
    error: str | None = Field(None, description="Error message if invalid")
