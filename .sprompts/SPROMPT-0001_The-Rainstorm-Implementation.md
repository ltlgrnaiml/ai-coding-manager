# SPROMPT-0001: The Rainstorm ⛈️ — Full Implementation

> **Type**: Super Prompt (SPROMPT)
> **Version**: 1.0.0
> **Created**: 2026-01-03
> **Source Discussion**: DISC-0002 (The Rainstorm)
> **Target Model**: Large Reasoning Model (Claude Opus, GPT-4o, Gemini Ultra, etc.)
> **Estimated Tokens**: ~200K context required
> **Expected Duration**: Single extended session (2-4 hours autonomous execution)

---

## ⚡ SPROMPT PROTOCOL

**SPROMPT** (Super Prompt) is designed for autonomous AI execution of complex, multi-artifact development tasks. Unlike regular prompts, an SPROMPT:

1. **Self-contains all context** — No external lookups required mid-execution
2. **Defines the full artifact chain** — RAG → DISC → ADR → SPEC → Contract → Plan → Code → Test → Validate
3. **Includes reasoning patterns** — Chain-of-Thought (CoT) and Tree-of-Thought (ToT) decision points
4. **Specifies verification gates** — Each phase has explicit success criteria
5. **Handles failure gracefully** — Rollback and retry strategies included

**Execution Mode**: Autonomous with checkpoint summaries

---

## 🎯 MISSION OBJECTIVE

Implement **"The Rainstorm ⛈️"** — the default workflow interface for AI Coding Manager (AICM) that enables:

1. **Visual artifact orchestration** via Workflow Builder tree
2. **Auto-discovery** of IDE-created artifacts
3. **Prompt generation** for missing artifacts
4. **Chat integration** (copy-paste and built-in)
5. **Nested Umbrella DISC support**

**Success Criteria**: A user can open AICM, see the Rainstorm welcome page, create an Umbrella DISC, view the artifact tree, generate prompts for missing children, and have new files auto-detected.

---

## 📚 SECTION 1: RAG CONTEXT (Read These Files First)

### 1.1 Required Reading — Foundation Documents

Execute these reads in order. Summarize key points after each.

```
READ_ORDER:
1. .discussions/DISC-0001_Genesis-AICM-Vision.md     # Foundation vision
2. .discussions/DISC-0002_The-Rainstorm-Workflow.md  # Primary requirements
3. VISION.md                                          # Product north star
4. AGENTS.md                                          # Coding standards
```

### 1.2 Required Reading — Existing Codebase

```
READ_ORDER:
5. frontend/package.json                              # Dependencies available
6. frontend/src/App.tsx                               # Router structure
7. frontend/src/pages/WorkflowManagerPage.tsx         # Current workflow page
8. frontend/src/components/workflow/index.ts          # Available components
9. frontend/src/components/workflow/EmptyState.tsx    # Current empty state
10. frontend/src/components/workflow/types.ts         # Type definitions
11. frontend/src/components/workflow/useWorkflowState.ts  # State management
12. backend/main.py                                   # API endpoints available
13. backend/services/artifact_service.py              # Artifact CRUD
```

### 1.3 Reference — Existing Patterns

```
PATTERN_FILES:
- frontend/src/components/workflow/ArtifactGraph.tsx      # Tree visualization pattern
- frontend/src/components/workflow/GenerateWorkflowModal.tsx  # Modal pattern
- frontend/src/components/workflow/WorkflowSidebar.tsx    # Sidebar pattern
- frontend/src/components/workflow/CommandPalette.tsx     # Cmd+K pattern
```

### 1.4 Templates — Artifact Formats

```
TEMPLATE_FILES:
- .discussions/.templates/DISC_TEMPLATE.md
- .adrs/.templates/ADR_TEMPLATE.json
- .plans/.templates/PLAN_TEMPLATE.json
```

---

## 🧠 SECTION 2: CHAIN OF THOUGHT — Problem Decomposition

Before writing any code, reason through this decision tree:

### CoT-1: Architecture Decision

