# Create SPEC-{{number}}: {{title}}

## Context

You are helping build the AI Coding Manager (AICM).

**Parent ADR**: {{parent_title}}
**Parent Path**: {{parent_file_path}}

**Architecture Decisions from Parent**:
{{parent_context}}

## Task

Create a Specification (SPEC) document that defines the behavioral requirements and acceptance criteria for:
{{feature_description}}

## Requirements

1. Follow the standard SPEC format
2. Status should be "draft" initially
3. Include clear Functional Requirements with IDs (FR-1, FR-2, etc.)
4. Include Non-Functional Requirements if applicable
5. Define Acceptance Criteria for each requirement
6. Reference the parent ADR appropriately

## Output Format

```markdown
# SPEC-{{number}}: {{title}}

> **Status**: `draft`
> **Date**: {{date}}
> **Parent ADR**: {{parent_id}}

## Overview

[Brief description of what this specification covers]

## Functional Requirements

### FR-1: [Requirement Name]

**Description**: [What the system must do]

**Acceptance Criteria**:
- [ ] AC-1.1: [Testable criterion]
- [ ] AC-1.2: [Testable criterion]

### FR-2: [Requirement Name]

**Description**: [What the system must do]

**Acceptance Criteria**:
- [ ] AC-2.1: [Testable criterion]

## Non-Functional Requirements

### NFR-1: [Performance/Security/etc.]

**Description**: [Constraint or quality attribute]

**Acceptance Criteria**:
- [ ] [Measurable criterion]

## API Contract (if applicable)

[Endpoint definitions, request/response schemas]

## Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| ... | ... | ... |

## Open Questions

| ID | Question | Status |
|----|----------|--------|
| Q-1 | ... | open |
```

## File Location

Save to: `.specs/SPEC-{{number}}_{{filename}}.md`
