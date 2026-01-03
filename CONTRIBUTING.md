# Contributing to AI Coding Manager

> Solo-dev project with AI-assisted development. These guidelines help AI assistants work effectively.

---

## Before You Start

1. **Run environment detection:**
   ```bash
   python scripts/detect_env.py
   ```

2. **Check recent sessions:**
   ```bash
   ls -la .sessions/
   ```

3. **Read the rules:**
   - [`AGENTS.md`](AGENTS.md) - Required reading for AI assistants

---

## Development Workflow

### Starting Work

```bash
# If arriving from another machine
git pull && make switch-in

# Check environment
make env

# Run tests to verify clean state
make test
```

### During Work

- Keep changes small and focused
- Commit frequently with descriptive messages
- Run `make test` after significant changes

### Finishing Work

```bash
# Before leaving machine
make switch-out
```

This commits, pushes, and updates `.sessions/CURRENT_MACHINE.md`.

---

## Platform Differences

| Platform | Execution | GPU | Commands |
|----------|-----------|-----|----------|
| Mac | Native Python | MPS (Metal) | `make dev` |
| Win11 | Docker + WSL2 | CUDA | `docker compose up` |

**Always use `make` commands** - they auto-detect platform and run the right thing.

---

## Session Management

Every AI session should:

1. **Claim a session number:**
   - Check `.sessions/` for highest `SESSION_XXX`
   - Create `SESSION_XXX+1_description.md`

2. **Document progress:**
   - What was done
   - What remains
   - Any blockers

3. **Update before finishing:**
   - Session file with handoff notes
   - `make switch-out` if leaving machine

---

## Code Standards

- **Python:** Type hints on all functions, Google-style docstrings
- **TypeScript:** Typed props, no `any` types
- **Tests:** Required for new functionality
- **Imports:** Always at top of file

---

## Directory Guide

| Directory | Purpose |
|-----------|---------|
| `backend/` | FastAPI backend services |
| `frontend/` | React + Vite UI |
| `contracts/` | Pydantic schemas (SSOT) |
| `scripts/` | Automation tools |
| `.adrs/` | Architecture Decision Records |
| `.discussions/` | Design conversations |
| `.plans/` | Execution plans |
| `.sessions/` | AI session logs |

---

## Running Tests

```bash
# Platform-aware (recommended)
make test

# Mac native
pytest tests/ -v

# Win11 Docker
docker exec aidev-backend pytest tests/ -v
```

---

## Docker Commands (Win11)

```bash
# Start services
docker compose --profile main up -d

# Rebuild after changes
docker compose --profile main build
docker compose --profile main up -d

# View logs
docker logs -f aidev-backend

# Shell into container
docker exec -it aidev-backend /bin/bash
```

---

## Questions?

Create a file in `.questions/` with your question. The next human or AI session will address it.
