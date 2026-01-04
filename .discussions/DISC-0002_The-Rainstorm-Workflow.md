# DISC-0002: The Rainstorm ⛈️ — Nested Umbrella DISC Workflow

> **Status**: `active`
> **Created**: 2026-01-03
> **Source Chat**: `The Rainstorm Workflow Session`
> **Session**: SESSION_0018
> **Parent Discussion**: DISC-0001 (Genesis)
> **Delegation Scope**: Workflow Builder UI, nested Umbrella DISC orchestration, auto-discovery, prompt generation, chat integration
> **Priority**: 🔴 **CRITICAL** — All other work stops until this scaffold is operational

---

## Summary

> **"When the ideas are pouring down like rain, grab your Umbrella!"** ☂️

**The Rainstorm** is the canonical workflow for handling complex, multi-faceted development initiatives within AI Coding Manager. It enables:

- **Nested Umbrella DISCs** — Parent Umbrella containing child Umbrellas
- **Workflow Builder UI** — Visual orchestration of the entire artifact family
- **Auto-Discovery** — Detect new artifacts created externally (in IDE)
- **Prompt Generation** — Ready-to-use prompts for each missing artifact
- **Chat Integration** — Send prompts directly to built-in chat or external AI

**This is the default workflow** shown when a user enters AI Coding Manager without selecting a document.

---

## Problem Statement

**How do we guide users through complex multi-artifact workflows while supporting both manual copy-paste and fully integrated AI chat?**

The v0 scaffold has basic DISC/ADR creation. But when topics get complex — when multiple related discussions spawn multiple ADRs, SPECs, Contracts, and PLANs — users need:

1. A visual map of the artifact family
2. Guidance on what to create next
3. Ready prompts for AI assistance
4. Automatic detection of externally-created files
5. Seamless integration between UI and chat

---

## The Rainstorm Metaphor

```text
                    ⛈️ THE RAINSTORM ⛈️
                    
    When heavy topics fall from the sky...
    
         💧   💧   💧   💧   💧   💧
           💧   💧   💧   💧   💧
              💧   💧   💧   💧
                 💧   💧   💧
                    💧   💧
                       💧
                       
    ...you need to open your Umbrella!
    
              ☂️ UMBRELLA DISC ☂️
             /                   \
            /                     \
           /_______________________\
          |                         |
          |  Organize the chaos     |
          |  into structured        |
          |  discussions            |
          |_________________________|
                     |
         ┌───────────┼───────────┐
         ▼           ▼           ▼
       DISC        DISC        DISC
         │           │           │
         ▼           ▼           ▼
        ADR         ADR        SPEC
```

---

## Chain of Thought: The Rainstorm User Journey

### Entry Point

```text
User opens AI Coding Manager
         │
         ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │                                                                 │
   │              ⛈️ Welcome to The Rainstorm ⛈️                     │
   │                                                                 │
   │   Your ideas are pouring in. Let's organize them.              │
   │                                                                 │
   │   ┌──────────────────────────────────────────────────────────┐  │
   │   │  🌧️ "The Rainstorm" is the workflow for complex topics   │  │
   │   │     that spawn multiple discussions, decisions, and      │  │
   │   │     specifications.                                      │  │
   │   │                                                          │  │
   │   │  ☂️ Start by creating an Umbrella DISC to organize      │  │
   │   │     related discussions under a common theme.            │  │
   │   │                                                          │  │
   │   │  📋 The Workflow Builder will guide you through         │  │
   │   │     creating all the artifacts you need.                 │  │
   │   └──────────────────────────────────────────────────────────┘  │
   │                                                                 │
   │   [ Start New Rainstorm ]    [ Open Existing ]    [ Learn More ]│
   │                                                                 │
   └─────────────────────────────────────────────────────────────────┘
```

### Workflow Builder Panel