```
QUESTION: Should The Rainstorm be a new page or enhance WorkflowManagerPage?

ANALYSIS:
├── Option A: New RainstormPage.tsx
│   ├── Pro: Clean separation, no regression risk
│   ├── Pro: Can coexist with current workflow
│   ├── Con: Code duplication with existing components
│   └── Con: Two entry points confuse users
│
├── Option B: Enhance WorkflowManagerPage.tsx
│   ├── Pro: Single source of truth for workflows
│   ├── Pro: Reuse existing sidebar, graph, reader
│   ├── Con: Risk breaking existing functionality
│   └── Con: File grows larger
│
└── Option C: WorkflowManagerPage with RainstormView component
    ├── Pro: Best of both — separation + reuse
    ├── Pro: Conditional rendering based on state
    ├── Pro: Components stay focused
    └── DECISION: ✅ SELECTED

REASONING:
The Rainstorm is the default view when NO artifact is selected.
WorkflowManagerPage already handles this case with EmptyState.
Replace EmptyState with RainstormWelcome when no workflow active.
Add WorkflowBuilder component for active Umbrella workflows.
```

### CoT-2: State Management

```
QUESTION: How should Rainstorm state be managed?

ANALYSIS:
├── Current: useWorkflowState.ts handles workflow stages
├── Need: Umbrella DISC tree structure with children
├── Need: Auto-discovery file watcher integration
├── Need: Prompt generation state

DECISION:
├── Extend useWorkflowState with umbrella-specific state
├── Create useRainstormState.ts for Rainstorm-specific logic
├── Use React Query for file system polling (no websockets needed initially)
└── Store workflow tree in .workflows/ JSON files
```

### CoT-3: Component Structure

```
TREE_OF_THOUGHT: Component Hierarchy

RainstormView/
├── RainstormWelcome.tsx          # Landing page (no workflow)
│   ├── AnimatedHeader            # Rainstorm animation
│   ├── ExplanationCard           # What is The Rainstorm?
│   └── ActionButtons             # Start New / Open Existing
│
├── WorkflowBuilder.tsx           # Main orchestration view
│   ├── WorkflowBuilderHeader     # Title, SPLAN link
│   ├── ArtifactTree.tsx          # Hierarchical tree
│   │   ├── TreeNode.tsx          # Individual node
│   │   ├── UmbrellaNode.tsx      # Umbrella-specific styling
│   │   └── CreateNodeButton.tsx  # [+Create] action
│   └── ActionPanel.tsx           # Prompt gen, copy, send
│
├── PromptGenerator.tsx           # Generate prompts for artifacts
│   ├── PromptPreview             # Show generated prompt
│   └── PromptActions             # Copy / Send to Chat
│
└── AutoDiscoveryNotification.tsx # "New artifact detected!"
```

---

## 🌳 SECTION 3: TREE OF THOUGHT — Implementation Paths

For each major component, evaluate implementation approaches:

### ToT-1: Artifact Tree Rendering

```
APPROACHES:
├── A: Flat list with indentation
│   └── Simple but limited interaction
│
├── B: Recursive TreeNode component
│   └── ✅ SELECTED — Natural for nested structure
│
└── C: Third-party tree library
    └── Overkill, adds dependency

IMPLEMENTATION:
- ArtifactTree receives flattened list with parent_id references
- Recursively renders TreeNode for each root, then children
- Collapse/expand state managed locally
- Icons indicate type: ☂️ Umbrella, 📋 DISC, 📜 ADR, etc.
```

### ToT-2: Auto-Discovery Mechanism

```
APPROACHES:
├── A: WebSocket file watcher (backend)
│   ├── Real-time but complex
│   └── Requires backend changes
│
├── B: Polling with React Query
│   ├── ✅ SELECTED — Simple, works now
│   ├── Poll every 3 seconds when Workflow Builder open
│   └── Compare with previous state, show notification
│
└── C: Manual refresh button only
    └── Poor UX, user request was auto-discovery

IMPLEMENTATION:
- useAutoDiscovery hook polls /api/devtools/artifacts
- Compares artifact list hash with previous
- When new artifact detected, parse frontmatter for parent_id
- Show notification: "ADR-0001 detected! Add to workflow?"
```

### ToT-3: Prompt Generation

```
APPROACHES:
├── A: Hardcoded templates per artifact type
│   └── Simple but inflexible
│
├── B: Template files in .prompts/ directory
│   └── ✅ SELECTED — Editable, versionable
│
└── C: LLM-generated prompts on demand
    └── Slow, unpredictable

IMPLEMENTATION:
- Load template from .prompts/{artifact_type}_TEMPLATE.md
- Inject context: parent title, parent path, extracted questions
- Show preview before copy/send
```

---

## 📋 SECTION 4: EXECUTION PLAN

