"""SPEC schema contracts for AI Development Workflow.

Per ADR-0006: 3-Tier Document Model.

This module defines the Pydantic schemas for SPECs (T2), the implementation
specifications that capture WHAT should be built.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

__version__ = "2025.12.01"


class FunctionalRequirement(BaseModel):
    """A functional requirement in the spec."""

    id: str = Field(..., description="Unique requirement ID (e.g., SPEC-0001-F01)")
    category: str = Field(..., description="Category of the requirement")
    description: str = Field(..., description="Description of the requirement")
    acceptance_criteria: list[str] = Field(
        default_factory=list, description="Acceptance criteria for this requirement"
    )


class NonFunctionalRequirement(BaseModel):
    """A non-functional requirement in the spec."""

    id: str = Field(..., description="Unique requirement ID (e.g., SPEC-0001-NF01)")
    category: str = Field(..., description="Category (Performance, Security, etc.)")
    description: str = Field(..., description="Description of the requirement")
    acceptance_criteria: list[str] = Field(
        default_factory=list, description="Acceptance criteria"
    )


class APIEndpoint(BaseModel):
    """An API endpoint definition."""

    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE)")
    path: str = Field(..., description="API path (e.g., /api/artifacts)")
    description: str = Field(..., description="Endpoint description")
    request: str | None = Field(None, description="Request model name")
    response: str | None = Field(None, description="Response model name")


class APIModel(BaseModel):
    """A data model definition for API contracts."""

    name: str = Field(..., description="Model name")
    type: str = Field(default="model", description="Type: model or enum")
    fields: list[dict[str, Any]] = Field(
        default_factory=list, description="Model fields"
    )


class APIContracts(BaseModel):
    """API contracts section of the spec."""

    endpoints: list[APIEndpoint] = Field(
        default_factory=list, description="API endpoints"
    )
    models: list[APIModel] = Field(default_factory=list, description="Data models")


class ImplementationMilestone(BaseModel):
    """A milestone in the implementation plan."""

    id: str = Field(..., description="Milestone ID (e.g., M1)")
    name: str = Field(..., description="Milestone name")
    tasks: list[str] = Field(default_factory=list, description="Tasks in this milestone")
    acceptance_criteria: list[str] = Field(
        default_factory=list, description="Acceptance criteria"
    )


class Overview(BaseModel):
    """Overview section of the spec."""

    purpose: str = Field(..., description="Purpose of this specification")
    scope: str = Field(..., description="Scope of this specification")
    out_of_scope: list[str] = Field(
        default_factory=list, description="What is explicitly out of scope"
    )


class Requirements(BaseModel):
    """Requirements section of the spec."""

    functional: list[FunctionalRequirement] = Field(
        default_factory=list, description="Functional requirements"
    )
    non_functional: list[NonFunctionalRequirement] = Field(
        default_factory=list, description="Non-functional requirements"
    )


class SPECSchema(BaseModel):
    """Schema for Implementation Specifications (T2 artifacts).

    SPECs capture WHAT should be built - the functional requirements,
    API contracts, and acceptance criteria.
    """

    schema_type: Literal["spec"] = Field(
        default="spec", description="Schema type identifier"
    )
    id: str = Field(..., description="Unique SPEC identifier (e.g., SPEC-0001)")
    title: str = Field(..., description="Descriptive title for the SPEC")
    status: Literal["draft", "review", "accepted", "deprecated"] = Field(
        default="draft", description="Current status of the SPEC"
    )
    created_date: str = Field(..., description="Date created in YYYY-MM-DD format")
    updated_date: str | None = Field(None, description="Last updated date")
    implements_adr: list[str] = Field(
        default_factory=list, description="ADR IDs this SPEC implements"
    )
    overview: Overview = Field(
        default_factory=Overview, description="Overview section"
    )
    requirements: Requirements = Field(
        default_factory=Requirements, description="Requirements section"
    )
    api_contracts: APIContracts = Field(
        default_factory=APIContracts, description="API contracts section"
    )
    implementation_milestones: list[ImplementationMilestone] = Field(
        default_factory=list, description="Implementation milestones"
    )

    model_config = {"extra": "forbid", "str_strip_whitespace": True}
