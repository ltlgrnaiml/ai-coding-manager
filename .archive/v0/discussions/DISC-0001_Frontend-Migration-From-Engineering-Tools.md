# DISC-0001: Frontend Migration from Engineering-Tools

> **Status**: Active  
> **Created**: 2026-01-01  
> **Context**: Migrating fully functional UI/UX from engineering-tools to ai-coding-manager (AICM)

---

## Executive Summary

The `engineering-tools` repository contains a **production-ready UI/UX** with:
- **Workflow Manager** - FSM-based artifact workflow (Discussion → ADR → Spec → Contract → Plan)
- **2D/3D Graph Visualizer** - React Force Graph with interactive node/edge visualization
- **Form Editors** - Schema-driven dynamic forms for ADRs, Specs, Plans, Discussions
- **Document Viewers** - JSON, Markdown, Python code with syntax highlighting
- **AI Integration** - LLM health checks, prompt generation, artifact generation
- **RAG System** - Knowledge archive with embeddings, search, context building
- **Command Palette** - Cmd+K global search across all artifacts

**Key Principle**: All existing code in AICM is **100% fungible**. Every file must change during refactor. Files not modified by end of development must be manually reviewed.

---

## Source Project Analysis: engineering-tools

### Directory Structure (Relevant Parts)

```
engineering-tools/
├── apps/homepage/frontend/         # Main UI application
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── HealthIndicator.tsx
│   │   │   └── workflow/           # 30+ workflow components
│   │   │       ├── ArtifactGraph.tsx        # 2D/3D force graph
│   │   │       ├── ArtifactGraph3D.tsx      # 3D-only variant
│   │   │       ├── ArtifactReader.tsx       # Document viewer
│   │   │       ├── ArtifactEditor.tsx       # Slide-in editor panel
│   │   │       ├── ArtifactList.tsx         # Sidebar artifact list
│   │   │       ├── WorkflowSidebar.tsx      # Left sidebar with tabs
│   │   │       ├── WorkflowHeader.tsx       # Top header with actions
│   │   │       ├── WorkflowStepper.tsx      # Horizontal stage stepper
│   │   │       ├── CommandPalette.tsx       # Cmd+K search
│   │   │       ├── ADRViewer.tsx            # Human-readable ADR display
│   │   │       ├── ADREditorForm.tsx        # Schema-driven ADR form
│   │   │       ├── SpecViewer.tsx           # SPEC display
│   │   │       ├── PlanViewer.tsx           # Plan display
│   │   │       ├── JsonRenderer.tsx         # JSON syntax highlighting
│   │   │       ├── MarkdownRenderer.tsx     # Markdown rendering
│   │   │       ├── CodeRenderer.tsx         # Python/code rendering
│   │   │       ├── GenerateWorkflowModal.tsx # AI-Full mode modal
│   │   │       ├── ReviewApprovePanel.tsx   # Generated artifact review
│   │   │       ├── EmptyState.tsx           # Empty/onboarding states
│   │   │       ├── types.ts                 # TypeScript types
│   │   │       ├── workflowUtils.ts         # Workflow stage logic
│   │   │       ├── useWorkflowState.ts      # Local workflow state hook
│   │   │       └── index.ts                 # Barrel exports
│   │   ├── hooks/
│   │   │   └── useWorkflowApi.ts    # API hooks for artifacts, graphs, LLM
│   │   ├── lib/
│   │   │   └── utils.ts             # cn() utility for Tailwind
│   │   └── pages/
│   │       ├── WorkflowManagerPage.tsx  # Main workflow page
│   │       ├── DevToolsPage.tsx         # DevTools page
│   │       └── HomePage.tsx             # Landing page
│   └── package.json                 # Dependencies
│
├── gateway/                         # Python FastAPI backend
│   ├── main.py                      # API entry point
│   ├── routes/
│   │   └── knowledge.py             # Knowledge/RAG routes
│   └── services/
│       ├── devtools_service.py      # DevTools API (1000+ lines)
│       ├── workflow_service.py      # Workflow FSM logic
│       ├── llm_service.py           # LLM integration
│       └── knowledge/               # RAG subsystem
│           ├── database.py          # SQLite vector store
│           ├── embedding_service.py # Embedding generation
│           ├── search_service.py    # Semantic search
│           ├── context_builder.py   # RAG context building
│           ├── chunking.py          # Document chunking
│           ├── parsers.py           # File parsers
│           └── sanitizer.py         # Content sanitization
│
└── shared/contracts/                # Pydantic schemas
    ├── devtools/
    │   ├── api.py                   # DevTools API contracts
    │   ├── workflow.py              # Workflow state contracts
    │   └── bug.py                   # Bug tracking contracts
    ├── core/
    │   ├── dataset.py
    │   ├── pipeline.py
    │   └── rendering.py
    └── adr_schema.py                # ADR Pydantic model
```

