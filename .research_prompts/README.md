# Research Prompts for AICM Vision Refinement

> **Created**: SESSION_009 | 2026-01-02
> **Purpose**: Targeted research acquisition to fill vision gaps

---

## Overview

These prompt files contain search queries and topic guides for acquiring research papers to strengthen weak areas in the AICM vision.

---

## Prompt Files by Priority

| File | Priority | Addresses | Target Papers |
|------|----------|-----------|---------------|
| `01_CONTEXT_MEMORY_MANAGEMENT.md` | P1 (HIGH) | W1: Tap-In Protocol | 10-15 |
| `02_AGENTIC_AI_ARCHITECTURES.md` | P2 (HIGH) | W2: AI Chat, W4: Pipelines | 12-18 |
| `05_CODE_GENERATION_VALIDATION.md` | P3 (HIGH) | W4: Artifact Generation | 10-14 |
| `03_LLM_EVALUATION_QUALITY.md` | P4 (MED) | W3: Quality Scoring | 8-12 |
| `04_AI_OBSERVABILITY_TRACING.md` | P5 (MED) | W5: Observability | 8-10 |
| `06_DEVELOPER_TOOL_UX.md` | P7 (MED) | W8: UI/UX Design | 6-10 |

**Total Target**: ~55-80 papers across all categories

---

## Workflow

### Step 1: Search

Use the queries in each prompt file to search:

- **arXiv** - cs.CL, cs.SE, cs.AI, cs.LG
- **Semantic Scholar** - Research paper search
- **Google Scholar** - Broad academic search
- **ACL Anthology** - NLP/CL papers
- **Conference proceedings** - ICSE, FSE, NeurIPS, etc.

### Step 2: Download PDFs

Collect PDFs to a staging folder (e.g., `~/Downloads/research/`)

### Step 3: Extract

```bash
# By category
python scripts/extract_pdf_papers.py --batch context-memory ~/Downloads/research/context/*.pdf
python scripts/extract_pdf_papers.py --batch agentic-systems ~/Downloads/research/agents/*.pdf
# etc.
```

### Step 4: Ingest

```bash
python scripts/research_paper_cli.py ingest extracted_papers/research/*_extraction.json --category <category>
```

### Step 5: Search & Synthesize

```bash
# Search across all papers
python scripts/research_paper_cli.py search "your topic" --method hybrid

# Get RAG context for vision update
python scripts/research_paper_cli.py show <paper_id>
```

---

## After Research Acquisition

1. **Re-read** the vision analysis: `docs/AICM_VISION_ANALYSIS.md`
2. **Update** weak areas with research-backed decisions
3. **Create Revision 2** of the AICM vision
4. **Iterate** until all areas reach 7+/10 score

---

## Current Research State

**Existing Papers**: ~24 in `extracted_papers/research/`

**Categories Already Present** (partial):

- Agentic AI systems
- RAG/Retrieval systems
- Multimodal learning
- Graph neural networks

**Categories Needing More**:

- Context/memory management (P1)
- Code generation validation (P3)
- LLM evaluation (P4)
- AI observability (P5)
- Developer tool UX (P7)

---

## Related Documents

- `docs/AICM_VISION_ANALYSIS.md` - Strengths/weaknesses analysis
- `docs/RESEARCH_INFRASTRUCTURE_REFERENCE.md` - How to use the research system
- `docs/RESEARCH_PAPER_RAG.md` - Detailed RAG documentation
