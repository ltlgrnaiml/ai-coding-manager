# DISC-0021: Automated Research Paper Agent System

> **Status**: `planned`
> **Created**: 2026-01-02
> **Updated**: 2026-01-02 (Q&A + Research)
> **Author**: Human + AI
> **AI Session**: SESSION_010
> **Depends On**: DISC-006 (Knowledge-Archive-RAG-System), DISC-018 (Meta-Agent-Self-Improvement-System)
> **Blocks**: None
> **Dependency Level**: L1

---

## Summary

Design an automated multi-agent system that continuously scrapes, analyzes, and recommends research papers to keep AICM informed of best practices. The system surfaces actionable insights and can automatically generate upgrade plans for legacy codebases to adopt current best practices.

---

## Context

### Background

The AI-assisted development landscape evolves rapidly. New techniques, frameworks, and architectural patterns emerge from academic research and industry practice. Currently, staying updated requires manual effort—reading papers, extracting insights, and determining applicability.

AICM already has:
- **PDF extraction tool** (`scripts/extract_pdf_papers.py`) for structured paper parsing
- **Knowledge Archive RAG system** (DISC-006) for storing and retrieving knowledge
- **Meta-Agent patterns** (DISC-018) for self-improvement capabilities
- **Hierarchical artifact system** for managing decisions, plans, and implementations

### Trigger

User request to build an automated research pipeline that:
1. Scrapes relevant papers from sources (arXiv, Semantic Scholar, etc.)
2. Analyzes and summarizes content via LLM agents
3. Surfaces recommendations for AICM improvements
4. Generates plug-and-play upgrade artifacts for legacy systems

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: **Paper Discovery Agent** - Continuously monitor and scrape research papers from configurable sources (arXiv, Semantic Scholar, ACL Anthology, etc.)
- [ ] **FR-2**: **Relevance Filter Agent** - Score and filter papers based on relevance to AI coding assistance, agentic workflows, and software engineering
- [ ] **FR-3**: **Analysis Agent** - Extract key insights, techniques, and patterns from papers using LLM-powered analysis
- [ ] **FR-4**: **Trend Aggregator** - Identify emerging trends across multiple papers and track evolution over time
- [ ] **FR-5**: **Recommendation Engine** - Surface actionable suggestions for AICM improvements based on analyzed research
- [ ] **FR-6**: **Upgrade Plan Generator** - For target legacy systems, generate complete artifact chains (DISC → ADR → PLAN) to adopt best practices
- [ ] **FR-7**: **Exclusion Rules Engine** - Allow configuration of what NOT to upgrade (protected paths, patterns, dependencies)
- [ ] **FR-8**: **Plug-and-Play Adapter** - Connect to external codebases and analyze their current state before generating upgrade plans

### Non-Functional Requirements

- [ ] **NFR-1**: **Background Operation** - Run asynchronously without blocking user workflows
- [ ] **NFR-2**: **Cost Efficiency** - Use tiered LLM approach (cheap models for filtering, expensive for deep analysis)
- [ ] **NFR-3**: **Auditability** - All recommendations must trace back to source papers with citations
- [ ] **NFR-4**: **Incremental Updates** - Support resumable scraping and avoid reprocessing known papers

---

## Constraints

- **C-1**: Must respect rate limits and terms of service for paper sources
- **C-2**: Paper storage must comply with copyright (store metadata + extracted insights, not full PDFs unless permitted)
- **C-3**: Generated upgrade plans must be human-reviewable before execution
- **C-4**: System must work with existing AICM artifact hierarchy (DISC → ADR → PLAN)

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Which paper sources should we prioritize? | `answered` | **World rankings by citation count** for topic areas. Sources ranked by academic impact. |
| Q-2 | How do we define "relevance" for AI coding assistance papers? | `answered` | **Adapt best method from deep research** - see Research Findings below (SPECTER2, citation metrics). |
| Q-3 | Should the system auto-execute upgrade plans or require human approval? | `answered` | **Human-in-the-loop ALWAYS**, with tiered step-down as trust improves. |
| Q-4 | How do we handle conflicting recommendations from different papers? | `answered` | **Present ALL options to user**, record feedback to improve decisions next time. |
| Q-5 | What's the target LLM provider for analysis agents? | `answered` | **xAI** (Grok) to start. |
| Q-6 | How do we test upgrade plans on legacy systems without breaking them? | `answered` | **Git branch policy + enforcement** - see Research Findings below. Needs deep research before implementation. |

