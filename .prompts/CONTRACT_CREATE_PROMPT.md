# Create Contract: {{title}}

## Context

You are helping build the AI Coding Manager (AICM).

**Parent SPEC**: {{parent_title}}
**Parent Path**: {{parent_file_path}}

**Data Requirements from Parent**:
{{parent_context}}

## Task

Create Pydantic contract models that define the data shapes for:
{{data_description}}

## Requirements

1. Use Pydantic v2 syntax
2. Include proper type hints
3. Add field descriptions and examples
4. Include validation where appropriate
5. Follow existing contract patterns in the codebase
6. Reference the parent SPEC in docstrings

## Output Format

```python
"""
Contracts for {{title}}

Parent SPEC: {{parent_id}}
Created: {{date}}
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class {{ModelName}}Base(BaseModel):
    """Base model with common fields."""
    
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class {{ModelName}}Create(BaseModel):
    """Request model for creating a new {{entity}}."""
    
    title: str = Field(..., min_length=1, max_length=200, description="Title")
    description: Optional[str] = Field(None, description="Optional description")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Example Title",
                "description": "Example description"
            }
        }
    }


class {{ModelName}}Response({{ModelName}}Base):
    """Response model for {{entity}} data."""
    
    title: str
    description: Optional[str] = None
    status: str = Field(default="active")


class {{ModelName}}List(BaseModel):
    """Paginated list response."""
    
    items: List[{{ModelName}}Response]
    total: int
    page: int = 1
    page_size: int = 20
```

## Guidelines

- **Naming**: Use `{Entity}Base`, `{Entity}Create`, `{Entity}Response`, `{Entity}List` pattern
- **Validation**: Use Pydantic Field validators for constraints
- **Documentation**: Every field should have a description
- **Examples**: Include `json_schema_extra` with realistic examples
- **Inheritance**: Use base classes to avoid repetition

## File Location

Save to: `contracts/{{filename}}.py` or `backend/contracts/{{filename}}.py`
