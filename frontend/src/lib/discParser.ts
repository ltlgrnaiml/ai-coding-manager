/**
 * DISC Parser - Comprehensive extraction of Discussion document content
 * 
 * Extracts ALL relevant context for AI prompt generation:
 * - Full sections (summary, problem statement, components, etc.)
 * - Artifact references with context
 * - Key questions for ADR production
 * - Proposed artifacts with scope
 * - Dependencies and relationships
 * - Implementation priorities
 * - UI/UX requirements
 * - Conversation insights
 */

export interface ArtifactReference {
  type: 'adr' | 'spec' | 'contract' | 'plan' | 'disc' | 'sprompt' | 'fragment' | 'splan'
  id: string
  title?: string
  scope?: string
  status: 'exists' | 'planned' | 'referenced'
  context?: string
  // NEW: Categorization
  category: 'proposed' | 'dependency' | 'concept' | 'archived'
  isArchived: boolean
}

export interface ProposedArtifact {
  type: string
  id: string
  title: string
  scope: string
}

export interface KeyQuestion {
  id: string
  question: string
  status: string
  proposedAnswer?: string
}

export interface Dependency {
  id: string
  type: string
  status: string
  notes?: string
}

export interface ComponentSpec {
  name: string
  purpose: string
  features: string[]
  interactions: string[]
}

export interface ParsedDisc {
  // Core metadata
  id: string
  title: string
  status: string
  created?: string
  session?: string
  priority?: string
  
  // Parent/child relationships
  parentDisc?: string
  delegationScope?: string
  
  // Rich content sections
  summary?: string
  problemStatement?: string
  metaphor?: string
  
  // Structured data - CATEGORIZED
  references: ArtifactReference[]
  proposedArtifacts: ProposedArtifact[]  // Artifacts TO BE CREATED from this DISC
  dependencies: Dependency[]              // Artifacts this DISC DEPENDS ON
  archivedReferences: ArtifactReference[] // Legacy/archived docs (reference only)
  conceptReferences: ArtifactReference[]  // Topic/concept mentions (not actionable)
  childDiscs: string[]
  keyQuestions: KeyQuestion[]
  componentSpecs: ComponentSpec[]
  
  // Requirements
  requirements: {
    functional: string[]
    nonFunctional: string[]
  }
  uiuxRequirements: string[]
  implementationPhases: Array<{ phase: string; tasks: string[] }>
  
  // Legacy fields
  openQuestions: Array<{ id: string; question: string; status: string; proposedAnswer?: string }>
  
  // Raw sections for context injection
  rawSections: Record<string, string>
  
  // Conversation insights
  keyInsights: string[]
  userQuotes: string[]
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
  splan: /SPLAN-(\d{4})/gi,
}

/**
 * Extract a named section from markdown content
 */
function extractSection(content: string, sectionName: string): string | undefined {
  // Match ## Section Name or ### Section Name
  const pattern = new RegExp(
    `##[#]?\\s*${sectionName}[\\s\\S]*?\\n+([\\s\\S]*?)(?=\\n##[^#]|\\n---\\s*\\n|$)`,
    'i'
  )
  const match = content.match(pattern)
  return match ? match[1].trim() : undefined
}

/**
 * Extract all sections as a map
 */
function extractAllSections(content: string): Record<string, string> {
  const sections: Record<string, string> = {}
  const sectionPattern = /^##\s+(.+?)$/gm
  let lastMatch: RegExpExecArray | null = null
  let lastIndex = 0
  let lastName = ''

  const matches = [...content.matchAll(sectionPattern)]
  for (let i = 0; i < matches.length; i++) {
    const match = matches[i]
    if (lastName && lastMatch) {
      const endIndex = match.index
      sections[lastName] = content.substring(lastIndex, endIndex).trim()
    }
    lastName = match[1].trim()
    lastIndex = (match.index || 0) + match[0].length
    lastMatch = match
  }
  // Capture last section
  if (lastName && lastMatch) {
    sections[lastName] = content.substring(lastIndex).trim()
  }
  return sections
}

/**
 * Parse a markdown table into rows
 */