---

## Research Findings

### Relevance Scoring Best Practices (Q-2)

**Sources**: Allen AI SPECTER2, Semantic Scholar, SciRepEval benchmark

#### Recommended Approach: Multi-Signal Relevance Scoring

1. **Citation-Based Metrics** (from Semantic Scholar):
   - **Citation Velocity**: Weighted average of citations over last 3 years (indicates lasting popularity)
   - **Citation Acceleration**: Change in velocity over time (trending up/down)
   - **Influential Citations**: ML model identifies citations with significant impact on citing paper
   - **h-Index of Authors**: Proxy for author credibility (use cautiously, not for comparison)
   - **Citation Intent**: Categorize as Background, Method, or Result Extension

2. **Embedding-Based Similarity** (SPECTER2 from Allen AI):
   - Use **SPECTER2** for scientific document embeddings (state-of-the-art for papers)
   - 2-step training: citation prediction + multi-task adapters
   - Supports 4 task formats: classification, regression, proximity, ad-hoc search
   - Outperforms OpenAI embeddings on scientific tasks at lower cost
   - Available on HuggingFace: `allenai/specter2`

3. **Composite Relevance Score**:
   ```
   relevance_score = (
       0.3 × citation_velocity_normalized +
       0.2 × author_h_index_normalized +
       0.3 × specter2_similarity_to_target_topics +
       0.2 × recency_weight
   )
   ```

4. **Field-Specific Considerations**:
   - SPECTER2 trained on 23 fields of study (not just CS/BioMed)
   - Use field-specific adapters for better performance
   - BM25 still competitive for some retrieval tasks

#### Implementation Notes
- Use Semantic Scholar API for citation metrics (free, rate-limited)
- Deploy SPECTER2 locally or via HuggingFace Inference API
- Store embeddings in Knowledge Archive (DISC-006) for efficient retrieval

---

### Git Branch Policy for Safe Upgrades (Q-6)

**Sources**: GitHub Engineering Blog, GitHub Docs, Graphite guides

#### Recommended Approach: Feature Flags + Branch Protection

##### 1. Branch Protection Rules (GitHub)

Required protections for `main`/`production` branches:
- **Require pull request before merging**
- **Require approvals** (1-2 reviewers minimum)
- **Dismiss stale approvals** when new commits pushed
- **Require status checks to pass** (CI/CD must succeed)
- **Require branches to be up to date** before merging
- **Require conversation resolution** before merge
- **Require signed commits** (for audit trail)
- **Require linear history** (cleaner rollbacks)
- **Lock branch** for read-only periods
- **Restrict who can push** to matching branches

##### 2. Feature Flag Strategy (GitHub's Approach)

**Why Feature Flags > Long-Lived Branches**:
- Small batches = easier code review
- Smaller changes = lower deployment risk
- Avoid merge conflicts from long-lived branches
- Enable instant rollback (disable flag in seconds vs. minutes for rollback)

**Flag Actor Types**:
- Individual users (for testing/staff)
- Organizations/Teams
- Repositories (for data-changing features)
- GitHub Apps (for API changes)
- Percentage of actors (gradual rollout)
- Dark shipping (per-call, not per-actor, for internal changes)

**Shipping Strategies**:
1. **Staff Shipping**: Enable for all employees first, gather internal feedback
2. **Early Access**: Small beta group tests before wide release
3. **Percentage Rollout**: 1% → 10% → 50% → 100% with monitoring
4. **Dark Shipping**: Test internal changes without user visibility

##### 3. Recommended Upgrade Workflow for AICM

```
[Upgrade Plan Generated]
        │
        ▼
┌───────────────────┐
│ 1. CREATE BRANCH  │  upgrade/PLAN-XXX-feature-name
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 2. APPLY CHANGES  │  AI applies recommended changes
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 3. RUN CI/TESTS   │  Automated validation
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 4. CREATE PR      │  Human review required
│    w/ FEATURE FLAG│  Changes behind flag
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 5. HUMAN APPROVAL │  Code owner review
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 6. MERGE + FLAG   │  Merge disabled, enable gradually
│    GRADUAL ROLLOUT│  Monitor for issues
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 7. CLEANUP        │  Remove flag, delete dead code
└───────────────────┘
```

