# Archive v0 — Pre-Genesis Artifacts

> **Archived**: 2026-01-03  
> **Reason**: Foundation reset to establish clear AICM vision

---

## What's Here

This archive contains all DISCs, ADRs, PLANs, contracts, and documentation created BEFORE the Genesis vision statement (`VISION.md`).

These artifacts represent valuable exploration work but were created without a clear answer to:

1. **What IS the AICM product?**
2. **How does it use UAM, AIKH, P2RE?**
3. **Why is it special?**
4. **What makes a project AICM-compatible?**

---

## Contents

| Folder | Description | Count |
|--------|-------------|-------|
| `discussions/` | DISC documents exploring various topics | ~40 |
| `adrs/` | Architecture Decision Records | ~10 |
| `plans/` | Execution plans | ~5 |
| `contracts/` | Pydantic schemas | ~10 |
| `docs/` | Documentation files | ~6 |
| `experiments/` | Experimental work | ~1 |
| `sync_todos/` | Sync tracking | ~2 |

---

## What Was Preserved (Not Archived)

- **`.chat_logs/`** — Raw conversation history (the source of truth)
- **`.sessions/`** — AI session continuity logs

---

## Retrieval

These artifacts may be referenced or restored if needed:

```bash
# View archived discussions
ls .archive/v0/discussions/

# Restore a specific file
cp .archive/v0/discussions/DISC-011_Unified-Artifact-Model.md .discussions/
```

---

## Going Forward

All new artifacts will be created with the Genesis vision as foundation:

1. Chat logs → Discussions
2. Discussions → Decisions  
3. Decisions → Specifications
4. Specifications → Code
5. Code → Traces
6. Traces → Knowledge → Next Chat

The loop is now closed.
