/**
 * DISC Parser - Extracts artifact references from Discussion documents
 * 
 * Parses DISC markdown content to find:
 * - Explicitly listed ADRs, SPECs, Contracts, Plans
 * - Cross-references in text (e.g., "see ADR-0025")
 * - Metadata fields linking to other artifacts
 */

export interface ArtifactReference {
  type: 'adr' | 'spec' | 'contract' | 'plan' | 'disc' | 'sprompt' | 'fragment'
  id: string
  title?: string
  status: 'exists' | 'planned' | 'referenced'
  context?: string // The line/section where it was found
}

export interface ParsedDisc {
  id: string
  title: string
  status: string
  summary?: string
  problemStatement?: string
  references: ArtifactReference[]
  childDiscs: string[]
  parentDisc?: string
  requirements: {
    functional: string[]
    nonFunctional: string[]
  }
  openQuestions: Array<{ id: string; question: string; status: string }>
  delegationScope?: string
}

// Regex patterns for artifact IDs
const ARTIFACT_PATTERNS: Record<string, RegExp> = {
  adr: /ADR-(\d{4})/gi,
  spec: /SPEC-(\d{4})/gi,
  contract: /CONTRACT-(\d{4})/gi,
  plan: /PLAN-(\d{4})/gi,
  disc: /DISC-(\d{4})/gi,
  sprompt: /SPROMPT-(\d{4})/gi,
  fragment: /FRAGMENT-(\d{4})/gi,
}

// Section patterns
const SECTION_PATTERNS = {
  title: /^#\s+(?:DISC-\d{4}:\s*)?(.+?)(?:\s*[-—]|$)/m,
  status: /\*\*Status\*\*:\s*`?(\w+)`?/i,
  summary: /##\s*Summary\n+([\s\S]*?)(?=\n##|\n---|\Z)/i,
  problemStatement: /##\s*Problem Statement\n+([\s\S]*?)(?=\n##|\n---|\Z)/i,
  delegationScope: /Delegation Scope:\s*(.+?)(?:\n|$)/i,
  parentDisc: /Parent Discussion:\s*(DISC-\d{4})/i,
  relatedArtifacts: /##\s*(?:Related Artifacts|Artifact Chain|Dependencies)\n+([\s\S]*?)(?=\n##|\n---|\Z)/i,
  functionalRequirements: /###\s*Functional Requirements\n+([\s\S]*?)(?=\n###|\n##|\n---|\Z)/i,
  openQuestions: /##\s*Open Questions\n+([\s\S]*?)(?=\n##|\n---|\Z)/i,
}

/**
 * Parse a DISC document and extract all artifact references
 */