##### 4. Exclusion Rules Configuration

```yaml
# .aicm/upgrade-policy.yaml
exclusion_rules:
  protected_paths:
    - "src/core/**"           # Never auto-modify core
    - "contracts/**"          # Contracts require manual review
    - "*.lock"                # Dependency locks
  
  protected_patterns:
    - "**/AGENTS.md"          # AI instruction files
    - "**/__init__.py"        # Module exports
  
  skip_upgrades:
    - pattern: "security-*"
      reason: "Security changes require security team review"
    - pattern: "breaking-*"
      reason: "Breaking changes require ADR"

trust_levels:
  level_0:  # New/untrusted
    auto_apply: false
    require_approval: 2
    require_tests: true
  
  level_1:  # Some trust
    auto_apply: ["docs", "comments", "formatting"]
    require_approval: 1
    require_tests: true
  
  level_2:  # High trust
    auto_apply: ["docs", "comments", "formatting", "minor-refactor"]
    require_approval: 1
    require_tests: true
```

##### 5. Rollback Strategy

- **Instant**: Disable feature flag (seconds)
- **Quick**: Revert merge commit (minutes)
- **Full**: Cherry-pick rollback + hotfix branch

---

## Proposed Architecture

### Agent Team Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    RESEARCH ORCHESTRATOR                        │
│              (Coordinator, schedules agents, manages state)     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
     ┌─────────────────────┼─────────────────────┐
     │                     │                     │
     ▼                     ▼                     ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│  DISCOVERY  │    │   ANALYSIS   │    │  RECOMMENDATION │
│    TEAM     │    │     TEAM     │    │      TEAM       │
└─────────────┘    └──────────────┘    └─────────────────┘
     │                     │                     │
     ▼                     ▼                     ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ • Scraper   │    │ • Summarizer │    │ • Trend Tracker │
│ • Deduper   │    │ • Extractor  │    │ • Plan Generator│
│ • Ranker    │    │ • Validator  │    │ • Adapter       │
└─────────────┘    └──────────────┘    └─────────────────┘
```

### Data Flow

```
[Paper Sources] 
       │
       ▼
┌──────────────────┐
│ 1. SCRAPE        │  ← Discovery Agent (daily/weekly cron)
│    (metadata)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. FILTER        │  ← Relevance Agent (cheap LLM: classify)
│    (score 0-100) │
└────────┬─────────┘
         │ (score > threshold)
         ▼
┌──────────────────┐
│ 3. EXTRACT       │  ← PDF Extractor (existing tool)
│    (full text)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 4. ANALYZE       │  ← Analysis Agent (expensive LLM)
│    (insights)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 5. STORE         │  ← Knowledge Archive (RAG system)
│    (embeddings)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 6. RECOMMEND     │  ← Recommendation Agent
│    (suggestions) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 7. PLAN          │  ← Upgrade Plan Generator
│    (artifacts)   │
└──────────────────┘
```

### Upgrade Workflow for Legacy Systems

```
[Target Codebase] ──┐
                    │
                    ▼
           ┌───────────────┐
           │ CODEBASE      │
           │ ANALYZER      │
           │ • Structure   │
           │ • Patterns    │
           │ • Tech Stack  │
           └───────┬───────┘
                   │
                   ▼
           ┌───────────────┐
           │ GAP ANALYSIS  │ ← Compare vs. current best practices
           │ • Missing     │
           │ • Outdated    │
           │ • Conflicts   │
           └───────┬───────┘
                   │
                   ▼
           ┌───────────────┐
           │ EXCLUSION     │ ← Apply user-defined exclusion rules
           │ FILTER        │
           │ • Protected   │
           │ • Skip paths  │
           └───────┬───────┘
                   │
                   ▼
           ┌───────────────┐
           │ ARTIFACT      │ ← Generate DISC → ADR → PLAN chain
           │ GENERATOR     │
           │ • Discussion  │
           │ • Decision    │
           │ • Plan        │
           └───────────────┘