```text
┌─────────────────────────────────────────────────────────────────────────┐
│  WORKFLOW BUILDER                                        ☂️ The Rainstorm │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  UMBRELLA: DISC-0002 AI Coding Manager Product Definition               │
│  SPLAN: SPLAN-0001 (linked)                                             │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         ARTIFACT TREE                            │   │
│  │                                                                   │   │
│  │  ☂️ DISC-0002 (Umbrella)                                         │   │
│  │  ├── DISC-0003 UAM ✅                                            │   │
│  │  │   ├── ADR-0001 [+Create]                                      │   │
│  │  │   ├── SPEC-0001 [+Create]                                     │   │
│  │  │   └── Contract [+Create]                                      │   │
│  │  │                                                               │   │
│  │  ├── DISC-0004 AIKH ✅                                           │   │
│  │  │   ├── ADR-0004 [+Create]                                      │   │
│  │  │   └── SPEC-0002 [+Create]                                     │   │
│  │  │                                                               │   │
│  │  ├── DISC-0005 P2RE ✅                                           │   │
│  │  │   └── ADR-0007 [+Create]                                      │   │
│  │  │                                                               │   │
│  │  ├── ☂️ DISC-0011 The Rainstorm (Nested Umbrella) ✅             │   │
│  │  │   ├── DISC-0012 Workflow Builder UI [+Create]                 │   │
│  │  │   ├── DISC-0013 Auto-Discovery Engine [+Create]               │   │
│  │  │   └── PLAN-0010 [+Create]                                     │   │
│  │  │                                                               │   │
│  │  └── SPLAN-0001 ✅                                               │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ACTIONS                                                         │   │
│  │                                                                   │   │
│  │  [+Create] Click a node to generate prompt                       │   │
│  │  [⚡Auto-Discover] Scan for new artifacts in workspace           │   │
│  │  [💬Send to Chat] Open prompt in chat window                     │   │
│  │  [📋Copy Prompt] Copy to clipboard for external AI               │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Tree of Thought: The Rainstorm Components

```text
                      THE RAINSTORM WORKFLOW
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
       ▼                      ▼                      ▼
   ENTRY PAGE            WORKFLOW              INTEGRATION
       │                  BUILDER                    │
       │                      │                      │
   ┌───┴───┐           ┌──────┴──────┐        ┌─────┴─────┐
   │       │           │             │        │           │
Welcome  Tutorial    Tree View   Actions   Chat      IDE
 Page    Wizard      Panel       Panel    Window   Discovery
   │       │           │             │        │           │
   │       │           │             │        │           │
   ▼       ▼           ▼             ▼        ▼           ▼
Animated  Step-by   Visual      Prompt    Built-in  File
Header   Step       Hierarchy   Gen       AI Chat   Watcher
```

---

## Component Specifications

### 1. Entry Page (Welcome to The Rainstorm)

**Purpose**: Welcoming, educational landing page when no document is selected.

**Content**:

- Animated rainstorm header (tasteful, not distracting)
- Clear explanation of the workflow
- Quick-start options
- Links to tutorials and reference material

**UI Elements**:

| Element | Type | Action |
|---------|------|--------|
| Rainstorm Animation | Header | Decorative, sets mood |
| "What is The Rainstorm?" | Expandable Section | Educational content |
| "Start New Rainstorm" | Primary Button | Opens Umbrella DISC wizard |
| "Open Existing" | Secondary Button | File picker for existing Umbrella |
| "Learn More" | Link | Documentation |

### 2. Workflow Builder Panel

**Purpose**: Visual orchestration of the entire artifact family.

**Features**:

- **Tree View**: Hierarchical display of all artifacts in the family
- **Node States**: ✅ Exists, ⏳ In Progress, [+Create] Missing
- **Nested Umbrellas**: Support for Umbrella within Umbrella
- **SPLAN Link**: Shows associated Super-Plan if exists

**Interactions**:

| Action | Trigger | Result |
|--------|---------|--------|
| Click [+Create] | Missing node | Opens prompt generation panel |
| Right-click | Any node | Context menu (edit, delete, promote to Umbrella) |
| Drag | Node | Reorder within parent (updates document references) |
| Double-click | Existing node | Opens document in editor |

### 3. Auto-Discovery Engine

**Purpose**: Detect new artifacts created outside the UI (e.g., in IDE via AI assistant).

**Behavior**:

```text
File System Watcher
        │
        ▼
   New .md file in .discussions/, .adrs/, etc.
        │
        ▼
   Parse frontmatter for references
        │
        ▼
   Match to existing Workflow Builder tree
        │
        ▼
   ┌─────────────────────────────────────┐
   │  📢 New artifact detected!          │
   │                                     │
   │  ADR-0001_Schema-Validation.md      │
   │  References: DISC-0003              │
   │                                     │
   │  [ Add to Workflow ] [ Ignore ]     │
   └─────────────────────────────────────┘