Execute these phases in order. Each phase has verification criteria.

### Phase 1: Foundation (ADR + Types)

**Goal**: Establish architectural decisions and type definitions

**Tasks**:
```
[ ] 1.1 Create ADR-0025: The Rainstorm Architecture
    - Document component structure decision
    - Document state management approach
    - Document auto-discovery mechanism
    
[ ] 1.2 Extend types.ts with Rainstorm types
    - UmbrellaDisc interface
    - ArtifactTreeNode interface
    - RainstormState interface
    - PromptTemplate interface

[ ] 1.3 Create useRainstormState.ts hook
    - activeUmbrella: UmbrellaDisc | null
    - artifactTree: ArtifactTreeNode[]
    - selectedNode: ArtifactTreeNode | null
    - discoveredArtifacts: ArtifactSummary[]
```

**Verification**:
```bash
# Types compile without errors
cd frontend && npx tsc --noEmit

# Hook exports correctly
grep -r "useRainstormState" frontend/src/
```

---

### Phase 2: Welcome Page

**Goal**: Create the Rainstorm landing experience

**Tasks**:
```
[ ] 2.1 Create RainstormWelcome.tsx
    - Animated rainstorm header (CSS animation, no library)
    - "What is The Rainstorm?" expandable section
    - Three action buttons: Start New / Open Existing / Learn More

[ ] 2.2 Update EmptyState.tsx or replace with RainstormWelcome
    - Conditional: show Rainstorm when no workflow active
    - Pass onStartNew callback

[ ] 2.3 Style with Tailwind
    - Dark theme consistent with existing UI
    - Subtle animation (falling droplets)
    - Responsive layout
```

**Verification**:
```bash
# Start dev server
cd frontend && npm run dev

# Visual check: Navigate to /workflow with no selection
# Expected: See Rainstorm welcome page with animation
```

---

### Phase 3: Workflow Builder Core

**Goal**: Tree view of artifact family

**Tasks**:
```
[ ] 3.1 Create WorkflowBuilder.tsx
    - Header with Umbrella title
    - ArtifactTree component
    - Action panel

[ ] 3.2 Create ArtifactTree.tsx
    - Recursive TreeNode rendering
    - Collapse/expand functionality
    - Node states: ✅ exists, ⏳ in-progress, [+Create] missing

[ ] 3.3 Create TreeNode.tsx
    - Icon based on artifact type
    - Click to select
    - Double-click to open
    - [+Create] button for missing children

[ ] 3.4 Integrate with WorkflowManagerPage
    - Show WorkflowBuilder when Umbrella workflow active
    - Pass artifact data from existing fetch
```

**Verification**:
```bash
# Create test Umbrella DISC manually
echo "# DISC-0099: Test Umbrella" > .discussions/DISC-0099_Test-Umbrella.md

# Visual check: Select test Umbrella
# Expected: See tree view with Umbrella as root
```

---

### Phase 4: Prompt Generation

**Goal**: Generate and copy prompts for missing artifacts

**Tasks**:
```
[ ] 4.1 Create .prompts/ directory with templates
    - DISC_CREATE_PROMPT.md
    - ADR_CREATE_PROMPT.md
    - SPEC_CREATE_PROMPT.md
    - PLAN_CREATE_PROMPT.md
    - CONTRACT_CREATE_PROMPT.md

[ ] 4.2 Create PromptGenerator.tsx
    - Load template based on artifact type
    - Inject context (parent info, extracted questions)
    - Preview pane with syntax highlighting

[ ] 4.3 Create usePromptGeneration hook
    - generatePrompt(artifactType, parentContext)
    - Returns formatted prompt string

[ ] 4.4 Add copy and send actions
    - "Copy to Clipboard" button
    - "Send to Chat" button (if chat available)
```

**Verification**:
```bash
# Click [+Create] on a missing ADR node
# Expected: Prompt preview appears with context injected
# Click "Copy to Clipboard"
# Paste in external editor — verify prompt is complete
```

---

### Phase 5: Auto-Discovery

**Goal**: Detect externally created artifacts

**Tasks**:
```
[ ] 5.1 Create useAutoDiscovery hook
    - Poll /api/devtools/artifacts every 3 seconds
    - Compare with previous artifact list
    - Detect new artifacts

[ ] 5.2 Create AutoDiscoveryNotification.tsx
    - Toast-style notification
    - Shows new artifact name and inferred parent
    - "Add to Workflow" and "Ignore" buttons

[ ] 5.3 Backend: Add artifact reference parsing
    - Parse frontmatter for parent_id or references
    - Return in artifact list response

[ ] 5.4 Integrate notification into WorkflowBuilder
    - Show notification when discovery triggers
    - Update tree when "Add to Workflow" clicked
```