```

---

## Options Considered

### Option A: Fully Autonomous System

**Description**: Agents run continuously, auto-apply recommendations

**Pros**:
- Maximum automation
- Real-time updates

**Cons**:
- Risk of unwanted changes
- Hard to audit
- May conflict with user intent

### Option B: Human-in-the-Loop Advisory System

**Description**: Agents research and recommend; human approves execution

**Pros**:
- Safe and auditable
- User maintains control
- Recommendations are suggestions, not mandates

**Cons**:
- Slower adoption
- Requires user attention

### Option C: Tiered Autonomy

**Description**: Low-risk changes auto-apply; high-risk require approval

**Pros**:
- Balance of speed and safety
- Configurable risk thresholds

**Cons**:
- Complexity in risk classification
- Edge cases may slip through

### Recommendation

**Option B** for initial implementation with a path to **Option C**. Start conservative with human approval gates, then gradually introduce auto-apply for low-risk improvements as trust builds.

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | Paper source priority list | `decided` | Rank by world citation count per topic |
| D-2 | LLM provider for agents | `decided` | xAI Grok (initial) |
| D-3 | Storage format for extracted insights | `pending` | |
| D-4 | Autonomy level for recommendations | `decided` | HITL always, tiered step-down |
| D-5 | Integration approach for legacy codebases | `decided` | Git branch + feature flag policy |

---

## Scope Definition

### In Scope

- Paper scraping from academic sources
- LLM-powered analysis and summarization
- Trend tracking over time
- Recommendation surfacing in AICM UI
- Upgrade plan generation for target codebases
- Exclusion rules configuration
- Integration with existing AICM artifact system

### Out of Scope

- Full-text storage of copyrighted papers
- Auto-execution of upgrade plans (initial version)
- Real-time paper monitoring (batch processing first)
- Multi-language paper support (English only initially)

---

## Cross-DISC Dependencies

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| DISC-006 | `FS` | `resolved` | Storage | Knowledge Archive provides RAG storage |
| DISC-018 | `soft` | `pending` | Self-improvement | Meta-agent patterns inform design |
| DISC-007 | `soft` | `resolved` | LLM calls | Unified xAI wrapper for agent LLM calls |

---

## Resulting Artifacts (Planned)

> **Feature Status**: `planned` - Artifacts documented for future implementation

### ADR: Research Agent Architecture

**ID**: TBD | **Status**: `planned`

**Content**:
- Decision on multi-agent vs. monolithic architecture
- Agent communication patterns (message queue vs. direct calls)
- State management strategy (persistent vs. ephemeral)
- LLM provider abstraction layer (xAI Grok initially, pluggable)
- Error handling and retry policies
- Cost optimization strategies (tiered LLM usage)

---

### SPEC: Agent Communication Protocol

**ID**: TBD | **Status**: `planned`

**Content**:
- Message schema for inter-agent communication
- Event types: `paper_discovered`, `paper_analyzed`, `insight_generated`, `recommendation_ready`
- Orchestrator → Agent command structure
- Progress reporting and status updates
- Failure modes and recovery procedures

---

### Contracts: Research Data Models

**Location**: `contracts/research/` | **Status**: `planned`

**Files to Create**:

1. **`paper.py`** - Paper metadata and content
   - `PaperMetadata`: arxiv_id, doi, title, authors, abstract, publication_date, source
   - `PaperContent`: sections, figures, tables, references
   - `CitationMetrics`: velocity, acceleration, influential_count, h_index_authors

2. **`insight.py`** - Extracted knowledge
   - `Insight`: key_finding, technique, applicability, source_paper_id, confidence
   - `InsightCategory`: enum (architecture, pattern, tool, methodology, metric)
   - `InsightRelation`: links between insights (supports, contradicts, extends)

3. **`recommendation.py`** - Actionable suggestions
   - `Recommendation`: title, description, impact_estimate, effort_estimate, source_insights
   - `RecommendationStatus`: enum (new, reviewed, accepted, rejected, implemented)
   - `UserFeedback`: rating, comments, applied (for learning loop)

4. **`upgrade.py`** - Upgrade plan generation
   - `UpgradePlan`: target_codebase, recommendations, exclusions, artifact_chain
   - `ExclusionRule`: pattern, reason, scope
   - `TrustLevel`: level_0, level_1, level_2 with auto_apply rules

---

### SPEC: Upgrade Policy Schema

**Location**: `.aicm/upgrade-policy.yaml` | **Status**: `planned`

**Content**:
- Protected paths configuration
- Protected patterns (glob-based)
- Skip upgrade conditions
- Trust level definitions
- Approval requirements per level
- Feature flag integration settings

---

### Plan: Research Agent MVP

**ID**: TBD | **Status**: `planned`

**Phases**:

1. **Phase 1: Discovery Agent** (MVP)
   - Semantic Scholar API integration
   - Paper metadata scraping
   - Deduplication logic
   - Basic relevance filtering (keyword-based)

2. **Phase 2: Analysis Pipeline**
   - PDF extraction integration (existing tool)
   - xAI Grok analysis prompts
   - Insight extraction and categorization
   - Knowledge Archive storage

3. **Phase 3: Recommendation Engine**
   - Trend aggregation across papers
   - AICM-specific recommendation generation
   - User feedback loop
   - Conflicting recommendation resolution UI

4. **Phase 4: Upgrade Plan Generator**
   - Codebase analyzer (structure, patterns, tech stack)
   - Gap analysis vs. best practices
   - Exclusion rules engine
   - Artifact chain generation (DISC → ADR → PLAN)
   - Git branch + feature flag integration

---

## Conversation Log

### 2026-01-02 - SESSION_010

**Topics Discussed**:
- Initial vision for automated research paper system
- Multi-agent architecture for discovery, analysis, recommendation
- Upgrade plan generation for legacy systems
- Exclusion rules and safety considerations

**Key Insights**:
- Existing PDF extraction tool provides foundation
- Tiered LLM approach balances cost and quality
- Human-in-the-loop is safest initial approach
- Artifact chain generation enables plug-and-play upgrades

**Action Items**:
- [x] Answer open questions (paper sources, LLM provider)
- [ ] Draft ADR for agent architecture
- [ ] Define contracts for Paper, Insight, Recommendation
- [ ] Prototype Discovery Agent with arXiv API

### 2026-01-02 - SESSION_010 (Update 2)

**Topics Discussed**:
- User answers to all 6 open questions
- Deep research on relevance scoring methods
- Deep research on git branch protection policies

**Key Insights**:
- **SPECTER2** (Allen AI) is state-of-the-art for scientific paper embeddings
- Semantic Scholar provides rich citation metrics (velocity, acceleration, influential citations)
- GitHub's feature flag approach enables instant rollback without deployment
- Branch protection + feature flags = safe automated upgrades
- Trust levels enable gradual autonomy increase

**Research Sources**:
- Allen AI Blog: SPECTER2 paper embeddings
- Semantic Scholar FAQ: Citation metrics explained
- GitHub Engineering Blog: Feature flag strategies
- GitHub Docs: Branch protection rules
- Graphite: Git branching strategies comparison

**Action Items**:
- [ ] Draft ADR for agent architecture
- [ ] Define contracts for Paper, Insight, Recommendation
- [ ] Prototype Discovery Agent with Semantic Scholar API
- [ ] Design exclusion rules schema
- [ ] Implement feature flag integration for upgrade workflow

---

### 2026-01-02 - SESSION_012

**Topics Discussed**:
- Research database systematic failures investigation
- First-principles approach to PDF extraction
- Production-quality database implementation

**Issues Fixed**:
- `extract_paper()` required output_dir - was passing `None`
- `full_text_preview` truncated to 5003 chars - now stores full text (~88K avg)
- FTS triggers had wrong schema - recreated with correct columns
- UNIQUE constraints on `arxiv_id`/`doi` blocking non-arXiv papers - removed
- Embedding generation bottleneck - added `--skip-embeddings` flag

**New Scripts Created**:
- `scripts/research_db_production.py` - First-principles production extractor with `RobustPDFExtractor` class
- `scripts/quick_ingest.py` - Minimal reliable ingestion bypassing complex dependencies
- `scripts/research_db_upgrade.py` - Database migration and upgrade script

**Final Database State**:
- 68 papers (100% of source folder)
- 100% with full text
- 100% with abstracts
- 94% with arXiv IDs (non-arXiv papers don't have IDs)
- 7,261 chunks for RAG
- FTS search fully operational

**Key Insight**:
First-principles approach was essential - instead of patching the complex sync system with multiple dependencies (langchain, watchdog, etc.), created minimal working solution that directly uses PyMuPDF and SQLite.

---

## Quality Score

**Status**: `[ACTIVE]` - Research DB production-ready, agent system ready for implementation

---

*Template version: 2.0.0 | Per ADR-0048 (Unified Artifact Model)*