```

### 4. Prompt Generation

**Purpose**: Generate ready-to-use prompts for creating the next artifact.

**Prompt Template Structure**:

```markdown
## Create {ARTIFACT_TYPE}-{NNNN}: {Suggested Title}

### Context
You are helping build the AI Coding Manager.

**Parent Document**: {parent_disc_title}
**Parent Path**: {parent_file_path}

**Relevant Context**:
{extracted_context_from_parent}

### Task
Create a new {ARTIFACT_TYPE} document that addresses:
{key_questions_from_parent}

### Output Format
Follow the template at: {template_path}

### File Location
Save to: {suggested_file_path}
```

### 5. Chat Integration

**Purpose**: Seamlessly send prompts to built-in chat or receive responses.

**Two Modes**:

| Mode | Description | Use Case |
|------|-------------|----------|
| **Integrated** | Built-in chat window | Full automation |
| **External** | Copy prompt, paste in IDE | Manual workflow |

**Chat Window Features**:

- Pre-populated with generated prompt
- Model selector (Anthropic, OpenAI, xAI, local)
- Context injection from AIKH
- Response validation (schema check)
- "Accept & Save" to create artifact file

---

## UI/UX Requirements

### Visual Design Principles

1. **Clarity over cleverness** — Information hierarchy is paramount
2. **Progressive disclosure** — Don't overwhelm; reveal complexity as needed
3. **Delightful touches** — The rainstorm animation, umbrella icons, tasteful fun
4. **Accessibility** — Full keyboard navigation, screen reader support

### Right-Click Context Menu: Create Umbrella from Selection

**Flow**:

```text
User selects multiple DISCs in sidebar
         │
         ▼
   Right-click
         │
         ▼
   ┌─────────────────────────────────┐
   │  📋 Copy                        │
   │  ✏️ Rename                      │
   │  🗑️ Delete                      │
   │  ───────────────────────────    │
   │  ☂️ Create Umbrella from        │
   │     Selection                   │
   └─────────────────────────────────┘
         │
         ▼
   Confirmation dialog (similar to v0 style)
         │
         ▼
   Opens Workflow Builder with new Umbrella
   containing selected DISCs as children