function parseTable(tableContent: string): Array<Record<string, string>> {
  const lines = tableContent.split('\n').filter(l => l.trim().startsWith('|'))
  if (lines.length < 2) return []
  
  // Parse header
  const headerCells = lines[0].split('|').filter(c => c.trim()).map(c => c.trim().toLowerCase())
  
  // Skip separator line (index 1)
  const rows: Array<Record<string, string>> = []
  for (let i = 2; i < lines.length; i++) {
    const cells = lines[i].split('|').filter(c => c.trim() !== '').map(c => c.trim())
    const row: Record<string, string> = {}
    headerCells.forEach((header, idx) => {
      row[header] = cells[idx] || ''
    })
    rows.push(row)
  }
  return rows
}

/**
 * Parse a DISC document and extract ALL relevant context
 */
export function parseDisc(content: string, discId: string): ParsedDisc {
  const references: ArtifactReference[] = []
  const childDiscs: string[] = []
  const seenIds = new Set<string>()
  
  // Extract all sections for raw access
  const rawSections = extractAllSections(content)

  // === METADATA EXTRACTION ===
  
  // Title from first H1
  const titleMatch = content.match(/^#\s+(.+?)$/m)
  const title = titleMatch ? titleMatch[1].trim() : discId

  // Status from blockquote metadata
  const statusMatch = content.match(/>\s*\*\*Status\*\*:\s*`?(\w+)`?/i)
  const status = statusMatch ? statusMatch[1].toLowerCase() : 'draft'

  // Created date
  const createdMatch = content.match(/>\s*\*\*Created\*\*:\s*(.+?)(?:\n|$)/i)
  const created = createdMatch ? createdMatch[1].trim() : undefined

  // Session
  const sessionMatch = content.match(/>\s*\*\*Session\*\*:\s*(.+?)(?:\n|$)/i)
  const session = sessionMatch ? sessionMatch[1].trim() : undefined

  // Priority
  const priorityMatch = content.match(/>\s*\*\*Priority\*\*:\s*(.+?)(?:\n|$)/i)
  const priority = priorityMatch ? priorityMatch[1].trim() : undefined

  // Parent Discussion
  const parentMatch = content.match(/>\s*\*\*Parent Discussion\*\*:\s*(DISC-\d{4})/i)
  const parentDisc = parentMatch ? parentMatch[1] : undefined

  // Delegation Scope
  const scopeMatch = content.match(/>\s*\*\*Delegation Scope\*\*:\s*(.+?)(?:\n|$)/i)
  const delegationScope = scopeMatch ? scopeMatch[1].trim() : undefined

  // === RICH CONTENT SECTIONS ===

  // Summary - full content including quotes
  const summary = extractSection(content, 'Summary')

  // Problem Statement - full content
  const problemStatement = extractSection(content, 'Problem Statement')

  // The metaphor section (e.g., "The Rainstorm Metaphor")
  const metaphorSection = Object.entries(rawSections).find(([key]) => 
    key.toLowerCase().includes('metaphor')
  )
  const metaphor = metaphorSection ? metaphorSection[1] : undefined

  // === KEY QUESTIONS FOR ADR PRODUCTION ===
  const keyQuestions: KeyQuestion[] = []
  const questionsSection = extractSection(content, 'Key Questions for ADR Production') ||
                           extractSection(content, 'Open Questions')
  if (questionsSection) {
    const rows = parseTable(questionsSection)
    for (const row of rows) {
      if (row['id'] || row['question']) {
        keyQuestions.push({
          id: row['id'] || '',
          question: row['question'] || '',
          status: row['status'] || 'open',
          proposedAnswer: row['proposed answer'] || row['answer'] || undefined,
        })
      }
    }
  }

  // === PROPOSED ARTIFACTS FROM THIS DISC ===
  const proposedArtifacts: ProposedArtifact[] = []
  const proposedSection = extractSection(content, 'Proposed ADRs from This DISC') ||
                          extractSection(content, 'Proposed Artifacts')
  if (proposedSection) {
    const rows = parseTable(proposedSection)
    for (const row of rows) {
      if (row['adr id'] || row['id'] || row['type']) {
        proposedArtifacts.push({
          type: row['type'] || 'ADR',
          id: row['adr id'] || row['id'] || '',
          title: row['title'] || '',
          scope: row['scope'] || '',
        })
      }
    }
  }

  // === DEPENDENCIES ===
  const dependencies: Dependency[] = []
  const depsSection = extractSection(content, 'Dependencies')
  if (depsSection) {
    const rows = parseTable(depsSection)
    for (const row of rows) {
      if (row['dependency'] || row['id']) {
        dependencies.push({
          id: row['dependency'] || row['id'] || '',
          type: row['type'] || '',
          status: row['status'] || '',
          notes: row['notes'] || '',
        })
      }
    }
  }

  // === COMPONENT SPECIFICATIONS ===
  const componentSpecs: ComponentSpec[] = []
  const compSection = extractSection(content, 'Component Specifications')
  if (compSection) {
    // Parse numbered component sections like "### 1. Entry Page"
    const compMatches = compSection.matchAll(/###\s*\d+\.\s*(.+?)(?:\n\n|\n(?=###))([\s\S]*?)(?=###\s*\d+\.|\n---\s*\n|$)/g)
    for (const match of compMatches) {
      const name = match[1].trim()
      const body = match[2].trim()
      
      // Extract purpose
      const purposeMatch = body.match(/\*\*Purpose\*\*:\s*(.+?)(?:\n|$)/i)
      const purpose = purposeMatch ? purposeMatch[1].trim() : ''
      
      // Extract features list
      const features: string[] = []
      const featuresMatch = body.match(/\*\*Features\*\*:\s*([\s\S]*?)(?=\n\*\*|\n###|$)/i)
      if (featuresMatch) {
        const featureItems = featuresMatch[1].matchAll(/[-*]\s*\*\*(.+?)\*\*:\s*(.+)/g)
        for (const item of featureItems) {
          features.push(`${item[1]}: ${item[2]}`)
        }
      }
      
      // Extract interactions table
      const interactions: string[] = []
      const interMatch = body.match(/\*\*Interactions\*\*:\s*([\s\S]*?)(?=\n\*\*|\n###|$)/i)
      if (interMatch) {
        const rows = parseTable(interMatch[1])
        for (const row of rows) {
          if (row['action'] || row['trigger']) {
            interactions.push(`${row['action'] || row['trigger']}: ${row['result'] || ''}`)
          }
        }
      }
      
      componentSpecs.push({ name, purpose, features, interactions })
    }
  }

  // === UI/UX REQUIREMENTS ===
  const uiuxRequirements: string[] = []
  const uiuxSection = extractSection(content, 'UI/UX Requirements') ||
                      extractSection(content, 'Visual Design Principles')
  if (uiuxSection) {
    const principles = uiuxSection.matchAll(/\d+\.\s*\*\*(.+?)\*\*\s*[-—]\s*(.+)/g)
    for (const p of principles) {
      uiuxRequirements.push(`${p[1]}: ${p[2]}`)
    }
  }

  // === IMPLEMENTATION PHASES ===
  const implementationPhases: Array<{ phase: string; tasks: string[] }> = []
  const implSection = extractSection(content, 'Implementation Priorities')
  if (implSection) {
    const phaseMatches = implSection.matchAll(/###\s*(.+?)\n([\s\S]*?)(?=###|$)/g)
    for (const match of phaseMatches) {
      const phase = match[1].trim()
      const taskContent = match[2]
      const tasks: string[] = []
      const taskMatches = taskContent.matchAll(/[-*]\s*\[.\]\s*(.+)/g)
      for (const t of taskMatches) {
        tasks.push(t[1].trim())
      }
      if (tasks.length > 0) {
        implementationPhases.push({ phase, tasks })
      }
    }
  }

  // === KEY INSIGHTS AND USER QUOTES ===
  const keyInsights: string[] = []
  const userQuotes: string[] = []
  const conversationSection = extractSection(content, 'Conversation Log') ||
                              extractSection(content, 'Key Insights')
  if (conversationSection) {
    // Extract key insights
    const insightMatches = conversationSection.matchAll(/[-*]\s*(.+)/g)
    for (const match of insightMatches) {
      keyInsights.push(match[1].trim())
    }
    
    // Extract user quotes
    const quoteMatches = conversationSection.matchAll(/>\s*"(.+?)"/g)
    for (const match of quoteMatches) {
      userQuotes.push(match[1].trim())
    }
  }

  // === ARTIFACT REFERENCES WITH CATEGORIZATION ===
  const archivedReferences: ArtifactReference[] = []
  const conceptReferences: ArtifactReference[] = []
  
  for (const [type, pattern] of Object.entries(ARTIFACT_PATTERNS)) {
    const matches = content.matchAll(pattern)
    for (const match of matches) {
      const id = `${type.toUpperCase()}-${match[1]}`
      
      // Skip self-references
      if (id === discId) continue
      
      // Skip duplicates
      if (seenIds.has(id)) continue
      seenIds.add(id)

      // Determine context
      const lineIndex = content.substring(0, match.index).split('\n').length
      const lines = content.split('\n')
      const contextLine = lines[lineIndex - 1] || ''

      // Detect if archived (in .archive folder or marked deprecated)
      const isArchived = /\.archive|archived|deprecated|legacy|obsolete/i.test(contextLine)
      
      // Check if this is a proposed artifact (from "Proposed ADRs" table)
      const proposedArtifact = proposedArtifacts.find(p => p.id === id)
      
      // Check if this is a dependency (from "Dependencies" table)
      const isDependency = dependencies.some(d => d.id === id)
      
      // Determine category
      let category: ArtifactReference['category'] = 'concept'
      if (isArchived) {
        category = 'archived'
      } else if (proposedArtifact) {
        category = 'proposed'
      } else if (isDependency) {
        category = 'dependency'
      }

      const reference: ArtifactReference = {
        type: type as ArtifactReference['type'],
        id,
        title: proposedArtifact?.title,
        scope: proposedArtifact?.scope,
        status: proposedArtifact ? 'planned' : 'referenced',
        context: contextLine.trim().substring(0, 150),
        category,
        isArchived,
      }

      // Route to appropriate list
      if (isArchived) {
        archivedReferences.push(reference)
      } else if (category === 'concept') {
        conceptReferences.push(reference)
      } else {
        references.push(reference)
      }

      // Track child DISCs
      if (type === 'disc') {
        childDiscs.push(id)
      }
    }
  }

  // === FUNCTIONAL REQUIREMENTS ===
  const functionalReqs: string[] = []
  // Look for numbered lists with checkboxes or bullet lists in Summary
  if (summary) {
    const enablesMatches = summary.matchAll(/[-*]\s*\*\*(.+?)\*\*\s*[-—]\s*(.+)/g)
    for (const match of enablesMatches) {
      functionalReqs.push(`${match[1]}: ${match[2]}`)
    }
  }

  return {
    id: discId,
    title,
    status,
    created,
    session,
    priority,
    parentDisc,
    delegationScope,
    summary,
    problemStatement,
    metaphor,
    references,
    proposedArtifacts,
    dependencies,
    archivedReferences,
    conceptReferences,
    childDiscs,
    keyQuestions,
    componentSpecs,
    requirements: {
      functional: functionalReqs,
      nonFunctional: [],
    },
    uiuxRequirements,
    implementationPhases,
    openQuestions: keyQuestions,
    rawSections,
    keyInsights,
    userQuotes,
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
 * Generate a COMPREHENSIVE, context-aware prompt for creating a specific artifact
 * 
 * This is a FIRST-CLASS prompt generator that extracts and injects ALL relevant
 * context from the source DISC into the prompt, enabling AI to produce high-quality
 * artifacts without needing to read the source document.
 */
export function generateArtifactPrompt(
  parsedDisc: ParsedDisc,
  targetType: ArtifactReference['type'],
  existingArtifacts: string[] = [],
  targetArtifactId?: string
): string {
  const today = new Date().toISOString().split('T')[0]
  
  // Find the specific proposed artifact if we have an ID
  const proposedArtifact = targetArtifactId 
    ? parsedDisc.proposedArtifacts.find(p => p.id === targetArtifactId)
    : parsedDisc.proposedArtifacts.find(p => p.type.toLowerCase() === targetType)

  // Build the common context header
  const buildContextHeader = () => `
# AI Coding Manager (AICM) — Artifact Generation Task

You are helping build the **AI Coding Manager (AICM)**, a sophisticated development orchestration platform.

---

## Source Discussion: ${parsedDisc.id}

**Title**: ${parsedDisc.title}
**Status**: \`${parsedDisc.status}\`
**Created**: ${parsedDisc.created || 'Unknown'}
${parsedDisc.session ? `**Session**: ${parsedDisc.session}` : ''}
${parsedDisc.priority ? `**Priority**: ${parsedDisc.priority}` : ''}
${parsedDisc.parentDisc ? `**Parent**: ${parsedDisc.parentDisc}` : ''}
${parsedDisc.delegationScope ? `**Delegation Scope**: ${parsedDisc.delegationScope}` : ''}
`

  // Build the problem context section
  const buildProblemContext = () => {
    let context = ''
    
    if (parsedDisc.summary) {
      context += `
## Summary

${parsedDisc.summary}
`
    }
    
    if (parsedDisc.problemStatement) {
      context += `
## Problem Statement

${parsedDisc.problemStatement}
`
    }
    
    return context
  }

  // Build functional requirements section
  const buildRequirements = () => {
    if (parsedDisc.requirements.functional.length === 0) return ''
    
    return `
## Functional Requirements (from DISC)

${parsedDisc.requirements.functional.map((r, i) => `${i + 1}. ${r}`).join('\n')}
`
  }

  // Build key questions section (critical for ADRs)
  const buildKeyQuestions = () => {
    if (parsedDisc.keyQuestions.length === 0) return ''
    
    return `
## Key Questions to Address

These questions were identified in the source discussion and MUST be addressed:

| ID | Question | Status | Proposed Answer |
|----|----------|--------|-----------------|
${parsedDisc.keyQuestions.map(q => 
  `| ${q.id} | ${q.question} | ${q.status} | ${q.proposedAnswer || '*Address in artifact*'} |`
).join('\n')}
`
  }

  // Build component specifications
  const buildComponentSpecs = () => {
    if (parsedDisc.componentSpecs.length === 0) return ''
    
    return `
## Component Specifications (from DISC)

${parsedDisc.componentSpecs.map(c => `
### ${c.name}

**Purpose**: ${c.purpose}

${c.features.length > 0 ? `**Features**:\n${c.features.map(f => `- ${f}`).join('\n')}` : ''}

${c.interactions.length > 0 ? `**Interactions**:\n${c.interactions.map(i => `- ${i}`).join('\n')}` : ''}
`).join('\n')}
`
  }

  // Build UI/UX requirements
  const buildUIUXRequirements = () => {
    if (parsedDisc.uiuxRequirements.length === 0) return ''
    
    return `
## UI/UX Design Principles

${parsedDisc.uiuxRequirements.map((r, i) => `${i + 1}. ${r}`).join('\n')}
`
  }

  // Build dependencies section
  const buildDependencies = () => {
    if (parsedDisc.dependencies.length === 0) return ''
    
    return `
## Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
${parsedDisc.dependencies.map(d => 
  `| ${d.id} | ${d.type} | ${d.status} | ${d.notes} |`
).join('\n')}
`
  }

  // Build implementation phases
  const buildImplementationPhases = () => {
    if (parsedDisc.implementationPhases.length === 0) return ''
    
    return `
## Implementation Phases (from DISC)

${parsedDisc.implementationPhases.map(p => `
### ${p.phase}

${p.tasks.map(t => `- [ ] ${t}`).join('\n')}
`).join('\n')}
`
  }

  // Build existing artifacts context (only proposed/dependency, not concepts)
  const buildExistingArtifacts = () => {
    const actionable = existingArtifacts.filter(a => 
      !parsedDisc.conceptReferences.some(c => c.id === a)
    )
    if (actionable.length === 0) return ''
    
    return `
## Already Created Artifacts

${actionable.map(a => `- ${a}`).join('\n')}
`
  }

  // Build archived references (legacy only, clearly marked)
  const buildArchivedReferences = () => {
    if (parsedDisc.archivedReferences.length === 0) return ''
    
    return `
## ⚠️ Legacy References (Archived)

These are **archived/deprecated** documents. Reference for historical context only:
${parsedDisc.archivedReferences.map(r => `- ~~${r.id}~~: ${r.context || 'archived'}`).join('\n')}
`
  }

  // Build concept references (informational only, not actionable)
  const buildConceptReferences = () => {
    if (parsedDisc.conceptReferences.length === 0) return ''
    
    // Only show if there are many concept refs cluttering things
    if (parsedDisc.conceptReferences.length < 3) return ''
    
    return `
## Related Concepts (Informational)

These are mentioned for context but are NOT part of this artifact chain:
${parsedDisc.conceptReferences.slice(0, 5).map(r => `- ${r.id}`).join('\n')}
`
  }

  // Build key insights (keep concise)
  const buildKeyInsights = () => {
    if (parsedDisc.keyInsights.length === 0 && parsedDisc.userQuotes.length === 0) return ''
    
    let section = ''
    
    // Only include user quotes if present - these are high value
    if (parsedDisc.userQuotes.length > 0) {
      section += '\n## User Vision\n\n'
      section += parsedDisc.userQuotes.slice(0, 1).map(q => `> "${q}"`).join('\n')
    }
    
    return section
  }

  // === TYPE-SPECIFIC PROMPTS ===

  const generateADRPrompt = () => {
    const proposedADR = proposedArtifact || parsedDisc.proposedArtifacts.find(p => p.type === 'ADR')
    
    return `${buildContextHeader()}

---

# TASK: Create Architecture Decision Record (ADR)

${proposedADR ? `
## Target Artifact

**ID**: ${proposedADR.id}
**Title**: ${proposedADR.title}
**Scope**: ${proposedADR.scope}
` : ''}

${buildProblemContext()}

${buildKeyQuestions()}

${buildComponentSpecs()}

${buildUIUXRequirements()}

${buildDependencies()}

${buildExistingArtifacts()}

${buildKeyInsights()}

---

# OUTPUT REQUIREMENTS

Create a complete ADR following this structure. **Address ALL key questions** from above.

## File Location

Save to: \`.adrs/${proposedADR?.id || 'ADR-XXXX'}_${proposedADR?.title?.replace(/\s+/g, '-') || 'Title'}.md\`

## Template

\`\`\`markdown
# ${proposedADR?.id || 'ADR-XXXX'}: ${proposedADR?.title || '[Decision Title]'}

> **Status**: \`proposed\`
> **Created**: ${today}
> **Source**: ${parsedDisc.id}
> **Scope**: ${proposedADR?.scope || '[Scope from discussion]'}

---

## Context

[Provide detailed context. Reference the problem statement and key questions from the DISC.
Explain WHY this decision is needed and what constraints exist.]

---

## Decision

[State the decision clearly and concisely. Use active voice.
"We will..." or "The system shall..."]

### Key Design Choices

1. **[Choice 1]**: [Rationale]
2. **[Choice 2]**: [Rationale]

---

## Consequences

### Positive

- [Benefit 1]
- [Benefit 2]

### Negative

- [Tradeoff 1]
- [Tradeoff 2]

### Neutral

- [Observation that is neither positive nor negative]

---

## Alternatives Considered

### Alternative 1: [Name]

**Description**: [What was this alternative?]

**Rejected because**: [Why was it not chosen?]

### Alternative 2: [Name]

**Description**: [What was this alternative?]

**Rejected because**: [Why was it not chosen?]

---

## Implementation Notes

[Practical guidance for implementing this decision]

---

## Open Questions Addressed

${parsedDisc.keyQuestions.length > 0 ? parsedDisc.keyQuestions.map(q => 
  `| ${q.id} | ${q.question} | **[Your answer]** |`
).join('\n') : '| ID | Question | Answer |\n|-------|----------|--------|'}

---

## References

- Source: ${parsedDisc.id}
${existingArtifacts.length > 0 ? existingArtifacts.map(a => `- Related: ${a}`).join('\n') : ''}

---

*${proposedADR?.id || 'ADR-XXXX'} | ${parsedDisc.id} | Created ${today}*
\`\`\`

---

**IMPORTANT**: 
- Address EVERY key question from the discussion
- Reference specific component specs where relevant
- Ensure consistency with existing artifacts
- Follow AICM documentation standards
`
  }

  const generateSPECPrompt = () => `${buildContextHeader()}

---

# TASK: Create Specification Document (SPEC)

${buildProblemContext()}

${buildRequirements()}

${buildComponentSpecs()}

${buildUIUXRequirements()}

${buildImplementationPhases()}

${buildExistingArtifacts()}

---

# OUTPUT REQUIREMENTS

Create a comprehensive SPEC document.

## File Location

Save to: \`.specs/SPEC-XXXX_[Feature-Name].md\`

## Template

\`\`\`markdown
# SPEC-XXXX: [Feature Name]

> **Status**: \`draft\`
> **Created**: ${today}
> **Source**: ${parsedDisc.id}
${existingArtifacts.filter(a => a.startsWith('ADR')).length > 0 
  ? `> **Implements**: ${existingArtifacts.filter(a => a.startsWith('ADR')).join(', ')}`
  : ''}

---

## Overview

[Comprehensive overview of the feature/component being specified]

---

## Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
${parsedDisc.requirements.functional.map((r, i) => 
  `| FR-${String(i + 1).padStart(2, '0')} | ${r} | must | [Criterion] |`
).join('\n') || '| FR-01 | [Requirement] | must | [Criterion] |'}

---

## Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-01 | Performance | [Requirement] |
| NFR-02 | Security | [Requirement] |
| NFR-03 | Accessibility | [Requirement] |

---

## Component Specifications

${parsedDisc.componentSpecs.length > 0 ? parsedDisc.componentSpecs.map(c => `
### ${c.name}

**Purpose**: ${c.purpose}

**Features**:
${c.features.map(f => `- ${f}`).join('\n') || '- [Feature]'}

**API**:
\`\`\`typescript
interface ${c.name.replace(/\s+/g, '')}Props {
  // Define props
}
\`\`\`
`).join('\n') : '[Define components]'}

---

## Data Models

\`\`\`typescript
// Define data models here
\`\`\`

---

## API Contracts

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/... | [Description] |
| POST | /api/... | [Description] |

### Request/Response Schemas

[Define schemas]

---

## User Interface Specifications

${parsedDisc.uiuxRequirements.length > 0 ? `
### Design Principles

${parsedDisc.uiuxRequirements.map((r, i) => `${i + 1}. ${r}`).join('\n')}
` : ''}

### Wireframes

[Describe or link wireframes]

### Interaction Patterns

[Describe key interactions]

---

## Testing Requirements

| Test Type | Scope | Criteria |
|-----------|-------|----------|
| Unit | [Component] | [Criteria] |
| Integration | [Flow] | [Criteria] |
| E2E | [Journey] | [Criteria] |

---

## Implementation Phases

${parsedDisc.implementationPhases.length > 0 ? parsedDisc.implementationPhases.map(p => `
### ${p.phase}

${p.tasks.map(t => `- [ ] ${t}`).join('\n')}
`).join('\n') : '[Define phases]'}

---

## Open Questions

${parsedDisc.keyQuestions.filter(q => q.status === 'open').map(q => 
  `- [ ] ${q.id}: ${q.question}`
).join('\n') || '- None'}

---

*SPEC-XXXX | ${parsedDisc.id} | Created ${today}*
\`\`\`
`

  const generatePlanPrompt = () => `${buildContextHeader()}

---

# TASK: Create Execution Plan

${buildProblemContext()}

${buildRequirements()}

${buildImplementationPhases()}

${buildDependencies()}

${buildExistingArtifacts()}

${buildKeyInsights()}

---

# OUTPUT REQUIREMENTS

Create a detailed execution Plan in JSON format.

## File Location

Save to: \`.plans/PLAN-XXXX_[Brief-Title].json\`

## Template

\`\`\`json
{
  "plan_id": "PLAN-XXXX",
  "title": "${parsedDisc.title}",
  "status": "draft",
  "created": "${today}",
  "source_discussions": ["${parsedDisc.id}"],
  "related_artifacts": ${JSON.stringify(existingArtifacts)},
  "priority": "${parsedDisc.priority || 'medium'}",
  
  "milestones": [
${parsedDisc.implementationPhases.length > 0 
  ? parsedDisc.implementationPhases.map((p, i) => `    {
      "id": "M${String(i + 1).padStart(2, '0')}",
      "title": "${p.phase}",
      "status": "pending",
      "tasks": [
${p.tasks.map((t, j) => `        {
          "id": "T${String(i + 1).padStart(2, '0')}-${String(j + 1).padStart(2, '0')}",
          "description": "${t}",
          "status": "pending",
          "acceptance_criteria": [
            {
              "id": "AC-01",
              "description": "[Specific criterion]",
              "verification_command": "[Command to verify]"
            }
          ]
        }`).join(',\n')}
      ]
    }`).join(',\n')
  : `    {
      "id": "M01",
      "title": "[Milestone Name]",
      "status": "pending",
      "tasks": [
        {
          "id": "T01-01",
          "description": "[Task description]",
          "status": "pending",
          "acceptance_criteria": [
            {
              "id": "AC-01",
              "description": "[Criterion]",
              "verification_command": "[Command]"
            }
          ]
        }
      ]
    }`}
  ],
  
  "open_questions": ${JSON.stringify(parsedDisc.keyQuestions.filter(q => q.status === 'open').map(q => ({
    id: q.id,
    question: q.question,
    blocker: false
  })))},
  
  "dependencies": ${JSON.stringify(parsedDisc.dependencies.map(d => ({
    artifact_id: d.id,
    type: d.type,
    status: d.status
  })))}
}
\`\`\`
`

  const generateContractPrompt = () => `${buildContextHeader()}

---

# TASK: Create Pydantic Data Contracts

${buildProblemContext()}

${buildComponentSpecs()}

${buildExistingArtifacts()}

---

# OUTPUT REQUIREMENTS

Create type-safe Pydantic models for the data contracts.

## File Location

Save to: \`contracts/[feature]_contracts.py\`

## Template

\`\`\`python
"""
Data Contracts for ${parsedDisc.title}

Source: ${parsedDisc.id}
Created: ${today}
${existingArtifacts.length > 0 ? `Related: ${existingArtifacts.join(', ')}` : ''}
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# === ENUMS ===

class Status(str, Enum):
    """Standard status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


# === BASE MODELS ===

class BaseContract(BaseModel):
    """Base model with common configuration."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


# === DOMAIN MODELS ===

${parsedDisc.componentSpecs.length > 0 ? parsedDisc.componentSpecs.map(c => `
class ${c.name.replace(/\s+/g, '')}(BaseContract):
    """
    ${c.purpose}
    
    Features:
    ${c.features.map(f => `    - ${f}`).join('\n') || '    - [Features]'}
    """
    
    id: UUID = Field(..., description="Unique identifier")
    # Add fields based on component specification
    
`).join('\n') : `
class ExampleModel(BaseContract):
    """Example model - replace with actual domain models."""
    
    id: UUID = Field(..., description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=255)
    status: Status = Field(default=Status.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
`}


# === REQUEST/RESPONSE MODELS ===

class CreateRequest(BaseContract):
    """Request model for creation endpoints."""
    pass


class UpdateRequest(BaseContract):
    """Request model for update endpoints."""
    pass


class ListResponse(BaseContract):
    """Paginated list response."""
    
    items: list[BaseContract] = Field(default_factory=list)
    total: int = Field(ge=0)
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)
\`\`\`
`

  const generateSPROMPTPrompt = () => `${buildContextHeader()}

---

# TASK: Create Super Prompt (SPROMPT)

${buildProblemContext()}

${buildRequirements()}

${buildComponentSpecs()}

${buildImplementationPhases()}

${buildKeyQuestions()}

${buildExistingArtifacts()}

${buildKeyInsights()}

---

# OUTPUT REQUIREMENTS

Create a comprehensive SPROMPT for autonomous AI execution.

## File Location

Save to: \`.sprompts/SPROMPT-XXXX_[Brief-Title].md\`

## Template

Reference the template at: \`.sprompts/.templates/SPROMPT_TEMPLATE_v1.1.md\`

Key sections to include:
1. **RAG Context**: List all files the AI should read
2. **Execution Phases**: Based on implementation phases from DISC
3. **Verification Gates**: Define checkpoints between phases
4. **Acceptance Criteria**: From key questions and requirements
5. **Rollback Strategy**: How to recover from failures

Include the full delegation scope: ${parsedDisc.delegationScope || '[Define scope]'}
`

  // === DISPATCH TO TYPE-SPECIFIC GENERATOR ===

  const generators: Record<string, () => string> = {
    adr: generateADRPrompt,
    spec: generateSPECPrompt,
    plan: generatePlanPrompt,
    contract: generateContractPrompt,
    sprompt: generateSPROMPTPrompt,
    splan: generatePlanPrompt, // Reuse plan template for now
    fragment: () => `${buildContextHeader()}

# TASK: Create Execution Fragment

Create an atomic, testable unit of work from the parent Plan.

${buildExistingArtifacts()}

Fragments should be small enough to complete in a single session.
`,
    disc: () => `${buildContextHeader()}

# TASK: Create Child Discussion (DISC)

Create a focused sub-discussion for a specific aspect of ${parsedDisc.id}.

${buildProblemContext()}

The child DISC should:
1. Focus on a specific sub-topic
2. Reference the parent: ${parsedDisc.id}
3. Define its own artifact chain
`,
  }

  return generators[targetType]?.() || generators.adr()
}
