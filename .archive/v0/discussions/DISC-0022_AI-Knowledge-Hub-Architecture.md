# DISC-0022: AI Knowledge Hub (AIKH) Architecture

**Status**: Draft  
**Created**: 2026-01-02  
**Author**: AI Assistant  
**Session ID**: SESSION_013  
**Priority**: CRITICAL - Core Infrastructure

---

## Summary

Define the architecture for the **AI Knowledge Hub (AIKH)** - the unified knowledge management system that consolidates research papers, concepts, citations, and semantic search into a single, integrated platform. This system becomes the knowledge backbone of the AICM, providing context enrichment for AI interactions and quick reference capabilities for all artifact types.

---

## Naming Clarification

| Current Name | Proposed Rename | Purpose |
|--------------|-----------------|---------|
| AI Knowledge Store | **AI Knowledge Hub (AIKH)** | Unified knowledge management system |
| Research Paper DB | **Research Papers Pane** | Subset of AIKH for academic papers |
| research_papers.db | `.workspace/aikh.db` | Single database for all knowledge |

**Rationale**: "Hub" implies centrality and connectivity, reflecting how knowledge radiates to all AICM components. "Store" was too passive - this system actively enriches, links, and serves knowledge.

---

## Problem Statement

Currently, the research infrastructure exists as isolated components:
1. **Research Paper DB** - SQLite with papers, chunks, embeddings
2. **Enhanced Organizer** - Concepts, citations, graphs
3. **RAG Service** - Semantic search
4. **Visualization** - D3.js graphs

**Missing Integration Points**:
- No autocomplete in chat for concepts/papers
- No quick reference panel for artifacts (DISC, ADR, SPEC)
- No context enrichment for AI prompts
- No unified search across all knowledge types
- No schema enforcement across knowledge ingestion

---

## Proposed Architecture

### 1. Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI KNOWLEDGE HUB (AIKH)                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Research   │  │   Concept   │  │  Citation   │              │
│  │   Papers    │  │   Graph     │  │   Network   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────┐      │
│  │              UNIFIED SEARCH ENGINE                     │      │
│  │  • Semantic (embeddings)  • Full-text (FTS5)          │      │
│  │  • Hybrid (RRF)           • Concept-based             │      │
│  └───────────────────────────────────────────────────────┘      │
│                          │                                       │
│         ┌────────────────┼────────────────┐                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Context    │  │   Quick     │  │   Auto-     │              │
│  │  Enricher   │  │  Reference  │  │  Complete   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │   Chat   │   │ Artifact │   │ Frontend │
    │  Panel   │   │  Editors │   │   Panes  │
    └──────────┘   └──────────┘   └──────────┘
```

### 2. Database Schema (Unified)

```sql
-- Core knowledge tables (existing, enhanced)
research_papers           -- Full paper metadata + content
paper_chunks              -- Semantic search chunks
paper_embeddings_v2       -- GPU-accelerated embeddings
extracted_concepts        -- NLP-extracted concepts
concept_cooccurrence      -- Concept relationships
paper_citations           -- Citation graph
paper_links               -- Similarity links

-- NEW: Cross-reference tables
artifact_knowledge_refs (
    id INTEGER PRIMARY KEY,
    artifact_type TEXT NOT NULL,    -- 'disc', 'adr', 'spec', 'plan'
    artifact_id TEXT NOT NULL,      -- e.g., 'DISC-0021'
    paper_id TEXT,                  -- Reference to research paper
    concept TEXT,                   -- Referenced concept
    citation_context TEXT,          -- How it's cited
    created_at TEXT DEFAULT (datetime('now'))
);

-- NEW: User annotations
knowledge_annotations (
    id INTEGER PRIMARY KEY,
    paper_id TEXT NOT NULL,
    user_note TEXT,
    highlight_text TEXT,
    tags TEXT,                      -- JSON array of tags
    created_at TEXT DEFAULT (datetime('now'))
);

