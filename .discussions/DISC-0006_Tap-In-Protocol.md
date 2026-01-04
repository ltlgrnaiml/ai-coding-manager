# DISC-0006: Tap-In Protocol (Pillar 4)

> **Status**: `active`
> **Created**: 2026-01-03
> **Source Chat**: `Conversation Memory Architecture.md`
> **Session**: SESSION_0017
> **Parent Discussion**: DISC-0003 (UAM Umbrella)
> **Delegation Scope**: Context serialization, session handoff, warm-up optimization, project state capture
> **Inherits Context**: `true`

---

## Summary

The **Tap-In Protocol** is AICM's Pillar 4 — the ability for any AI session to instantly understand a project by consuming its artifacts. This is what makes "never repeat yourself" real. When an AI "taps in," it receives the full context needed to continue work without re-explaining the project.

---

## Inherited Context (from DISC-0002)

- **Current Score**: 4/10 (weakest pillar, highest potential)
- **What's Good**: Idea documented
- **What's Great**: Core differentiator
- **Needs Enhancement**: Everything
- **Missing**: Technical specification

---

## Chain of Thought: What IS Tap-In?

### Level 1: The Promise

```
New AI Session
    │
    ▼
"Tap-In" Protocol
    │
    ├── Read AGENTS.md → Learn project rules
    ├── Read recent .sessions/ → Understand current state
    ├── Query AIKH → Get relevant context
    └── Follow UAM → Know what artifacts to produce
    │
    ▼
AI understands project instantly
    │
    ▼
Zero context re-explaining
```

### Level 2: The Challenge

| Challenge | Description | Severity |
|-----------|-------------|----------|
| **Token Budget** | Context windows are finite | HIGH |
| **Relevance** | Not all context is useful | HIGH |
| **Staleness** | Old context may be wrong | MEDIUM |
| **Cold Start** | First tap-in needs full index | MEDIUM |
| **Cross-Project** | Shared knowledge across repos | LOW (defer) |

### Level 3: The Solution Space

```
TAP-IN ARCHITECTURE
│
├── CONTEXT LAYERS (prioritized)
│   ├── L0: AGENTS.md (always included)
│   ├── L1: Recent sessions (last 3)
│   ├── L2: Current DISC/PLAN (if active)
│   ├── L3: Relevant past decisions (semantic)
│   └── L4: Research context (if applicable)
│
├── TOKEN BUDGET ALLOCATION
│   ├── System prompt: 2K tokens
│   ├── Context layers: 8K tokens
│   ├── User message: 2K tokens
│   └── Response headroom: variable
│
└── CONTEXT COMPRESSION
    ├── Summarization of old sessions
    ├── Key decisions extraction
    └── Relevance scoring
```

---

## Assessment: What's Documented

### ✅ Conceptual Model (CLEAR)

From VISION.md:
- AI reads AGENTS.md → project rules
- AI reads sessions → current state
- AI queries AIKH → relevant context
- AI follows UAM → artifact production

### ✅ Value Proposition (COMPELLING)

- **Zero ramp-up time**: No "let me explain the project"
- **Continuity across sessions**: AI "remembers"
- **Consistent context**: Same knowledge, different sessions

---

## Assessment: What's Missing

### 🔴 Context Serialization Format (MISSING)

**Problem**: No defined format for packaging context.

**Needed**:
```python
@dataclass
class TapInContext:
    """Serialized context for AI session."""
    
    # L0: Always included
    agents_md: str
    
    # L1: Recent activity
    recent_sessions: list[SessionSummary]
    
    # L2: Current work
    active_disc: Optional[DiscSummary]
    active_plan: Optional[PlanSummary]
    
    # L3: Relevant history
    related_decisions: list[ADRSummary]
    related_specs: list[SpecSummary]
    
    # L4: Knowledge
    relevant_papers: list[PaperChunk]
    relevant_concepts: list[str]
    
    # Metadata
    total_tokens: int
    timestamp: datetime
    
    def to_system_prompt(self) -> str:
        """Convert to system prompt injection."""
        ...
```

### 🔴 Token Budget Management (MISSING)

**Problem**: No strategy for fitting context into finite window.

**Needed**:
- Priority ordering of context layers
- Token counting before serialization
- Truncation strategy (summarize vs drop)
- Model-specific budget adjustment

**Proposed Algorithm**:
```python
def build_tap_in_context(
    project_path: str,
    model_context_size: int,
    user_message: str
) -> TapInContext:
    """Build context within token budget."""
    
    budget = TokenBudget(
        total=model_context_size,
        reserved_response=4000,
        reserved_user=len(user_message) * 1.5
    )
    
    context = TapInContext()
    
    # L0: Always include AGENTS.md
    context.agents_md = read_agents_md(project_path)
    budget.consume(context.agents_md)
    
    # L1: Recent sessions (up to budget)
    for session in get_recent_sessions(project_path, limit=5):
        if budget.remaining > session.tokens:
            context.recent_sessions.append(session)
            budget.consume(session)
        else:
            break
    
    # L2-L4: Relevance-based selection
    relevant = semantic_search(user_message, top_k=20)
    for item in relevant:
        if budget.remaining > item.tokens:
            context.add_relevant(item)
            budget.consume(item)
        else:
            break
    
    return context
```

