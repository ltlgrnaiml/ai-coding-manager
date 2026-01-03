# SESSION_015: GPU-Accelerated RAG & Cross-Platform Workflow

**Date**: 2026-01-03
**Status**: complete
**Related DISCs**: DISC-028, DISC-029

## Objectives

1. Create discussion on GPU-accelerated RAG containerization patterns
2. Create strategy for cross-platform development (Mac native ↔ Win11 Docker)

## Deliverables

### DISC-028: GPU-Accelerated RAG Containerization
- 4 common RAG deployment patterns documented
- Hardware profile for Win11 (5090 + 3090 Ti) and Mac (M4 Max)
- Phased rollout recommendation (Qdrant → GPU → Local LLM)
- Performance comparison tables

### DISC-029: Cross-Platform Development Workflow
- Machine switch protocol (switch_out.sh / switch_in.sh)
- Environment detection system (detect_env.py)
- Platform-aware Makefile
- AI assistant context injection strategy

### Scripts Created
- `scripts/detect_env.py` - Environment detection
- `scripts/switch_out.sh` - Before leaving machine
- `scripts/switch_in.sh` - After arriving at machine
- `scripts/switch_out.ps1` - Windows PowerShell version
- `Makefile` - Platform-aware commands

## Key Decisions

| Topic | Decision |
|-------|----------|
| GPU containers | Not needed now; add Qdrant when >500 research papers |
| Machine sync | Git-based with switch scripts + CURRENT_MACHINE.md |
| Environment detection | Python script used by code and AI assistants |
| Mac execution | Native Python (no Docker for dev) |
| Win11 execution | Docker + WSL2 (existing setup) |

## Handoff Notes

- Run `make help` to see all available commands
- Before leaving Mac: `make switch-out` or `./scripts/switch_out.sh`
- After arriving Win11: `git pull && ./scripts/switch_in.sh`
- AI assistants should run `python scripts/detect_env.py` first

## 2026-01-03 Updates (continued)

### Mac Native Dev Environment Setup

**Issues Found:**
- venv was missing backend dependencies (fastapi, uvicorn, etc.)
- `make dev` only started backend, not frontend or Phoenix

**Fixes Applied:**
1. Installed backend deps: `uv pip install -r backend/requirements.txt`
2. Installed pytest: `uv pip install pytest pytest-asyncio`
3. Installed Phoenix: `uv pip install arize-phoenix`
4. Created `scripts/dev_mac.sh` - starts all 3 services in parallel
5. Updated Makefile:
   - `make dev` now starts ALL services
   - Added `make dev-backend`, `make dev-frontend`, `make dev-phoenix`
6. Updated README.md with new commands

**Result:**
- 48 tests passing
- Mac and Win11 have identical dev experience on ports 8100, 3100, 6006
- `make dev` works the same on both platforms