-- NEW: Search history for learning
search_history (
    id INTEGER PRIMARY KEY,
    query TEXT NOT NULL,
    method TEXT,                    -- 'semantic', 'fulltext', 'hybrid'
    result_count INTEGER,
    clicked_paper_id TEXT,          -- Learning signal
    created_at TEXT DEFAULT (datetime('now'))
);
```

### 3. Integration Points

#### A. Chat Panel Autocomplete

When typing in chat, provide suggestions for:
- **Paper titles**: `@paper:` prefix triggers paper search
- **Concepts**: `@concept:` prefix triggers concept search
- **Authors**: `@author:` prefix
- **Artifacts**: `@disc:`, `@adr:`, `@spec:` prefixes

```typescript
// Example autocomplete trigger
const triggers = {
  '@paper:': searchPapers,
  '@concept:': searchConcepts,
  '@author:': searchAuthors,
  '@disc:': searchDiscussions,
  '@adr:': searchDecisions,
};
```

#### B. Context Enricher for AI Prompts

Before sending prompts to AI, automatically enrich with:
1. **Relevant papers** based on query semantic similarity
2. **Related concepts** extracted from conversation
3. **Cited decisions** from ADRs that apply
4. **Schema constraints** from contracts

```python
def enrich_context(user_message: str, max_papers: int = 3) -> EnrichedContext:
    # Semantic search for relevant papers
    papers = semantic_search(user_message, top_k=max_papers)
    
    # Extract concepts from message
    concepts = extract_concepts(user_message)
    
    # Find related ADRs
    adrs = find_related_adrs(concepts)
    
    return EnrichedContext(
        papers=papers,
        concepts=concepts,
        adrs=adrs,
        schema_hints=get_schema_hints(concepts)
    )
```

#### C. Research Papers Pane (Linked Panel)

A dedicated side panel for research papers with:

**Quick Reference Features**:
- Searchable paper list with filters
- Click to expand paper details
- Copy citation in multiple formats
- Insert reference into current document

**Drag-and-Drop**:
- Drag paper onto DISC/ADR to create reference
- Auto-generates citation link

**Keyboard Shortcuts**:
- `Ctrl+Shift+P` - Open paper search
- `Ctrl+Shift+C` - Search concepts
- `Ctrl+Shift+K` - Quick knowledge lookup

---

## Frontend Architecture

### Research Papers Pane Design

```
┌──────────────────────────────────────────┐
│  🔬 Research Papers                    ⚙️ │
├──────────────────────────────────────────┤
│ 🔍 [Search papers, concepts, authors...] │
├──────────────────────────────────────────┤
│ Filters: [Category ▼] [Year ▼] [Sort ▼]  │
├──────────────────────────────────────────┤
│                                          │
│ ┌────────────────────────────────────┐   │
│ │ 📄 Context Compression for LLMs    │   │
│ │    arXiv:2406.13618 • 2024        │   │
│ │    Keywords: compression, context  │   │
│ │    [View] [Cite] [Insert]          │   │
│ └────────────────────────────────────┘   │
│                                          │
│ ┌────────────────────────────────────┐   │
│ │ 📄 Hierarchical Memory for Agents  │   │
│ │    arXiv:2507.22925 • 2025        │   │
│ │    Keywords: memory, agents        │   │
│ │    [View] [Cite] [Insert]          │   │
│ └────────────────────────────────────┘   │
│                                          │
│ ┌────────────────────────────────────┐   │
│ │ 📊 Concept Cloud                   │   │
│ │    transformer • attention • rag   │   │
│ │    embeddings • context • memory   │   │
│ └────────────────────────────────────┘   │
│                                          │
└──────────────────────────────────────────┘
```

### Paper Detail View (Modal/Slide-out)

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Back                    📄 Paper Details                    ✕ │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ # Context Compression for Large Language Models                │
│                                                                 │
│ **Authors**: Smith, J., Doe, A., et al.                        │
│ **Published**: 2024 • arXiv:2406.13618                         │
│ **Categories**: context-compression, memory-hierarchies        │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [Abstract] [Full Text] [Figures] [Citations] [Related]      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ## Abstract                                                     │
│ This paper proposes a fast compression method preserving       │
│ semantic meaning using self-attention mechanisms for 4x        │
│ reduction in context length...                                  │
│                                                                 │
│ ## Key Concepts                                                 │
│ [transformer] [attention] [compression] [context-window]       │
│                                                                 │
│ ## Citations (12 internal, 45 external)                        │
│ • Cited by: Memory OS of AI Agent (2025)                       │
│ • Cites: Attention Is All You Need (2017)                      │
│                                                                 │
│ ────────────────────────────────────────────────────────────── │
│ [📋 Copy Citation] [📥 Download PDF] [🔗 Insert Reference]      │
└─────────────────────────────────────────────────────────────────┘
```