### 🔴 Session Handoff Protocol (MISSING)

**Problem**: No standard for ending one session and enabling the next.

**Needed**:
- Session summary format
- What to capture at session end
- How to structure handoff notes
- Verification of session → chat alignment

**Proposed Session Summary**:
```markdown
## SESSION_0017 Summary

**Duration**: 2026-01-03 13:00 - 14:30
**Source Chat**: `Conversation Memory Architecture.md`

### Work Completed
- Created VISION.md (Genesis)
- Archived pre-Genesis artifacts
- Created Umbrella DISC-0002

### Active Work
- DISC-0003 through DISC-0009 in progress

### Next Session Should
- Continue child DISC creation
- Begin ADR production from resolved DISCs

### Key Decisions Made
- 4-digit artifact numbering adopted
- Session ↔ Chat alignment strategy defined
```

### 🔴 Warm-Up Performance (UNKNOWN)

**Problem**: No measurements of tap-in latency.

**Needed**:

- Benchmark cold start time
- Measure context assembly latency
- Define acceptable performance targets
- Optimize hot paths

**Target**: < 5 seconds for full tap-in

---

## Provenance Consumption Architecture

> **Added**: SESSION_0018 (2026-01-03)
> **Status**: ✅ Generation implemented, 🟡 Consumption in progress

### Overview

AICM generates **provenance metadata** for each DISC document that captures:

- Historical evidence chains (where concepts originated)
- Confidence scores (how certain the relationship is)
- Multi-signal match details (semantic, keyword, lexical, venue, author)

The Tap-In Protocol must **consume** this provenance to enrich AI context.

### Provenance Data Flow

```text
User asks about "P2RE evaluation metrics"
         │
         ▼
┌─────────────────────────────────────────────────┐
│ 1. DISC Lookup                                  │
│    → Load DISC-0005_P2RE.md                     │
│    → Load DISC-0005_provenance.yaml             │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ 2. Context Expansion (from evidence_chain)      │
│    → archived PLAN-0008 (72% match) — include   │
│    → concept:rag (70% match) — include          │
│    → DISC-016 (60% match) — maybe include       │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ 3. Prompt Assembly                              │
│    → DISC content                               │
│    → Key provenance metadata                    │
│    → Top 3-5 evidence snippets                  │
│    → Confidence-weighted context budget         │
└─────────────────────────────────────────────────┘
```

### Provenance File Structure

Each DISC has companion files in `.discussions/provenance/`:

| File | Content | Purpose |
| ---- | ------- | ------- |
| `DISC-XXXX_provenance.yaml` | Structured evidence chain | Machine-readable for context injection |
| `DISC-XXXX_context.md` | Markdown summary | Human-readable, can be appended to DISC |

### Provenance YAML Schema

```yaml
provenance:
  enrichment_date: '2026-01-03T17:21:50'
  confidence_score: 0.74  # Weighted average of all evidence
  sources_searched:
    - research.db
    - chatlogs.db
    - artifacts.db
    - workspace
  evidence_count: 48
  key_concepts:
    - p2re
    - agent
    - llm
    - rag
  evidence_chain:
    - source: artifacts:archived_plans
      id: archive_v0_6b144b73ec22a399
      title: '[Archived] PLAN-0008: P2RE Implementation'
      score: 0.72
      match_type: semantic
      concepts:
        - p2re
        - llm
```

### TapInContext Enhancement

The `TapInContext` dataclass should include provenance:

```python
@dataclass
class TapInContext:
    """Serialized context for AI session."""
    
    # Existing layers...
    agents_md: str
    recent_sessions: list[SessionSummary]
    active_disc: Optional[DiscSummary]
    
    # NEW: Provenance-enriched context
    disc_provenance: Optional[ProvenanceData]
    expanded_evidence: list[EvidenceSnippet]
    historical_context: str  # Generated summary
    
    def to_system_prompt(self) -> str:
        """Convert to system prompt injection with provenance."""
        sections = [
            self._format_agents_md(),
            self._format_recent_sessions(),
            self._format_active_work(),
        ]
        
        # Inject provenance if available
        if self.disc_provenance:
            sections.append(self._format_provenance_context())
        
        return "\n\n---\n\n".join(sections)
    
    def _format_provenance_context(self) -> str:
        """Format provenance for AI consumption."""
        return f"""## Historical Context (Auto-Generated)

**Confidence**: {self.disc_provenance.confidence_score:.0%}
**Key Concepts**: {', '.join(self.disc_provenance.key_concepts)}

### Evidence Chain
{self._format_top_evidence(limit=5)}

### Historical Note
{self.historical_context}
"""
```

### Context Budget Allocation (Updated)

