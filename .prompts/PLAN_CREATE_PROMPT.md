# Create PLAN-{{number}}: {{title}}

## Context

You are helping build the AI Coding Manager (AICM).

**Parent SPEC**: {{parent_title}}
**Parent Path**: {{parent_file_path}}

**Requirements from Parent**:
{{parent_context}}

## Task

Create an execution Plan that breaks the work into milestones and tasks for:
{{feature_description}}

## Requirements

1. Follow the standard PLAN format (JSON preferred)
2. Status should be "planned" initially
3. Break into logical Milestones (M01, M02, etc.)
4. Each milestone has discrete Tasks
5. Include verification commands where applicable
6. Reference the parent SPEC appropriately

## Output Format

```json
{
  "id": "PLAN-{{number}}",
  "title": "{{title}}",
  "status": "planned",
  "parent_spec": "{{parent_id}}",
  "created": "{{date}}",
  "milestones": [
    {
      "id": "M01",
      "title": "Milestone 1 Title",
      "status": "pending",
      "tasks": [
        {
          "id": "T01",
          "title": "Task description",
          "status": "pending",
          "verification": "command to verify completion"
        },
        {
          "id": "T02",
          "title": "Another task",
          "status": "pending",
          "verification": null
        }
      ]
    },
    {
      "id": "M02",
      "title": "Milestone 2 Title",
      "status": "pending",
      "tasks": [
        {
          "id": "T01",
          "title": "Task description",
          "status": "pending",
          "verification": "npm run test"
        }
      ]
    }
  ],
  "dependencies": [
    {
      "type": "spec",
      "id": "{{parent_id}}",
      "status": "active"
    }
  ]
}
```

## Guidelines

- **Milestones**: High-level deliverables (typically 2-5 per plan)
- **Tasks**: Concrete work items (typically 2-8 per milestone)
- **Verification**: Shell commands, test commands, or manual check descriptions
- **Dependencies**: What must exist before this plan can execute

## File Location

Save to: `.plans/PLAN-{{number}}_{{filename}}.json`