### Concept Graph View

```
┌─────────────────────────────────────────────────────────────────┐
│ 🧠 Concept Network                              [Filter] [Zoom] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    ┌─────────┐                                  │
│           ┌───────│ context │───────┐                           │
│           │       └────┬────┘       │                           │
│           ▼            │            ▼                           │
│     ┌──────────┐       │     ┌───────────┐                      │
│     │ memory   │◄──────┼────►│ attention │                      │
│     └────┬─────┘       │     └─────┬─────┘                      │
│          │             │           │                            │
│          ▼             ▼           ▼                            │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│    │  agents  │  │embeddings│  │transformer│                    │
│    └──────────┘  └──────────┘  └──────────┘                     │
│                                                                 │
│ Selected: "attention" (45 papers, 12 co-occurring concepts)    │
│ Related: transformer, context, memory, multi-head, self-       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Frontend Options

### Option A: Integrated Side Panel (Recommended)

**Description**: A collapsible side panel that lives alongside the main editor, providing quick access to research papers and concepts without leaving context.

**Pros**:
- Always accessible
- Non-intrusive
- Quick reference while editing
- Keyboard shortcut access

**Cons**:
- Takes horizontal space
- May be too compact for detailed viewing

**Implementation**:
```typescript
// React component structure
<Layout>
  <MainContent>
    <Editor />
  </MainContent>
  <SidePanel collapsible defaultOpen={false}>
    <ResearchPapersPane />
    <ConceptCloudPane />
  </SidePanel>
</Layout>
```

### Option B: Modal-Based Access

**Description**: Full-screen modal that opens on demand, providing comprehensive research access.

**Pros**:
- Maximum screen real estate
- Rich detail view
- Focus on research task

**Cons**:
- Context switching
- Loses sight of current work
- Extra click to access

### Option C: Command Palette Integration

**Description**: Extend existing command palette (Ctrl+K) with knowledge search capabilities.

**Pros**:
- Familiar interface pattern
- Keyboard-first
- Non-intrusive

**Cons**:
- Limited preview capabilities
- Requires typing to access

### Option D: Floating Quick Lookup (Spotlight-style)

**Description**: A floating search bar that appears on hotkey, showing results inline.

**Pros**:
- Minimal UI footprint
- Fast access
- Contextual positioning

**Cons**:
- May obstruct content
- Limited result display

### Recommended Approach: Hybrid (A + C + D)

Combine multiple access patterns:
1. **Side Panel** for persistent access during research tasks
2. **Command Palette** for quick searches
3. **Floating Lookup** for inline references while editing

---

## API Design

### REST Endpoints

```http
# Knowledge Hub Core
GET  /api/aikh/search?q={query}&type={paper|concept|all}&method={semantic|hybrid}
GET  /api/aikh/papers/{id}
GET  /api/aikh/papers/{id}/context?query={query}
GET  /api/aikh/concepts
GET  /api/aikh/concepts/{name}/papers
GET  /api/aikh/concepts/{name}/related

# Autocomplete
GET  /api/aikh/autocomplete?prefix={text}&type={paper|concept|author}

# Context Enrichment
POST /api/aikh/enrich
     Body: { message: string, max_papers: number, include_adrs: boolean }

# Cross-references
GET  /api/aikh/refs/artifact/{type}/{id}
POST /api/aikh/refs/create
     Body: { artifact_type, artifact_id, paper_id, concept, context }
