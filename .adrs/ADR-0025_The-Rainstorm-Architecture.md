# ADR-0025: The Rainstorm Architecture

> **Status**: `active`  
> **Date**: 2026-01-03  
> **Author**: SESSION_017  
> **Parent DISC**: DISC-0002

## Context

The Rainstorm is the canonical workflow for handling complex, multi-faceted development initiatives within AI Coding Manager. It requires:

- Visual orchestration of artifact families
- Auto-discovery of externally created artifacts
- Prompt generation for missing artifacts
- Support for nested Umbrella DISCs
- Integration with existing workflow system

## Decision

### Component Structure: WorkflowManagerPage with RainstormView

**Selected**: Option C - WorkflowManagerPage with RainstormView component

**Reasoning**:
- The Rainstorm is the default view when NO artifact is selected
- WorkflowManagerPage already handles this case with EmptyState
- Replace EmptyState with RainstormWelcome when no workflow active
- Add WorkflowBuilder component for active Umbrella workflows
- Components stay focused and reusable

### State Management

**Decision**: Hybrid approach
- Extend useWorkflowState with umbrella-specific state
- Create useRainstormState.ts for Rainstorm-specific logic
- Use React Query for file system polling (no websockets initially)
- Store workflow tree in `.workflows/` JSON files

### Component Hierarchy

```
RainstormView/
├── RainstormWelcome.tsx          # Landing page (no workflow)
├── WorkflowBuilder.tsx           # Main orchestration view
│   ├── WorkflowBuilderHeader
│   ├── ArtifactTree.tsx          # Hierarchical tree
│   └── ActionPanel.tsx           # Prompt gen, copy, send
├── PromptGenerator.tsx           # Generate prompts
└── AutoDiscoveryNotification.tsx # New artifact detected
```

## Implementation Approach

### Artifact Tree Rendering
- **Selected**: Recursive TreeNode component
- Natural for nested structure
- Collapse/expand state managed locally
- Icons indicate type: ☂️ Umbrella, 📋 DISC, 📜 ADR

### Auto-Discovery Mechanism
- **Selected**: Polling with React Query
- Poll every 3 seconds when Workflow Builder open
- Compare with previous state, show notification
- Simple implementation, no backend changes needed initially

### Prompt Generation
- **Selected**: Template files in `.prompts/` directory
- Editable, versionable templates
- Context injection from parent documents

## Consequences

### Positive
- Clean separation between Rainstorm and existing workflow
- Reuses existing components and patterns
- Progressive enhancement without breaking existing functionality
- Supports both manual and AI-assisted workflows

### Negative
- Polling approach may have slight delay in detection
- Additional state management complexity
- Need to maintain template files

## Alternatives Considered

1. **New RainstormPage.tsx**: Rejected - would duplicate existing components
2. **Enhance WorkflowManagerPage directly**: Rejected - file would grow too large
3. **WebSocket file watcher**: Deferred - adds complexity, polling sufficient for MVP

## Related ADRs
- ADR-0026: Auto-Discovery Engine Design (future)
- ADR-0027: Prompt Template System (future)
- ADR-0028: Chat-Workflow Integration (future)

---

*ADR-0025 | The Rainstorm Architecture | SESSION_017*