**Verification**:
```bash
# With Workflow Builder open, create file in another terminal:
echo "---
parent: DISC-0099
---
# ADR-0001: Test ADR" > .adrs/ADR-0001_Test.md

# Expected: Notification appears within 5 seconds
# Click "Add to Workflow" — tree updates
```

---

### Phase 6: Integration & Polish

**Goal**: Connect all pieces, handle edge cases

**Tasks**:
```
[ ] 6.1 Wire up Start New Rainstorm flow
    - Click "Start New Rainstorm"
    - Modal to create Umbrella DISC
    - Creates file, switches to Workflow Builder

[ ] 6.2 Wire up Open Existing flow
    - File picker filtered to Umbrella DISCs
    - Load existing tree structure

[ ] 6.3 Right-click context menu
    - "Create Umbrella from Selection" option
    - Creates new Umbrella with selected as children

[ ] 6.4 Error handling
    - Network failures gracefully handled
    - Invalid artifact references logged

[ ] 6.5 Performance
    - Virtualize tree for >100 nodes
    - Debounce auto-discovery polling
```

**Verification**:
```bash
# Full flow test:
1. Open AICM → See Rainstorm welcome
2. Click "Start New Rainstorm"
3. Create Umbrella DISC via modal
4. See Workflow Builder with empty tree
5. Click [+Create] on child node
6. Copy prompt, use external AI to create file
7. See auto-discovery notification
8. Click "Add to Workflow"
9. See tree update with new node
```

---

## 🔧 SECTION 5: TECHNICAL SPECIFICATIONS

### 5.1 New Type Definitions

```typescript
// Add to types.ts

export interface UmbrellaDisc {
  id: string
  title: string
  filePath: string
  children: string[]  // artifact IDs
  splanId?: string
  createdAt: string
  status: 'active' | 'resolved'
}

export interface ArtifactTreeNode {
  id: string
  type: ArtifactType | 'placeholder'
  title: string
  filePath?: string
  status: 'exists' | 'in_progress' | 'missing'
  children: ArtifactTreeNode[]
  parentId?: string
  depth: number
  isUmbrella?: boolean
}

export interface RainstormState {
  activeUmbrella: UmbrellaDisc | null
  artifactTree: ArtifactTreeNode[]
  selectedNode: ArtifactTreeNode | null
  expandedNodes: Set<string>
  discoveryEnabled: boolean
  lastDiscoveryCheck: number
}

export interface PromptTemplate {
  type: ArtifactType
  template: string
  variables: string[]  // e.g., ['parent_title', 'parent_path', 'questions']
}
```

### 5.2 API Contracts

```typescript
// GET /api/devtools/umbrella/:id/tree
interface UmbrellaTreeResponse {
  umbrella: UmbrellaDisc
  tree: ArtifactTreeNode[]
  splan?: { id: string; title: string }
}

// POST /api/devtools/umbrella
interface CreateUmbrellaRequest {
  title: string
  description: string
  children?: string[]  // existing artifact IDs to include
}

// GET /api/devtools/artifacts/discover
interface DiscoveryResponse {
  newArtifacts: ArtifactSummary[]
  suggestedParents: Record<string, string>  // artifact_id -> suggested_parent_id
}
```

### 5.3 Component Props

```typescript
// RainstormWelcome.tsx
interface RainstormWelcomeProps {
  onStartNew: () => void
  onOpenExisting: () => void
  onLearnMore: () => void
}

// WorkflowBuilder.tsx
interface WorkflowBuilderProps {
  umbrella: UmbrellaDisc
  tree: ArtifactTreeNode[]
  onNodeSelect: (node: ArtifactTreeNode) => void
  onCreateNode: (parentId: string, type: ArtifactType) => void
  onRefresh: () => void
}

// ArtifactTree.tsx
interface ArtifactTreeProps {
  nodes: ArtifactTreeNode[]
  selectedId?: string
  expandedIds: Set<string>
  onSelect: (node: ArtifactTreeNode) => void
  onCreate: (parentId: string, type: ArtifactType) => void
  onToggleExpand: (nodeId: string) => void
}

// PromptGenerator.tsx
interface PromptGeneratorProps {
  targetType: ArtifactType
  parentContext: {
    title: string
    path: string
    content: string
    openQuestions?: string[]
  }
  onCopy: () => void
  onSendToChat?: () => void
}
```