```

### WebSocket for Real-time Features

```typescript
// Real-time concept highlighting
ws.on('concept:highlight', (concepts: string[]) => {
  highlightConceptsInEditor(concepts);
});

// Download progress
ws.on('download:progress', (progress: DownloadProgress) => {
  updateDownloadIndicator(progress);
});

// New paper ingested notification
ws.on('paper:ingested', (paper: PaperSummary) => {
  showNotification(`New paper: ${paper.title}`);
});
```

---

## Implementation Phases

### Phase 1: Backend Integration (1 week)
- [ ] Unify database schema
- [ ] Create context enrichment service
- [ ] Implement autocomplete API
- [ ] Add cross-reference tables

### Phase 2: Core Frontend (2 weeks)
- [ ] Research Papers side panel
- [ ] Paper detail view
- [ ] Basic search with filters
- [ ] Citation copy functionality

### Phase 3: Autocomplete & Integration (1 week)
- [ ] Chat panel autocomplete
- [ ] Artifact editor integration
- [ ] Keyboard shortcuts
- [ ] Command palette extension

### Phase 4: Advanced Features (2 weeks)
- [ ] Concept graph visualization
- [ ] Citation network view
- [ ] Context enrichment display
- [ ] Annotation system

### Phase 5: Polish & Optimization (1 week)
- [ ] Performance optimization
- [ ] Caching layer
- [ ] Mobile/responsive design
- [ ] User preferences

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Paper lookup time | < 2 seconds | Time from search to view |
| Autocomplete latency | < 200ms | Response time for suggestions |
| Context enrichment | < 500ms | Time to enrich AI prompt |
| User adoption | 80% | % of sessions using AIKH |
| Reference accuracy | 95% | Correct paper/concept matches |

---

## Dependencies

### Technical
- FastAPI for API endpoints
- React for frontend components
- D3.js for visualizations
- sentence-transformers for embeddings
- SQLite FTS5 for full-text search

### Content
- Existing research paper database (79 papers)
- Extracted concepts (498 types)
- Citation graph (2,309 citations)
- Similarity links

---

## GPU Policy (CRITICAL)

> **Policy**: GPU acceleration EVERYWHERE possible with robust fallbacks.

### GPU-First Architecture

| Component | GPU Implementation | Fallback |
|-----------|-------------------|----------|
| **Embeddings** | PyTorch + sentence-transformers (RTX 5090) | CPU batch processing |
| **Semantic Search** | GPU cosine similarity | SQLite FTS5 |
| **2D Graph** | Sigma.js (WebGL) | Cytoscape.js (Canvas) |
| **3D Graph** | deck.gl (WebGL2/WebGPU) | 2D-only mode |
| **Layout Compute** | GPU force-directed | Web Worker CPU |

### Technology Decisions (2026-01-02)

**2D Visualization**: **Sigma.js 2.0** via `@react-sigma/core`
- WebGL-native rendering
- Handles 10,000+ nodes at 60fps
- React integration with hooks
- Active development, modern API

**3D Visualization**: **deck.gl** via `@deck.gl/react`
- WebGL2/WebGPU support (GPU-native)
- By Uber/OpenJS Foundation
- Handles millions of data points
- Custom graph layers possible

**Rejected Alternatives**:
- `react-force-graph` - Too slow for large datasets, limited customization
- `vis.js` - Canvas-based, no WebGL
- `Ogma/KeyLines` - Paid enterprise licenses

### GPU Capability Detection

```typescript
interface GPUCapabilities {
  webgl2: boolean;
  webgpu: boolean;
  maxTextureSize: number;
  estimatedNodes: number; // Max nodes before fallback
}

