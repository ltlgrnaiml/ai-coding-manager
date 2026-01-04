# Create {{artifact_type}}-{{number}}: {{title}}

## Context
You are helping build the AI Coding Manager (AICM).

**Parent Document**: {{parent_title}}
**Parent Path**: {{parent_file_path}}

**Relevant Context**:
{{parent_context}}

## Task
Create a new Discussion (DISC) document that addresses the following questions/topics:
{{key_questions}}

## Requirements
1. Follow the standard DISC format with proper frontmatter
2. Status should be "active"
3. Include clear Problem Statement and Context sections
4. Document any open questions in a structured table
5. Reference the parent document appropriately

## Output Format
Create a markdown file following the template at: `.discussions/.templates/DISC_TEMPLATE.md`

Key sections to include:
- Problem Statement (concise, clear)
- Context (background, trigger)
- Discussion content
- Open Questions table
- Next Steps

## File Location
Save to: `.discussions/DISC-{{number}}_{{filename}}.md`

## Example Structure
```markdown
# DISC-{{number}}: {{title}}

> **Status**: `active`
> **Created**: {{date}}
> **Parent**: {{parent_id}}

## Problem Statement
[Clear statement of the problem]

## Context
[Background and trigger for this discussion]

## Discussion
[Main content]

## Open Questions
| ID | Question | Status |
|----|----------|--------|
| Q-1 | ... | open |

## Next Steps
[Action items]
```