---

## ✅ SECTION 6: VERIFICATION GATES

Each gate must pass before proceeding.

### Gate 1: Types Compile
```bash
cd frontend && npx tsc --noEmit
# Exit code must be 0
```

### Gate 2: Lint Passes
```bash
cd frontend && npm run lint
# Exit code must be 0 (or only warnings)
```

### Gate 3: Dev Server Runs
```bash
cd frontend && npm run dev
# Server starts on localhost:5173
# No console errors on page load
```

### Gate 4: Welcome Page Renders
```
Manual: Navigate to /workflow with no selection
Expected: Rainstorm welcome page visible
Expected: Animation plays smoothly
Expected: All three buttons clickable
```

### Gate 5: Tree Renders
```
Manual: Create Umbrella DISC, navigate to Workflow Builder
Expected: Tree shows Umbrella as root
Expected: Placeholder nodes show [+Create]
Expected: Expand/collapse works
```

### Gate 6: Prompt Generates
```
Manual: Click [+Create] on placeholder node
Expected: Prompt preview appears
Expected: Copy to clipboard works
Expected: Prompt includes parent context
```

### Gate 7: Auto-Discovery Works
```
Manual: With Workflow Builder open, create new artifact file
Expected: Notification appears within 5 seconds
Expected: "Add to Workflow" adds node to tree
```

### Gate 8: Full Flow
```
Manual: Complete the full flow from Gate verification above
Expected: All steps complete without errors
```

---

## 🚨 SECTION 7: FAILURE HANDLING

### If Types Don't Compile
1. Check for circular imports
2. Verify all imports have correct paths
3. Run `npx tsc --noEmit 2>&1 | head -50` to see first errors

### If Component Doesn't Render
1. Check browser console for errors
2. Verify component is exported from index.ts
3. Check props are passed correctly
4. Add console.log to component to verify it's reached

### If API Fails
1. Check backend logs: `docker logs aidev-backend`
2. Verify endpoint exists in main.py
3. Test with curl: `curl http://localhost:8100/api/devtools/artifacts`

### If Auto-Discovery Doesn't Trigger
1. Verify polling is running (console.log in useAutoDiscovery)
2. Check if artifact list is changing
3. Verify comparison logic is correct

### Rollback Strategy
If a phase fails completely:
1. Git stash changes: `git stash`
2. Review the failing code
3. Simplify the approach
4. Try again with reduced scope

---

## 📤 SECTION 8: OUTPUT FORMAT

### For Each Phase, Output:

```markdown
## Phase N: [Title] — COMPLETE ✅

### Files Created/Modified:
- `path/to/file.tsx` — [description of changes]
- `path/to/file.ts` — [description of changes]

### Verification:
- [x] Gate N.1 passed: [evidence]
- [x] Gate N.2 passed: [evidence]

### Issues Encountered:
- [issue] → [resolution]

### Notes for Next Phase:
- [any context needed]
```

### Final Summary Format:

```markdown
# SPROMPT-0001 Execution Complete

## Artifacts Produced:
| Type | ID | Path | Status |
|------|-----|------|--------|
| ADR | ADR-0025 | .adrs/ADR-0025_Rainstorm-Architecture.md | ✅ |
| Component | RainstormWelcome | frontend/src/components/workflow/RainstormWelcome.tsx | ✅ |
| ... | ... | ... | ... |

## Verification Summary:
- Gates Passed: 8/8
- Tests Added: [count]
- Lines of Code: [count]

## Known Limitations:
- [any scope reductions]

## Recommended Follow-ups:
- [future improvements]
```

---

## 🎬 SECTION 9: EXECUTION START

**You are now ready to execute this SPROMPT.**

Begin with Phase 1. Read all required files from Section 1 first. Summarize key findings. Then proceed through each phase sequentially, verifying at each gate.

**Remember**:
- Quality over speed
- Follow existing patterns in the codebase
- Don't break existing functionality
- Commit logical checkpoints mentally
- If stuck, simplify and iterate

**Go.** ⛈️

---

*SPROMPT-0001 | The Rainstorm Implementation | v1.0.0 | 2026-01-03*