// Auto-detect and degrade gracefully
const capabilities = detectGPUCapabilities();
if (capabilities.estimatedNodes < nodeCount) {
  // Switch to 2D-only mode
}
```

---

## First-Class Visualization Suite (2026-01-02)

> **Goal**: Replace cluttered basic graphs with **3 professional visualization modes** inspired by industry-leading tools (Connected Papers, Litmaps, ResearchRabbit).

### Visualization Mode 1: Similarity Graph (Connected Papers Style)

**Inspiration**: [Connected Papers](https://connectedpapers.com) - Industry gold standard

| Feature | Implementation |
|---------|---------------|
| **Layout** | Force-directed with similarity-based clustering |
| **Node Size** | Citation count / importance score |
| **Node Color** | Publication year gradient (darker = newer) |
| **Edge Thickness** | Cosine similarity strength from GPU embeddings |
| **Background** | Light/white for documentation quality |
| **Interaction** | Hover for tooltip, click for detail panel |

**Data Source**: GPU embeddings similarity matrix (already available)

### Visualization Mode 2: Timeline-Scatterplot (Litmaps Style)

**Inspiration**: [Litmaps](https://litmaps.com) - Best for temporal navigation

| Feature | Implementation |
|---------|---------------|
| **X-Axis** | Publication year (timeline) |
| **Y-Axis** | Citation count / impact score |
| **Quadrant Logic** | Top-right = recent + highly cited (most relevant) |
| **Connection Lines** | Citation relationships (dashed) |
| **Grid** | Year markers and citation thresholds |
| **Seed Highlight** | Origin/search papers prominently marked |

**Data Source**: Paper metadata (year, citations) + citation graph

### Visualization Mode 3: Topic Treemap (Hierarchical Clusters)

**Inspiration**: Academic topic maps, D3.js treemaps

| Feature | Implementation |
|---------|---------------|
| **Hierarchy** | Topics → Sub-topics → Papers |
| **Area Size** | Number of papers or total citations |
| **Color** | Category-based (consistent with sidebar) |
| **Labels** | Topic names, paper count per cluster |
| **Drill-down** | Click cluster to zoom into papers |
| **Breadcrumb** | Navigation path for deep exploration |

**Data Source**: Category detection + hierarchical clustering

### View Mode Selector UI

```
┌─────────────────────────────────────────────────────┐
│ [🔗 Similarity] [📅 Timeline] [📊 Topics] [⋮ 3D]   │
└─────────────────────────────────────────────────────┘
```

- Toggle between modes with preserved paper selection
- Each mode optimized for different exploration patterns
- 3D remains as advanced option (existing implementation)

### Technology Stack

| Mode | Library | GPU Acceleration |
|------|---------|-----------------|
| Similarity Graph | Sigma.js 2.0 (WebGL) | ✅ Yes |
| Timeline Scatter | D3.js + Canvas | ⚠️ Partial |
| Topic Treemap | D3.js Treemap | ⚠️ Partial |
| 3D Explorer | deck.gl (WebGL2) | ✅ Yes |

---

## Open Questions

1. ~~**Pane Position**: Left side or right side of editor?~~ **RESOLVED**: Left side, dedicated nav item
2. ~~**Default State**: Open or collapsed on startup?~~ **RESOLVED**: Full page, always visible
3. ~~**Citation Format**: BibTeX, APA, or custom markdown?~~ **RESOLVED**: BibTeX
4. **Sync Strategy**: How to handle offline access?
5. **Multi-user**: Will multiple users share the knowledge base?

---

## Related Documents

- `@/.discussions/DISC-0020_Research-Paper-Display-And-Visualization.md` - Existing visualization work
- `@/.discussions/DISC-0021_Automated-Research-Agent-System.md` - Research agent design
- `@/.discussions/DISC-017_Standalone-DevTool-Architecture.md` - AICM architecture
- `@/.sessions/SESSION_013_Enhanced-Research-Organization-System.md` - Implementation session

---

## Session Log

### 2026-01-02 - Initial Draft

**Decisions Made**:
- Rename "AI Knowledge Store" to "AI Knowledge Hub (AIKH)"
- Research Papers becomes a "pane" within AIKH
- Hybrid frontend approach (side panel + command palette + floating lookup)
- Prioritize autocomplete and context enrichment

**Next Steps**:
1. Review and refine architecture with user feedback
2. Create detailed component specifications
3. Begin Phase 1 backend integration

---

*Template version: 2.0.0 | Per ADR-0048 (Unified Artifact Model)*