---

## Target Project Analysis: ai-coding-manager

### Current State (Minimal)

```
ai-coding-manager/frontend/
├── src/
│   ├── App.tsx                 # Simple 2-route app (Chat, Workflow)
│   ├── views/
│   │   ├── ChatView.tsx        # Basic chat interface
│   │   └── WorkflowView.tsx    # Placeholder workflow view
│   ├── main.tsx
│   └── index.css
├── package.json                # Fewer dependencies than source
└── vite.config.ts
```

### Current Dependencies (ai-coding-manager)
```json
{
  "clsx": "^2.0.0",
  "lucide-react": "^0.294.0",
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-markdown": "^10.1.0",
  "react-router-dom": "^6.20.0",
  "react-syntax-highlighter": "^16.1.0",
  "tailwind-merge": "^2.1.0"
}
```

### Missing Dependencies (Need to Add)
```json
{
  "@monaco-editor/react": "^4.7.0",       // Code editor
  "@tanstack/react-query": "^5.8.0",       // Data fetching
  "@types/three": "^0.182.0",              // 3D types
  "react-force-graph-2d": "^1.29.0",       // 2D graph
  "react-force-graph-3d": "^1.29.0",       // 3D graph
  "three": "^0.182.0"                      // 3D rendering
}
```

---

## Migration Strategy

### Phase 1: Foundation (Standalone Page Working)

**Goal**: Get `/workflow` route serving the full WorkflowManagerPage

#### 1.1 Frontend Files to Copy

| Source Path | Target Path | Notes |
|-------------|-------------|-------|
| `apps/homepage/frontend/src/components/workflow/*` | `frontend/src/components/workflow/*` | All 30+ components |
| `apps/homepage/frontend/src/hooks/useWorkflowApi.ts` | `frontend/src/hooks/useWorkflowApi.ts` | API hooks |
| `apps/homepage/frontend/src/lib/utils.ts` | `frontend/src/lib/utils.ts` | cn() utility |
| `apps/homepage/frontend/src/pages/WorkflowManagerPage.tsx` | `frontend/src/pages/WorkflowManagerPage.tsx` | Main page |

#### 1.2 Backend Files to Copy

| Source Path | Target Path | Notes |
|-------------|-------------|-------|
| `gateway/services/devtools_service.py` | `backend/services/devtools_service.py` | DevTools API |
| `gateway/services/workflow_service.py` | `backend/services/workflow_service.py` | Workflow FSM |
| `gateway/services/llm_service.py` | `backend/services/llm_service.py` | LLM integration |
| `shared/contracts/devtools/*` | `contracts/devtools/*` | API contracts |

#### 1.3 Package.json Updates

```bash
cd frontend
npm install @monaco-editor/react @tanstack/react-query react-force-graph-2d react-force-graph-3d three @types/three
```

### Phase 2: Backend Integration

**Goal**: Wire up FastAPI backend with all DevTools endpoints

#### 2.1 Files to Create/Migrate

| Source | Target | Action |
|--------|--------|--------|
| `gateway/main.py` | `backend/main.py` | Merge router mounts |
| `gateway/services/knowledge/*` | `backend/services/knowledge/*` | Full RAG subsystem |

#### 2.2 API Endpoint Mapping

| Endpoint | Purpose |
|----------|---------|
| `GET /api/devtools/artifacts` | List all artifacts |
| `GET /api/devtools/artifacts/graph` | Get relationship graph |
| `GET /api/devtools/artifacts/{id}` | Get single artifact |
| `POST /api/devtools/artifacts` | Create artifact |
| `PUT /api/devtools/artifacts/{id}` | Update artifact |
| `DELETE /api/devtools/artifacts/{id}` | Delete artifact |
| `POST /api/devtools/workflows` | Create workflow |
| `GET /api/devtools/workflows/{id}/status` | Get workflow status |
| `POST /api/devtools/workflows/{id}/advance` | Advance workflow stage |
| `GET /api/devtools/artifacts/{id}/prompt` | Get AI prompt |
| `POST /api/devtools/artifacts/generate` | Generate artifact |
| `POST /api/devtools/workflows/{id}/generate-all` | AI-Full mode |
| `GET /api/devtools/llm/health` | LLM health check |
| `POST /api/devtools/llm/model` | Set LLM model |
| `GET /api/devtools/schemas` | List JSON schemas |
| `GET /api/devtools/schemas/{type}` | Get schema |

### Phase 3: Full Refactor

**Goal**: Every file in AICM modified to work with new architecture

---

## Component Inventory (30+ Components)

### Core Components
1. **WorkflowSidebar** - Left panel with artifact list and tabs
2. **SidebarTabs** - Discussion/ADR/Spec/Plan/Contract tabs
3. **ArtifactList** - Scrollable list of artifacts per type

