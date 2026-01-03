# SESSION_002: Frontend Migration Analysis

> **Date**: 2026-01-01  
> **Task**: Analyze engineering-tools UI/UX for migration to AICM  
> **Status**: Complete

---

## Summary

Completed comprehensive analysis of the `engineering-tools` repository to identify components needed for migration to `ai-coding-manager`.

## Work Completed

1. **Explored engineering-tools structure**
   - Identified `apps/homepage/frontend/` as the main UI source
   - Found 30+ workflow components in `src/components/workflow/`
   - Located backend services in `gateway/services/`

2. **Analyzed key components**
   - `WorkflowManagerPage.tsx` - Main orchestrating page (250 lines)
   - `ArtifactGraph.tsx` - 2D/3D force graph visualizer (619 lines)
   - `useWorkflowApi.ts` - API hooks (346 lines)
   - `devtools_service.py` - Backend API (1000+ lines)

3. **Compared with ai-coding-manager**
   - Current AICM frontend is minimal (~87 lines in App.tsx)
   - Missing dependencies: react-force-graph, @monaco-editor/react, three
   - No workflow components exist yet

4. **Created migration discussion**
   - `DISC-002_Frontend-Migration-From-Engineering-Tools.md`
   - Documents all 30+ components to migrate
   - Lists API endpoints to implement
   - Defines 3-phase migration strategy

## Key Findings

### Components to Migrate (30+)

| Category | Components |
|----------|-----------|
| Core | WorkflowSidebar, SidebarTabs, ArtifactList |
| Graph | ArtifactGraph, ArtifactGraph3D, GraphToolbar |
| Readers | ArtifactReader, JsonRenderer, MarkdownRenderer, CodeRenderer |
| Viewers | ADRViewer, SpecViewer, PlanViewer, SchemaViewer |
| Editors | ArtifactEditor, ADREditorForm, SpecEditorForm, PlanEditorForm |
| UI | WorkflowHeader, CommandPalette, WorkflowStepper, EmptyState |
| AI | GenerateWorkflowModal, ReviewApprovePanel |

### Dependencies to Add

```json
{
  "@monaco-editor/react": "^4.7.0",
  "@tanstack/react-query": "^5.8.0",
  "react-force-graph-2d": "^1.29.0",
  "react-force-graph-3d": "^1.29.0",
  "three": "^0.182.0",
  "@types/three": "^0.182.0"
}
```

### Backend Services Required

- `devtools_service.py` - DevTools API endpoints
- `workflow_service.py` - Workflow FSM logic
- `llm_service.py` - LLM integration
- `knowledge/` - RAG subsystem (database, embeddings, search)

## Artifacts Created

- `.discussions/DISC-002_Frontend-Migration-From-Engineering-Tools.md`
- `.sessions/SESSION_002_DISC-002_Frontend-Migration-Analysis.md`

## Next Steps

1. Install missing npm dependencies
2. Copy workflow components from engineering-tools
3. Update App.tsx to mount WorkflowManagerPage
4. Wire up backend with devtools_service
5. Test standalone frontend

## Open Questions

- Q-1: Keep ChatView or merge into workflow?
- Q-2: Backend port 8080 vs 8000?
- Q-3: Copy RAG subsystem immediately or defer?

---

## Handoff Notes

The migration plan is complete. Ready to begin Phase 1 implementation:
copying workflow components and getting `/workflow` route serving the full UI.