```

---

## Worst Case Scenario: The Full Rainstorm

When too many topics are falling from the sky, the structure becomes:

```text
☂️ UMBRELLA DISC (Root)
├── ☂️ UMBRELLA DISC (Nested 1)
│   ├── DISC-A
│   │   ├── ADR-A1
│   │   ├── SPEC-A1
│   │   └── Contract-A1
│   ├── DISC-B
│   │   └── ADR-B1
│   └── PLAN-1
│
├── ☂️ UMBRELLA DISC (Nested 2)
│   ├── DISC-C
│   │   ├── ADR-C1
│   │   ├── SPEC-C1
│   │   └── GUIDE-C1
│   └── PLAN-2
│
├── DISC-D (direct child)
│   └── ADR-D1
│
└── SPLAN-0001 (one per family)
```

**The Workflow Builder handles this** by:

1. Collapsible tree nodes
2. Breadcrumb navigation
3. Focus mode (zoom into nested Umbrella)
4. Minimap for large trees

---

## Implementation Priorities

### Phase 1: Entry Page & Basic Tree (Week 1)

- [ ] Rainstorm welcome page with animation
- [ ] Basic Workflow Builder tree view
- [ ] Static display of existing artifacts
- [ ] Manual refresh to detect new files

### Phase 2: Prompt Generation (Week 2)

- [ ] Prompt templates for each artifact type
- [ ] Context extraction from parent documents
- [ ] "Copy Prompt" functionality
- [ ] Template reference links

### Phase 3: Auto-Discovery (Week 3)

- [ ] File system watcher for artifact directories
- [ ] Frontmatter parser for references
- [ ] Notification system for new artifacts
- [ ] "Add to Workflow" action

### Phase 4: Chat Integration (Week 4)

- [ ] Connect Workflow Builder to chat window
- [ ] Pre-populate prompt on node click
- [ ] Response validation
- [ ] "Accept & Save" artifact creation

### Phase 5: Polish (Week 5)

- [ ] Right-click "Create Umbrella from Selection"
- [ ] Nested Umbrella support
- [ ] SPLAN integration
- [ ] Performance optimization for large trees

---

## Key Questions for ADR Production

| ID | Question | Status | Proposed Answer |
|----|----------|--------|-----------------|
| Q-1 | How to persist Workflow Builder state? | `open` | JSON in `.workflows/` |
| Q-2 | File watcher technology? | `open` | chokidar (Node.js) |
| Q-3 | Maximum nesting depth? | `open` | 3 levels recommended, unlimited supported |
| Q-4 | Prompt template storage? | `open` | `.prompts/` directory |
| Q-5 | Chat window framework? | `open` | Reuse v0 chat, enhance |

---

## Proposed ADRs from This DISC

| ADR ID | Title | Scope |
|--------|-------|-------|
| ADR-0025 | Workflow Builder Architecture | Component structure, state management |
| ADR-0026 | Auto-Discovery Engine Design | File watching, parsing, matching |
| ADR-0027 | Prompt Template System | Template format, context injection |
| ADR-0028 | Chat-Workflow Integration | Bidirectional communication |

---

## Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| DISC-0001 (Genesis) | `parent` | `active` | Root discussion |
| DISC-0010 (SPLAN) | `sibling` | `active` | Rainstorm may use SPLAN |
| DISC-0009 (AI Chat) | `soft` | `active` | Chat integration |
| v0 Frontend | `foundation` | `working` | Build upon existing UI |

---

## Terminology Update

**FRAG** replaces CHUNK in all AI Coding Manager documentation:

| Old Term | New Term | Meaning |
|----------|----------|---------|
| CHUNK | FRAG | Code fragment, smallest executable unit |

---

## Conversation Log

### 2026-01-03 - SESSION_0018

**Topics Discussed**:

- User vision for "The Rainstorm" workflow
- Nested Umbrella DISC complexity
- Workflow Builder UI requirements
- Auto-discovery from IDE-created artifacts
- Chat integration (both directions)
- Entry page design ("welcoming wiki/readme/wizard")
- Right-click to create Umbrella from selection

**Key Insights**:

- The Rainstorm is the default workflow — the entry point
- Must support manual copy-paste AND integrated chat
- Auto-discovery bridges the IDE ↔ AI Coding Manager gap
- One SPLAN per artifact family, always

**User Quote**:

> "These visions can be visions until the full AICM is built, until I get a working scaffold for our 'The Rainstorm' workflow, all other work stops. I want to use our beautiful prototype to build the real thing!!"

---

## Associated Artifacts

| Type | ID | Path | Status |
|------|-----|------|--------|
| SPROMPT | SPROMPT-0001 | `.sprompts/SPROMPT-0001_The-Rainstorm-Implementation.md` | `executed` |
| ADR | ADR-0025 | `.adrs/ADR-0025_The-Rainstorm-Architecture.md` | `accepted` |
| Component | RainstormWelcome | `frontend/src/components/workflow/RainstormWelcome.tsx` | `verified` |
| Component | WorkflowBuilder | `frontend/src/components/workflow/WorkflowBuilder.tsx` | `complete` |
| Component | ArtifactTree | `frontend/src/components/workflow/ArtifactTree.tsx` | `complete` |
| Hook | useRainstormState | `frontend/src/components/workflow/useRainstormState.ts` | `complete` |
| Evaluation | DISC-0011 | `.discussions/DISC-0011_SPROMPT-Execution-Evaluation.md` | `complete` |
| Meta-Eval | DISC-0012 | `.discussions/DISC-0012_SPROMPT-Meta-Evaluation.md` | `complete` |

---

## Resolution

**Resolution Date**: TBD

**Outcome**: TBD (Produces ADRs for Workflow Builder, Auto-Discovery, Prompt Templates, Chat Integration)

---

*DISC-0002 | The Rainstorm ⛈️ | Child of DISC-0001 | SESSION_0018*
