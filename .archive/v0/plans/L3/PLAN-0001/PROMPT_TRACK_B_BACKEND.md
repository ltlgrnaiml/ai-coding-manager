# PLAN-0001 Track B: Backend Migration

> **Assistant Assignment**: Execute CHUNK-B1 and CHUNK-B2 sequentially
> **Parallel Track**: Track A (Frontend) is running simultaneously - DO NOT touch frontend/ files

## Your Mission

Modify the copied backend files from engineering-tools to work in the AICM project structure. Files have been bulk-copied - you need to fix imports and mount the API routers.

---

## CHUNK-B1: Backend Services (Execute First)

### Files to Modify
1. `backend/services/__init__.py` (create if missing)
2. `backend/services/devtools_service.py`
3. `backend/services/workflow_service.py`
4. `backend/services/llm_service.py`
5. `backend/main.py`

### Tasks

#### B1-01: Create backend/services/__init__.py
```bash
test -f backend/services/__init__.py && echo 'exists' || echo 'missing'
```
If missing, create with:
```python
# Backend services
```

#### B1-02: Fix devtools_service.py imports

Find and replace these patterns throughout the file:

| Find | Replace With |
|------|--------------|
| `from shared.contracts.devtools` | `from contracts.devtools` |
| `from shared.contracts` | `from contracts` |
| `from gateway.services` | `from backend.services` |
| `from services.knowledge` | `from backend.services.knowledge` |

Verification:
```bash
grep -n 'from shared' backend/services/devtools_service.py | wc -l  # Should be 0
grep -n 'from gateway' backend/services/devtools_service.py | wc -l  # Should be 0
```

#### B1-03: Fix workflow_service.py imports

Same pattern replacements:
| Find | Replace With |
|------|--------------|
| `from shared.contracts` | `from contracts` |
| `from gateway.services` | `from backend.services` |

#### B1-04: Fix llm_service.py imports

Same pattern replacements as above.

#### B1-05: Update backend/main.py

Add the devtools router. The file should include:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.services.devtools_service import router as devtools_router

app = FastAPI(title="AI Coding Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devtools_router, prefix="/api/devtools", tags=["devtools"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### CHUNK-B1 Verification
```bash
cd /home/mycahya/coding/ai-coding-manager
python -c "from backend.services.devtools_service import router; print('DevTools OK')"
python -c "from backend.main import app; print('Main OK')"
```

---

## CHUNK-B2: Knowledge/RAG + Contracts (Execute After B1)

### Files to Modify
1. `backend/services/knowledge/__init__.py`
2. `backend/services/knowledge/*.py` (all files)
3. `contracts/devtools/__init__.py`
4. `contracts/devtools/api.py`
5. `contracts/devtools/workflow.py`

### Tasks

#### B2-01: Verify/Update knowledge/__init__.py
```bash
cat backend/services/knowledge/__init__.py
```
Ensure it exports key components or at minimum exists.

#### B2-02: Batch Fix All Knowledge Service Imports

Apply to ALL files in `backend/services/knowledge/`:

| Find | Replace With |
|------|--------------|
| `from shared.contracts` | `from contracts` |
| `from gateway.services` | `from backend.services` |

Files to check:
- `database.py`
- `embedding_service.py`
- `search_service.py`
- `context_builder.py`
- `chunking.py`
- `parsers.py`
- `sanitizer.py`
- `enhanced_rag.py`
- `archive_service.py`
- `sync_service.py`

Verification:
```bash
grep -r 'from shared' backend/services/knowledge/ | wc -l  # Should be 0
grep -r 'from gateway' backend/services/knowledge/ | wc -l  # Should be 0
```

#### B2-03: Verify/Create contracts/devtools/__init__.py
```bash
test -f contracts/devtools/__init__.py && cat contracts/devtools/__init__.py
```
Should export from api.py and workflow.py.

#### B2-04: Fix contracts/devtools/api.py
Check for any internal imports that need fixing. These are usually standalone Pydantic models.

#### B2-05: Fix contracts/devtools/workflow.py
Same verification - check for broken imports.

### CHUNK-B2 Verification
```bash
cd /home/mycahya/coding/ai-coding-manager
python -c "from contracts.devtools import *; print('Contracts OK')"
python -c "from backend.services.knowledge.database import *; print('DB OK')"
python -c "from backend.services.knowledge.search_service import *; print('Search OK')"
python -c "from backend.main import app; print('Full App OK')"
```

---

## Final Track B Verification

After both chunks complete:
```bash
cd /home/mycahya/coding/ai-coding-manager
python -c "from backend.main import app; print('Backend fully importable')"
pytest tests/ -v  # Run existing tests
```

If all imports resolve and tests pass, Track B is complete. Report success and any warnings to the coordinator.

---

## Critical Rules

1. **DO NOT TOUCH** any files in `frontend/` - Track A handles those
2. **Preserve all functionality** - only change import paths, not logic
3. **Every file must be modified** - if a file has no bad imports, add a comment or verify it's correct
4. **No guessing** - read files before modifying, verify after each change
5. **Watch for circular imports** - if you hit import errors, check dependency order
6. **Commit after success**: `git add backend/ contracts/ && git commit -m "PLAN-0001 Track-B: Backend migration complete"`