### Graph Components
4. **ArtifactGraph** - 2D/3D force-directed graph (619 lines)
5. **ArtifactGraph3D** - 3D-specific implementation
6. **GraphToolbar** - Graph controls and settings

### Reader Components
7. **ArtifactReader** - Main document viewer with format detection
8. **JsonRenderer** - JSON with syntax highlighting
9. **MarkdownRenderer** - Markdown rendering with react-markdown
10. **CodeRenderer** - Python/code with react-syntax-highlighter

### Viewer Components (Human-Readable)
11. **ADRViewer** - Structured ADR display
12. **SpecViewer** - SPEC display
13. **PlanViewer** - Plan/milestone display
14. **SchemaViewer** - JSON Schema display
15. **SchemaInterpreter** - Dynamic form from schema

### Editor Components
16. **ArtifactEditor** - Slide-in editor panel
17. **EditorForm** - Base form component
18. **ADREditorForm** - ADR-specific form
19. **SpecEditorForm** - SPEC-specific form
20. **DiscussionEditorForm** - Discussion form
21. **PlanEditorForm** - Plan form

### UI Components
22. **WorkflowHeader** - Top header with actions
23. **NewWorkflowDropdown** - Workflow type selector
24. **CommandPalette** - Cmd+K global search
25. **WorkflowStepper** - Horizontal stage progress
26. **ActivityFeed** - Recent activity display
27. **EmptyState** - Onboarding/empty states
28. **WorkflowStartedState** - Workflow in-progress state

### AI Components
29. **GenerateWorkflowModal** - AI-Full mode modal
30. **ReviewApprovePanel** - Review generated artifacts

### Utilities
31. **types.ts** - TypeScript type definitions
32. **workflowUtils.ts** - Stage logic helpers
33. **useWorkflowState.ts** - Local state management
34. **index.ts** - Barrel exports

---

## Key Types (from types.ts)

```typescript
export type ArtifactType = 'discussion' | 'adr' | 'spec' | 'plan' | 'contract'
export type ArtifactStatus = 'draft' | 'active' | 'deprecated' | 'superseded' | 'completed'
export type FileFormat = 'json' | 'markdown' | 'python' | 'unknown'
export type WorkflowMode = 'manual' | 'ai_lite' | 'ai_full'
export type WorkflowScenario = 'new_feature' | 'bug_fix' | 'architecture_change' | 'enhancement' | 'data_structure'
export type WorkflowStage = 'discussion' | 'adr' | 'spec' | 'contract' | 'plan'

export interface ArtifactSummary {
  id: string
  type: ArtifactType
  title: string
  status: ArtifactStatus
  file_path: string
  file_format: FileFormat
  updated_date?: string
}

export interface GraphNode {
  id: string
  type: ArtifactType
  label: string
  status: ArtifactStatus
  file_path: string
}

export interface GraphEdge {
  source: string
  target: string
  relationship: string
}
```

---

## Refactor Guidelines

### Rule: Every File Must Change

Per user requirement, **every single file** in the project must be modified during this migration. Files not touched by end of development must be manually reviewed.

### Tracking Approach

Create a checklist of all files and mark as modified:

```
# File Modification Tracking
- [ ] frontend/src/App.tsx
- [ ] frontend/src/main.tsx
- [ ] frontend/src/index.css
- [ ] frontend/src/views/ChatView.tsx (DELETE or merge)
- [ ] frontend/src/views/WorkflowView.tsx (REPLACE)
- [ ] frontend/package.json
- [ ] frontend/vite.config.ts
- [ ] frontend/tailwind.config.js
- [ ] frontend/tsconfig.json
- [ ] backend/main.py
- [ ] backend/requirements.txt
- [ ] contracts/__init__.py
- [ ] contracts/adr_schema.py
- [ ] contracts/plan_schema.py
- [ ] contracts/discussion_schema.py
... (all files)
```

---

## Immediate Next Steps

1. **Install missing dependencies** in `frontend/package.json`
2. **Copy workflow components** from engineering-tools
3. **Update App.tsx** to mount WorkflowManagerPage at `/workflow`
4. **Copy API hooks** and adjust API_BASE URL
5. **Test standalone frontend** with mock data
6. **Wire up backend** with devtools_service
7. **Full integration test**

---

## Open Questions

| ID | Question | Status |
|----|----------|--------|
| Q-1 | Should we keep ChatView or merge it into the workflow? | open |
| Q-2 | Backend port: keep 8080 or switch to 8000 like engineering-tools? | open |
| Q-3 | Should we copy the full RAG subsystem immediately or defer? | open |

---

## References

- Source: `\\wsl$\Ubuntu\home\mycahya\coding\engineering-tools`
- Target: `\\wsl$\Ubuntu\home\mycahya\coding\ai-coding-manager`
- ADR-0045 (engineering-tools): DevTools Workflow Manager UI
- PLAN-001 (engineering-tools): Workflow Manager Implementation
