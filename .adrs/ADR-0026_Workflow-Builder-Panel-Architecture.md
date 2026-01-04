# ADR-0026: Workflow Builder Panel Architecture

**Status**: proposed  
**Created**: 2026-01-03  
**Decision Makers**: Human + AI  
**Related**: DISC-0002 (The Rainstorm), ADR-0025 (Rainstorm Architecture)

---

## Context

The current Workflow Manager implementation has a critical UX limitation:

1. **Linear Stepper Problem**: The horizontal 6-step stepper (Discussion → ADR → SPEC → Contract → Plan → Fragment) assumes a simple linear progression
2. **UAM Complexity**: The Unified Artifact Model supports:
   - Nested Umbrella DISCs (parent containing children)
   - 1:N artifact relationships (one DISC → multiple ADRs)
   - Cross-references between artifacts
   - Non-linear workflows (skip optional steps, branch paths)
3. **Space Competition**: Trying to embed workflow guidance into the viewer/editor panel creates cramped, competing UI concerns

### Current Pain Points

```
┌─────────────────────────────────────────────────────────────┐
│ [1]─→[2]─→[3]─→[4]─→[5]─→[6]  ← Linear, can't show nesting │
├─────────────────────────────────────────────────────────────┤
│ Sidebar │ Viewer/Editor (cramped with workflow overlays)   │
└─────────────────────────────────────────────────────────────┘
```

### What We Actually Need

```
DISC-0001 (Genesis)
├── DISC-0002 (The Rainstorm) ← Umbrella
│   ├── ADR-0025
│   ├── SPEC-0001
│   ├── DISC-0003 (UAM) ← Nested Umbrella
│   │   ├── ADR-0010
│   │   └── CONTRACT-0001
│   └── PLAN-0001
│       ├── Fragment-1
│       └── Fragment-2
└── DISC-0004 (AIKH)
    └── ...
```

---

## Decision

### 1. Separate Workflow Builder Panel

Create a **dedicated Workflow Builder view** as a first-class panel, not overlaid on the viewer:

```
┌──────────────────────────────────────────────────────────────┐
│ [Workflow Builder] [Viewer/Editor] [Graph]  ← View switcher  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  When in Workflow Builder mode:                              │
│  Full-screen canvas for artifact orchestration               │
│                                                              │
│  When in Viewer mode:                                        │
│  Full reading/editing experience (no workflow clutter)       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2. Hybrid Visualization Strategy

Use **multiple visualization modes** based on task complexity:

| Mode | Visualization | Use Case |
|------|--------------|----------|
| **Simple** | Kanban/List | Single DISC → few artifacts |
| **Standard** | Sunburst/Radial Tree | One Umbrella with children |
| **Complex** | Force-Directed Network | Multiple Umbrellas, cross-refs |
| **Flow** | Sankey Diagram | Understanding artifact dependencies |

### 3. Visualization Selection (Inspired by data-to-viz.com)

```
Your Workflow Structure:
┌─────────────────────────────────────────────────────┐
│ How many Umbrella DISCs?                            │
│ ○ Just one (Simple)                                 │
│ ○ 2-5 with nesting (Standard)                       │
│ ○ Complex web of relationships (Complex)            │
├─────────────────────────────────────────────────────┤
│ Recommended: [Sunburst View] [Try Network View]     │
└─────────────────────────────────────────────────────┘
```

### 4. Core Visualization Components

#### A. Radial Tree / Sunburst (Primary for nested Umbrellas)

```
                    ┌───────┐
              ┌─────│ DISC  │─────┐
              │     └───────┘     │
         ┌────┴────┐         ┌────┴────┐
         │   ADR   │         │  SPEC   │
         └────┬────┘         └────┬────┘
              │                   │
         ┌────┴────┐         ┌────┴────┐
         │ Contract│         │  Plan   │
         └─────────┘         └─────────┘