export function parseDisc(content: string, discId: string): ParsedDisc {
  const references: ArtifactReference[] = []
  const childDiscs: string[] = []
  const seenIds = new Set<string>()

  // Extract title
  const titleMatch = content.match(SECTION_PATTERNS.title)
  const title = titleMatch ? titleMatch[1].trim() : discId

  // Extract status
  const statusMatch = content.match(SECTION_PATTERNS.status)
  const status = statusMatch ? statusMatch[1].toLowerCase() : 'draft'

  // Extract summary
  const summaryMatch = content.match(SECTION_PATTERNS.summary)
  const summary = summaryMatch ? summaryMatch[1].trim() : undefined

  // Extract problem statement
  const problemMatch = content.match(SECTION_PATTERNS.problemStatement)
  const problemStatement = problemMatch ? problemMatch[1].trim() : undefined

  // Extract delegation scope
  const delegationMatch = content.match(SECTION_PATTERNS.delegationScope)
  const delegationScope = delegationMatch ? delegationMatch[1].trim() : undefined

  // Extract parent DISC
  const parentMatch = content.match(SECTION_PATTERNS.parentDisc)
  const parentDisc = parentMatch ? parentMatch[1] : undefined

  // Extract functional requirements
  const frMatch = content.match(SECTION_PATTERNS.functionalRequirements)
  const functionalReqs: string[] = []
  if (frMatch) {
    const reqMatches = frMatch[1].matchAll(/[-*]\s*(?:\[.\])?\s*\*\*([^*]+)\*\*:\s*(.+)/g)
    for (const match of reqMatches) {
      functionalReqs.push(`${match[1]}: ${match[2]}`)
    }
  }

  // Extract open questions
  const oqMatch = content.match(SECTION_PATTERNS.openQuestions)
  const openQuestions: Array<{ id: string; question: string; status: string }> = []
  if (oqMatch) {
    // Parse table format: | ID | Question | Status |
    const tableRows = oqMatch[1].matchAll(/\|\s*(Q-\d+)\s*\|\s*(.+?)\s*\|\s*(\w+)\s*\|/g)
    for (const row of tableRows) {
      openQuestions.push({
        id: row[1],
        question: row[2].trim(),
        status: row[3].toLowerCase(),
      })
    }
  }

  // Find all artifact references in the document
  for (const [type, pattern] of Object.entries(ARTIFACT_PATTERNS)) {
    const matches = content.matchAll(pattern)
    for (const match of matches) {
      const id = `${type.toUpperCase()}-${match[1]}`
      
      // Skip self-references
      if (id === discId) continue
      
      // Skip duplicates
      if (seenIds.has(id)) continue
      seenIds.add(id)

      // Determine context (find the line containing this reference)
      const lineIndex = content.substring(0, match.index).split('\n').length
      const lines = content.split('\n')
      const contextLine = lines[lineIndex - 1] || ''

      // Determine if this is planned vs just referenced
      const isPlanned = /(?:will create|to be created|planned|TODO|needs?|should create)/i.test(contextLine)
      const isListed = /^[-*]\s/.test(contextLine) || /^\|/.test(contextLine)

      const reference: ArtifactReference = {
        type: type as ArtifactReference['type'],
        id,
        status: isPlanned ? 'planned' : (isListed ? 'exists' : 'referenced'),
        context: contextLine.trim().substring(0, 100),
      }

      references.push(reference)

      // Track child DISCs
      if (type === 'disc' && id !== discId) {
        childDiscs.push(id)
      }
    }
  }

  // Look for explicitly listed artifacts in "Related Artifacts" or similar sections
  const relatedSection = content.match(SECTION_PATTERNS.relatedArtifacts)
  if (relatedSection) {
    // Parse list items like "- ADR-0025: Architecture Decision"
    const listItems = relatedSection[1].matchAll(/[-*]\s*\*?\*?([A-Z]+-\d{4})\*?\*?(?::\s*(.+))?/g)
    for (const item of listItems) {
      const id = item[1]
      const existingRef = references.find(r => r.id === id)
      if (existingRef) {
        existingRef.status = 'exists'
        if (item[2]) existingRef.title = item[2].trim()
      }
    }
  }

  return {
    id: discId,
    title,
    status,
    summary,
    problemStatement,
    references,
    childDiscs,
    parentDisc,
    delegationScope,
    requirements: {
      functional: functionalReqs,
      nonFunctional: [],
    },
    openQuestions,
  }
}

/**
 * Build an artifact tree from a parsed DISC
 */
export interface ArtifactTreeNode {
  id: string
  type: ArtifactReference['type'] | 'root'
  title?: string
  status: 'exists' | 'planned' | 'missing'
  children: ArtifactTreeNode[]
  level: number
}

export function buildArtifactTree(parsedDisc: ParsedDisc): ArtifactTreeNode {
  const root: ArtifactTreeNode = {
    id: parsedDisc.id,
    type: 'disc',
    title: parsedDisc.title,
    status: 'exists',
    children: [],
    level: 0,
  }

  // Group references by type
  const byType: Record<string, ArtifactReference[]> = {}
  for (const ref of parsedDisc.references) {
    if (!byType[ref.type]) byType[ref.type] = []
    byType[ref.type].push(ref)
  }

  // Standard workflow order
  const typeOrder: ArtifactReference['type'][] = ['adr', 'spec', 'contract', 'plan', 'sprompt', 'fragment']

  for (const type of typeOrder) {
    const refs = byType[type] || []
    
    if (refs.length > 0) {
      // Add each reference as a child
      for (const ref of refs) {
        root.children.push({
          id: ref.id,
          type: ref.type,
          title: ref.title,
          status: ref.status === 'exists' ? 'exists' : (ref.status === 'planned' ? 'planned' : 'missing'),
          children: [],
          level: 1,
        })
      }
    } else {
      // Add placeholder for missing artifact type
      root.children.push({
        id: `${type.toUpperCase()}-????`,
        type,
        status: 'missing',
        children: [],
        level: 1,
      })
    }
  }

  // Add child DISCs
  for (const childId of parsedDisc.childDiscs) {
    const existing = root.children.find(c => c.id === childId)
    if (!existing) {
      root.children.push({
        id: childId,
        type: 'disc',
        status: 'exists',
        children: [],
        level: 1,
      })
    }
  }

  return root
}

/**
 * Generate a context-aware prompt for creating a specific artifact
 */