| Layer | Budget | Content |
| ----- | ------ | ------- |
| L0 | 2K tokens | AGENTS.md (always) |
| L1 | 2K tokens | Recent sessions (last 3) |
| L2 | 2K tokens | Active DISC content |
| **L2.5** | **1K tokens** | **Provenance evidence (NEW)** |
| L3 | 2K tokens | Related decisions (semantic) |
| L4 | 1K tokens | Research context |

### Confidence-Weighted Inclusion

Evidence items are included based on confidence threshold:

```python
def select_evidence_for_context(
    provenance: ProvenanceData,
    token_budget: int
) -> list[EvidenceSnippet]:
    """Select evidence items within budget, prioritized by confidence."""
    
    selected = []
    remaining = token_budget
    
    # Sort by score descending
    for item in sorted(provenance.evidence_chain, 
                       key=lambda x: x.score, reverse=True):
        
        # Confidence threshold: include if > 60%
        if item.score < 0.60:
            continue
        
        snippet = load_evidence_snippet(item)
        if snippet.tokens <= remaining:
            selected.append(snippet)
            remaining -= snippet.tokens
        
        # Max 5 evidence items
        if len(selected) >= 5:
            break
    
    return selected
```

### Implementation Status

| Component | Status | Notes |
| --------- | ------ | ----- |
| Provenance generation | ✅ Complete | `disc_enrichment_rag.py` |
| Multi-signal matching | ✅ Complete | Semantic + keyword + lexical + venue + author |
| YAML/MD output | ✅ Complete | `.discussions/provenance/` |
| TapInContext integration | 🔴 Not started | Needs implementation |
| Context budget allocation | 🔴 Not started | Needs implementation |
| Confidence-weighted selection | 🔴 Not started | Needs implementation |

### Integration Points

| System | Integration | Priority |
| ------ | ----------- | -------- |
| **Session Handoff** | Include provenance in handoff notes | P1 |
| **Chat Backend** | Query provenance on DISC reference | P2 |
| **Agent Memory** | Tool to query provenance directly | P3 |
| **IDE Extension** | Show provenance on DISC hover | P4 |

---

## Key Questions for ADR Production

| ID | Question | Status | Proposed Answer |
|----|----------|--------|-----------------|
| Q-1 | What's the context serialization format? | `open` | Structured TapInContext object |
| Q-2 | How to handle token overflow? | `open` | Priority layers + summarization |
| Q-3 | Where is tap-in context built? | `open` | Backend service, served via API |
| Q-4 | What triggers a tap-in? | `open` | First message in new conversation |
| Q-5 | How to validate context freshness? | `open` | Timestamp + hash comparison |

---

## Proposed ADRs from This DISC

| ADR ID | Title | Scope |
|--------|-------|-------|
| ADR-0010 | Tap-In Context Serialization | Format and structure |
| ADR-0011 | Token Budget Management | Allocation strategy |
| ADR-0012 | Session Handoff Protocol | End-of-session capture |

---

## Implementation Priorities

### P1: Context Model (Week 1)

- [ ] Define TapInContext dataclass
- [ ] Implement token counting
- [ ] Create serialization methods

### P2: Budget Management (Week 2)

- [ ] Implement TokenBudget class
- [ ] Priority-based context selection
- [ ] Truncation/summarization fallback

### P3: Session Handoff (Week 3)

- [ ] Session summary template
- [ ] Auto-generation at session end
- [ ] Verification against chat logs

### P4: Performance Optimization (Week 4)

- [ ] Benchmark tap-in latency
- [ ] Cache frequently-used context
- [ ] Async pre-warming

---

## Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| DISC-0004 (AIKH) | `hard` | `pending` | Tap-In queries AIKH for context |
| DISC-0005 (P2RE) | `soft` | `pending` | Traces can inform context selection |
| DISC-0009 (AI Chat) | `hard` | `pending` | Chat triggers tap-in |

---

## Conversation Log

### 2026-01-03 - SESSION_0017

**Topics Discussed**:

- Tap-In as the core differentiator
- Context layers and prioritization
- Token budget management
- Session handoff protocol

**Key Insights**:

- Tap-In is weakest pillar but most impactful
- Token budget is the central constraint
- Session summary format enables verification
- Performance target: < 5 seconds

### 2026-01-03 - SESSION_0018

**Topics Discussed**:

- Provenance consumption architecture
- How AI agents use evidence chains
- Multi-signal matching integration
- Context budget allocation for provenance layer

**Key Insights**:

- Provenance generation is ✅ complete (`disc_enrichment_rag.py`)
- Consumption side needs implementation (TapInContext enhancement)
- New L2.5 layer allocated for provenance evidence (1K tokens)
- Confidence threshold of 60% for evidence inclusion
- Top 5 evidence items selected per DISC

---

## Resolution

**Resolution Date**: TBD

**Outcome**: TBD (Produces ADRs for context serialization, token budget, session handoff)

---

*DISC-0006 | Child of DISC-0003 | SESSION_0017*
