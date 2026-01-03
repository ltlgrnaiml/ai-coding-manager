# PLAN-0002: AIKH Integration Sprint - Test Suite

## Phase 1 Tests (Backend)

```bash
# T1: Context enrichment endpoint
curl -s localhost:8001/api/aikh/enrich -X POST \
  -H 'Content-Type: application/json' \
  -d '{"message":"context compression for LLMs"}' | python -m json.tool

# T2: Autocomplete endpoint
curl -s "localhost:8001/api/aikh/autocomplete?prefix=trans&type=concept"

# T3: Cross-reference tables
sqlite3 .workspace/research_papers.db '.tables' | grep -E 'artifact_knowledge|knowledge_annotations'

# T4: BibTeX generation
curl -s localhost:8001/api/aikh/papers/{paper_id}/bibtex
```

## Phase 2 Tests (Frontend)

```bash
# T1: Components exist
ls frontend/src/components/research/

# T2: Hook exists
cat frontend/src/hooks/useResearch.ts

# T3: Build succeeds
cd frontend && npm run build
```

## Phase 3 Tests (Integration)

```bash
# T1: Autocomplete in ChatInput
grep '@paper:' frontend/src/components/ChatInput.tsx

# T2: Keyboard shortcuts
grep 'useKeyboardShortcuts' frontend/src/App.tsx

# T3: Full integration test
cd frontend && npm run dev
# Manual: Type @paper: in chat, verify suggestions appear
```

## Global Tests

```bash
# Backend loads
.venv/bin/python -c 'from backend.services.research_api import app; print("✅ Backend OK")'

# Frontend builds
cd frontend && npm run build && echo "✅ Frontend OK"
```