export function generateArtifactPrompt(
  parsedDisc: ParsedDisc,
  targetType: ArtifactReference['type'],
  existingArtifacts: string[] = []
): string {
  const basePrompts: Record<string, string> = {
    adr: `Create an Architecture Decision Record (ADR) for the following discussion.

## Context from Source Discussion
**Discussion**: ${parsedDisc.id} - ${parsedDisc.title}
**Status**: ${parsedDisc.status}

${parsedDisc.summary ? `**Summary**: ${parsedDisc.summary}` : ''}
${parsedDisc.problemStatement ? `**Problem**: ${parsedDisc.problemStatement}` : ''}

## Requirements to Address
${parsedDisc.requirements.functional.map(r => `- ${r}`).join('\n') || '- See discussion for requirements'}

## Template
\`\`\`markdown
# ADR-XXXX: [Decision Title]

**Status**: proposed
**Created**: ${new Date().toISOString().split('T')[0]}
**Source**: ${parsedDisc.id}

## Context
[What situation requires this decision?]

## Decision
[What is the change being proposed?]

## Consequences
### Positive
- [Benefits]

### Negative
- [Tradeoffs]

## Alternatives Considered
1. [Alternative]: Rejected because [reason]
\`\`\``,

    spec: `Create a Specification (SPEC) document based on the following discussion.

## Context from Source Discussion
**Discussion**: ${parsedDisc.id} - ${parsedDisc.title}
${parsedDisc.summary ? `**Summary**: ${parsedDisc.summary}` : ''}

## Requirements to Specify
${parsedDisc.requirements.functional.map(r => `- ${r}`).join('\n') || '- See discussion for requirements'}

${existingArtifacts.length > 0 ? `## Related ADRs\n${existingArtifacts.filter(a => a.startsWith('ADR')).join(', ')}` : ''}

## Template
\`\`\`markdown
# SPEC-XXXX: [Feature Name]

**Status**: draft
**Created**: ${new Date().toISOString().split('T')[0]}
**Source**: ${parsedDisc.id}

## Overview
[Brief description]

## Functional Requirements
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-1 | [Requirement] | must | pending |

## API Contracts
[Define endpoints, schemas, etc.]

## Acceptance Criteria
- [ ] [Criterion]
\`\`\``,

    contract: `Create Pydantic data contracts based on the following discussion and specs.

## Context
**Discussion**: ${parsedDisc.id} - ${parsedDisc.title}
${existingArtifacts.length > 0 ? `**Related**: ${existingArtifacts.join(', ')}` : ''}

## Template
\`\`\`python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ExampleRequest(BaseModel):
    """Request schema."""
    field: str = Field(..., description="Description")

class ExampleResponse(BaseModel):
    """Response schema."""
    id: str
    created_at: datetime
\`\`\``,

    plan: `Create an execution Plan for implementing the following discussion.

## Context
**Discussion**: ${parsedDisc.id} - ${parsedDisc.title}
${parsedDisc.summary ? `**Summary**: ${parsedDisc.summary}` : ''}
${existingArtifacts.length > 0 ? `**Artifacts Created**: ${existingArtifacts.join(', ')}` : ''}

## Requirements to Implement
${parsedDisc.requirements.functional.map(r => `- ${r}`).join('\n') || '- See discussion'}

## Open Questions (address in plan)
${parsedDisc.openQuestions.map(q => `- ${q.id}: ${q.question} (${q.status})`).join('\n') || '- None'}

## Template (JSON)
\`\`\`json
{
  "plan_id": "PLAN-XXXX",
  "title": "${parsedDisc.title}",
  "status": "draft",
  "source_discussions": ["${parsedDisc.id}"],
  "milestones": [
    {
      "id": "M01",
      "title": "Milestone Name",
      "tasks": [
        {
          "id": "T01",
          "description": "Task description",
          "acceptance_criteria": [
            {"id": "AC-01", "description": "Criterion", "verification_command": "command"}
          ]
        }
      ]
    }
  ]
}
\`\`\``,

    sprompt: `Create an SPROMPT (Super Prompt) for autonomous AI execution of this work.

## Context
**Discussion**: ${parsedDisc.id} - ${parsedDisc.title}
${parsedDisc.delegationScope ? `**Scope**: ${parsedDisc.delegationScope}` : ''}
${existingArtifacts.length > 0 ? `**Artifacts**: ${existingArtifacts.join(', ')}` : ''}

## Template
See .sprompts/.templates/SPROMPT_TEMPLATE_v1.1.md for full structure.`,

    fragment: `Create execution Fragments (sub-tasks) from the Plan.

## Context
**Discussion**: ${parsedDisc.id}
${existingArtifacts.filter(a => a.startsWith('PLAN')).length > 0 
  ? `**Plan**: ${existingArtifacts.filter(a => a.startsWith('PLAN')).join(', ')}`
  : '**Note**: Create a Plan first before generating Fragments'}

Fragments should be atomic, testable units of work.`,

    disc: `Create a child Discussion for a sub-topic of ${parsedDisc.id}.

## Parent Context
**Parent**: ${parsedDisc.id} - ${parsedDisc.title}
${parsedDisc.summary ? `**Summary**: ${parsedDisc.summary}` : ''}

Create a focused discussion for a specific aspect that warrants its own artifact chain.`,
  }

  return basePrompts[targetType] || `Create a ${targetType.toUpperCase()} artifact for ${parsedDisc.id}`
}