```

**Why**: Shows hierarchy naturally, supports drill-down, handles 1:N

#### B. Force-Directed Network (For complex cross-references)

```
    [DISC-0002]────────[ADR-0025]
         │                  │
         │            ┌─────┴─────┐
         │            │           │
    [DISC-0003]──[SPEC-0001]  [CONTRACT]
         │
    [ADR-0010]
```

**Why**: Shows arbitrary connections, auto-layouts, interactive

#### C. Sankey Flow (For understanding artifact chain)

```
DISC ═══╦═══► ADR ═══╦═══► SPEC ═══► CONTRACT
        ║            ║
        ╚═══► ADR-2  ╚═══► SPEC-2 ═══► PLAN
```

**Why**: Shows flow direction, branching, volume of work

### 5. Interaction Model

Each artifact node supports:

| Action | Trigger | Result |
|--------|---------|--------|
| **View** | Click | Opens in Viewer panel (split or switch) |
| **Edit** | Double-click | Opens in Editor |
| **Create** | Click empty node | AI Prompt modal or manual create |
| **Link** | Drag connection | Creates reference between artifacts |
| **Generate** | Right-click → "AI Generate" | Copies context-aware prompt |

### 6. Panel Layout Options

#### Option A: View Switcher (Recommended)

```
┌─────────────────────────────────────────────────────────┐
│ [🔧 Builder] [📄 Viewer] [🕸️ Graph]    Search... [⚙️]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│           (Full panel for selected view)                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Option B: Split Panel (Power Users)

```
┌───────────────────────────┬─────────────────────────────┐
│     Workflow Builder      │      Viewer/Editor          │
│     (Visualization)       │      (Selected artifact)    │
│                           │                             │
└───────────────────────────┴─────────────────────────────┘
```

---

## Implementation Strategy

### Phase 1: Dedicated Builder View
- Add "Builder" to view switcher (alongside List/Graph)
- Full-panel Sunburst/Radial Tree for current Umbrella
- Click node → switch to Viewer with that artifact

### Phase 2: Node Actions
- Empty nodes show "Create" affordance
- Right-click context menu for AI generation
- Drag to create connections

### Phase 3: Visualization Selector
- Auto-detect complexity from artifact count
- User can override visualization choice
- Remember preference per workflow

### Phase 4: Split Panel Mode
- Optional split view for power users
- Resizable panels
- Linked selection (click in Builder → shows in Viewer)

---

## Technology Choices

| Component | Library | Rationale |
|-----------|---------|-----------|
| Radial Tree/Sunburst | D3.js (already have) | Flexible, powerful |
| Force Network | react-force-graph (already have) | 2D/3D support |
| Sankey | d3-sankey | Part of D3 ecosystem |
| Interactions | Native React | Keep it simple |

---

## Consequences

### Positive
- Clean separation of concerns (building vs. viewing)
- Proper visualization for complex UAM structures
- Scalable to arbitrary nesting depth
- Intuitive navigation through artifact families

### Negative
- More complex navigation (switching views)
- Initial learning curve for visualization modes
- Additional development effort

### Mitigations
- Default to simplest view that fits the data
- Provide quick-switch keyboard shortcuts
- Seamless linking between Builder and Viewer

---

## Alternatives Considered

1. **Keep linear stepper, add sub-steps**: Rejected - doesn't solve nesting
2. **Overlay workflow on viewer**: Rejected - cramped, competing concerns
3. **Sidebar-only workflow**: Rejected - too narrow for complex visualization

---

## Open Questions

1. Should Builder view replace or supplement the existing Graph view?
2. How to handle very large artifact trees (100+ nodes)?
3. Should we support custom visualization plugins?

---

## References

- [data-to-viz.com](https://www.data-to-viz.com) - Visualization decision tree
- DISC-0002: The Rainstorm Workflow
- ADR-0025: Rainstorm Architecture
- D3.js Hierarchy Visualizations

---

*Part of: AI Coding Manager (AICM)*
