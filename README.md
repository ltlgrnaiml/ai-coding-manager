# AI Coding Manager (AICM)

> **A proof-of-concept framework for AI-assisted development with cross-platform workflow, RAG, and observability.**

[![Status](https://img.shields.io/badge/status-POC-yellow)]()
[![Platform](https://img.shields.io/badge/platform-Mac%20%7C%20Win11%20Docker-blue)]()

---

## 🚀 Quick Start: Cross-Platform Workflow

**This project is developed across two machines.** Use these commands for seamless switching:

### Machine Switch Protocol

```bash
# BEFORE leaving any machine
make switch-out          # Commits, pushes, updates state

# AFTER arriving at new machine  
git pull && make switch-in   # Pulls, shows env, ready to work
```

### Platform-Aware Commands

| Command | Mac (Native) | Win11 (Docker) |
|---------|--------------|----------------|
| `make dev` | Starts backend + frontend + Phoenix | `docker compose up` |
| `make dev-backend` | Backend only (port 8100) | Backend container only |
| `make dev-frontend` | Frontend only (port 3100) | Frontend container only |
| `make dev-phoenix` | Phoenix only (port 6006) | Phoenix container only |
| `make test` | `pytest` native | `pytest` in container |

### Environment Detection

```bash
python scripts/detect_env.py
```

AI assistants should run this first to understand the execution context.

---

## 🖥️ Hardware Profile

| Machine | Purpose | GPU | Execution |
|---------|---------|-----|-----------|
| **MacBook Pro M4 Max** | Mobile dev (couch) | MPS (Metal) | Native Python |
| **Win11 Desktop** | Heavy GPU work | RTX 5090 + 3090 Ti | Docker + WSL2 |

---

## 📦 Docker Deployment (Win11)

```bash
# Start all services
docker compose --profile main up -d

# View logs
docker logs -f aidev-backend

# Rebuild after code changes
docker compose --profile main build && docker compose --profile main up -d
```

**Ports:**
- `8100` - Backend API
- `3100` - Frontend UI  
- `6006` - Phoenix Observability

---

## What is AICM?

AI Coding Manager helps you get **consistent, high-quality code** from AI assistants:

- **🤖 Multi-LLM Support** - xAI, Anthropic, Google via unified adapter
- **📚 RAG System** - SQLite + hybrid search (FTS + vector embeddings)
- **👁️ Phoenix Observability** - OpenTelemetry tracing for all LLM calls
- **📋 Plan Granularity** - L1/L2/L3 plans match detail to model capability
- **🔄 6-Tier Workflow** - Discussion → ADR → SPEC → Contract → Plan → Fragment
- **📝 Session Continuity** - Handoff context between AI sessions

---

## 📁 Project Structure

```text
ai-coding-manager/
├── backend/              # FastAPI backend
│   ├── services/         # Business logic
│   │   ├── knowledge/    # RAG, embeddings, retrieval
│   │   └── llm/          # Multi-provider LLM adapter
│   └── main.py           # API entrypoint
│
├── frontend/             # React + Vite frontend
│   └── src/
│       ├── components/   # UI components
│       └── views/        # Page views
│
├── contracts/            # Pydantic schemas (SSOT)
├── scripts/              # Automation & workflow tools
│   ├── detect_env.py     # Environment detection
│   ├── switch_out.sh     # Machine switch protocol
│   └── switch_in.sh      # Machine arrival protocol
│
├── docker/               # Dockerfiles
├── .adrs/                # Architecture Decision Records
├── .discussions/         # Design conversations
├── .plans/               # Execution plans (L1/L2/L3)
├── .sessions/            # AI session continuity logs
└── .research_papers/     # PDFs for RAG ingestion
```

---

## 🤖 For AI Assistants

**Read these first:**

1. [`AGENTS.md`](AGENTS.md) - Global rules for AI coding assistants
2. [`python scripts/detect_env.py`](scripts/detect_env.py) - Run to understand execution context
3. [`.sessions/`](.sessions/) - Check recent session logs for context

**Key Rules:**

- Create a session file in `.sessions/SESSION_XXX_description.md`
- Run `make test` before and after changes
- Use `make switch-out` before finishing work

---

## 📚 Core Documentation

| Document | Purpose |
|----------|---------|
| [`AGENTS.md`](AGENTS.md) | AI assistant rules |
| [`docs/CONCURRENT_DEVELOPMENT_POLICY.md`](docs/CONCURRENT_DEVELOPMENT_POLICY.md) | Cross-platform sync |
| [`.discussions/DISC-029_Cross-Platform-Dev-Workflow-Strategy.md`](.discussions/DISC-029_Cross-Platform-Dev-Workflow-Strategy.md) | Full workflow strategy |
| [`.discussions/DISC-028_GPU-Accelerated-RAG-Containerization.md`](.discussions/DISC-028_GPU-Accelerated-RAG-Containerization.md) | GPU architecture |

---

## 🧪 Running Tests

```bash
# Mac (native)
pytest tests/ -v

# Win11 (Docker)
docker exec aidev-backend pytest tests/ -v

# Or use platform-aware make
make test
```

---

## 🔧 Development Setup

### Mac (Native Python)

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start dev server
make dev
# or: python -m uvicorn backend.main:app --reload --port 8100
```

### Win11 (Docker)

```bash
# Build and start
docker compose --profile main up -d

# View logs
docker logs -f aidev-backend
```

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

*Built with AI, for AI-assisted development*
