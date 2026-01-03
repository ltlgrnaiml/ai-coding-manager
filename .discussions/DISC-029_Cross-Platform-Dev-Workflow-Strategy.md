# DISC-029: Cross-Platform Development Workflow Strategy

> **Status**: `active`
> **Created**: 2026-01-03
> **Updated**: 2026-01-03
> **Author**: AI-Assisted
> **AI Session**: SESSION_015
> **Depends On**: DISC-028
> **Blocks**: None
> **Dependency Level**: L0

---

## Summary

A deterministic, robust strategy for developing the same codebase across two environments:
- **MacBook Pro M4 Max** (couch/upstairs) - Native Python execution
- **Win11 Desktop** (desk/downstairs) - Docker/WSL2 execution

Addresses: git sync, environment detection, AI assistant context, testing parity.

---

## Context

### Background

User workflow:
1. Code on MacBook upstairs (couch) using native Python
2. Push changes
3. Walk downstairs to Win11 desktop with better GPU + monitors
4. Pull changes, continue working on same files
5. Run in Docker on Win11

**Pain Points:**
- Forgetting to push/pull before switching
- AI assistants confused about which environment they're in
- Docker vs native execution differences
- Testing works on one platform, fails on other

### Existing Policy

`docs/CONCURRENT_DEVELOPMENT_POLICY.md` covers basics but lacks:
- Environment auto-detection for AI assistants
- Pre-switch validation scripts
- Native ↔ Docker parity testing
- AI context injection for platform awareness

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: One-command sync before leaving any machine
- [ ] **FR-2**: Environment auto-detection in code and for AI assistants
- [ ] **FR-3**: Tests must pass on BOTH native (Mac) and Docker (Win11)
- [ ] **FR-4**: AI assistants must know which platform they're operating on
- [ ] **FR-5**: Clear handoff notes between machines

### Non-Functional Requirements

- [ ] **NFR-1**: Sync command must complete in <30 seconds
- [ ] **NFR-2**: Zero data loss during machine switches

---

## The Strategy

### 1. Environment Detection System

Create `scripts/detect_env.py` that every script and AI session uses:

```python
#!/usr/bin/env python3
"""Environment detection for cross-platform development."""

import os
import platform
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Platform(Enum):
    MAC_NATIVE = "mac-native"
    WIN_DOCKER = "win-docker"
    WIN_WSL = "win-wsl"
    LINUX_NATIVE = "linux-native"
    DOCKER = "docker"
    UNKNOWN = "unknown"


class GPUBackend(Enum):
    CUDA = "cuda"
    MPS = "mps"
    CPU = "cpu"


@dataclass
class Environment:
    platform: Platform
    gpu_backend: GPUBackend
    in_docker: bool
    workspace_root: Path
    hostname: str
    
    def summary(self) -> str:
        return f"[{self.platform.value}] GPU:{self.gpu_backend.value} Docker:{self.in_docker}"


def detect_environment() -> Environment:
    """Detect current execution environment."""
    
    # Check if running in Docker
    in_docker = (
        os.path.exists("/.dockerenv") or
        os.environ.get("WORKSPACE_ROOT") == "/workspace"
    )
    
    # Detect platform
    system = platform.system()
    hostname = platform.node()
    
    if in_docker:
        plat = Platform.DOCKER
    elif system == "Darwin":
        plat = Platform.MAC_NATIVE
    elif system == "Linux":
        # Check if WSL
        if "microsoft" in platform.release().lower():
            plat = Platform.WIN_WSL
        else:
            plat = Platform.LINUX_NATIVE
    elif system == "Windows":
        plat = Platform.WIN_DOCKER  # Assume Docker context
    else:
        plat = Platform.UNKNOWN
    
    # Detect GPU backend
    gpu = GPUBackend.CPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu = GPUBackend.CUDA
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            gpu = GPUBackend.MPS
    except ImportError:
        pass
    
    # Workspace root
    workspace = Path(os.environ.get("WORKSPACE_ROOT", Path.cwd()))
    
    return Environment(
        platform=plat,
        gpu_backend=gpu,
        in_docker=in_docker,
        workspace_root=workspace,
        hostname=hostname,
    )


# Singleton for caching
_cached_env: Environment | None = None

def get_env() -> Environment:
    global _cached_env
    if _cached_env is None:
        _cached_env = detect_environment()
    return _cached_env


if __name__ == "__main__":
    env = detect_environment()
    print(f"Platform:   {env.platform.value}")
    print(f"GPU:        {env.gpu_backend.value}")
    print(f"In Docker:  {env.in_docker}")
    print(f"Workspace:  {env.workspace_root}")
    print(f"Hostname:   {env.hostname}")
```

---

### 2. Machine Switch Protocol

#### Before Leaving ANY Machine

Create `scripts/switch_out.sh` (Mac) and `scripts/switch_out.ps1` (Windows):

**Mac Version (`switch_out.sh`):**
```bash
#!/bin/bash
set -e

echo "🔄 AICM Machine Switch-Out Protocol"
echo "===================================="

# 1. Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo "📝 Uncommitted changes detected:"
    git status --short
    
    read -p "Commit all changes? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        git add -A
        read -p "Commit message: " msg
        git commit -m "${msg:-WIP: switching machines}"
    else
        echo "❌ Aborting - commit your changes first"
        exit 1
    fi
fi

# 2. Push to remote
echo "⬆️  Pushing to origin..."
git push origin $(git branch --show-current)

# 3. Run tests (optional but recommended)
read -p "Run tests before switch? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 Running tests..."
    python -m pytest tests/ -v --tb=short
fi

# 4. Update session file
SESSION_FILE=".sessions/CURRENT_MACHINE.md"
cat > "$SESSION_FILE" << EOF
# Current Machine State

**Last Active**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Machine**: $(hostname)
**Branch**: $(git branch --show-current)
**Commit**: $(git rev-parse --short HEAD)
**Status**: Switched out - ready for other machine

## Notes
$(git log -1 --pretty=format:"%s")
EOF

git add "$SESSION_FILE"
git commit -m "chore: machine switch-out from $(hostname)"
git push

echo ""
echo "✅ Ready to switch! Run on other machine:"
echo "   git pull && ./scripts/switch_in.sh"
```

**Windows Version (`switch_out.ps1`):**
```powershell
Write-Host "🔄 AICM Machine Switch-Out Protocol" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# 1. Check for uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "📝 Uncommitted changes detected:" -ForegroundColor Yellow
    git status --short
    
    $commit = Read-Host "Commit all changes? [Y/n]"
    if ($commit -ne 'n') {
        git add -A
        $msg = Read-Host "Commit message"
        if (-not $msg) { $msg = "WIP: switching machines" }
        git commit -m $msg
    } else {
        Write-Host "❌ Aborting - commit your changes first" -ForegroundColor Red
        exit 1
    }
}

# 2. Push to remote
Write-Host "⬆️  Pushing to origin..." -ForegroundColor Green
git push origin (git branch --show-current)

# 3. Update session file
$sessionFile = ".sessions/CURRENT_MACHINE.md"
$content = @"
# Current Machine State

**Last Active**: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
**Machine**: $env:COMPUTERNAME
**Branch**: $(git branch --show-current)
**Commit**: $(git rev-parse --short HEAD)
**Status**: Switched out - ready for other machine

## Notes
$(git log -1 --pretty=format:"%s")
"@
Set-Content -Path $sessionFile -Value $content

git add $sessionFile
git commit -m "chore: machine switch-out from $env:COMPUTERNAME"
git push

Write-Host ""
Write-Host "✅ Ready to switch! Run on other machine:" -ForegroundColor Green
Write-Host "   git pull && ./scripts/switch_in.sh" -ForegroundColor White
```

#### Arriving at New Machine

Create `scripts/switch_in.sh`:

```bash
#!/bin/bash
set -e

echo "🔄 AICM Machine Switch-In Protocol"
echo "==================================="

# 1. Pull latest
echo "⬇️  Pulling latest changes..."
git fetch origin
git pull origin $(git branch --show-current)

# 2. Show what changed
echo ""
echo "📋 Recent changes:"
git log --oneline -5

# 3. Check environment
echo ""
echo "🖥️  Environment Detection:"
python scripts/detect_env.py

# 4. Platform-specific setup
if [[ "$(uname)" == "Darwin" ]]; then
    echo ""
    echo "🍎 Mac Native Mode"
    echo "   - Running without Docker"
    echo "   - GPU: MPS (Metal)"
    echo ""
    echo "Start dev server: python -m uvicorn backend.main:app --reload --port 8100"
else
    echo ""
    echo "🪟 Windows/WSL Docker Mode"
    echo "   - Running with Docker"
    echo "   - GPU: CUDA"
    echo ""
    echo "Start containers: docker compose --profile main up -d"
fi

# 5. Update session file
SESSION_FILE=".sessions/CURRENT_MACHINE.md"
cat > "$SESSION_FILE" << EOF
# Current Machine State

**Last Active**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Machine**: $(hostname)
**Branch**: $(git branch --show-current)
**Commit**: $(git rev-parse --short HEAD)
**Status**: Active development

## Environment
$(python scripts/detect_env.py 2>/dev/null || echo "Detection script not found")
EOF

echo ""
echo "✅ Ready to work!"
```

---

### 3. AI Assistant Context Injection

Add to `AGENTS.md` or create `.ai-context.md` in repo root:

```markdown
# AI Context: Cross-Platform Development

## Environment Detection

Before executing ANY command, detect the current environment:

```bash
python scripts/detect_env.py
```

## Platform-Specific Commands

| Action | Mac Native | Win11 Docker |
|--------|------------|--------------|
| **Start backend** | `uvicorn backend.main:app --reload --port 8100` | `docker compose --profile main up -d` |
| **Run tests** | `pytest tests/ -v` | `docker exec aidev-backend pytest tests/ -v` |
| **Install deps** | `pip install -r requirements.txt` | `docker compose build aidev-backend` |
| **View logs** | Terminal output | `docker logs -f aidev-backend` |
| **GPU check** | `python -c "import torch; print(torch.backends.mps.is_available())"` | `docker exec aidev-backend python -c "import torch; print(torch.cuda.is_available())"` |

## Before Making Changes

1. Check `git status` - ensure clean or committed
2. Check `.sessions/CURRENT_MACHINE.md` - see last machine state
3. Run `python scripts/detect_env.py` - confirm environment

## Key Differences

### Mac Native
- No Docker overhead
- Direct filesystem access
- MPS (Metal) for GPU
- Faster iteration
- Run: `python -m uvicorn ...`

### Win11 Docker
- Containers isolate environment
- CUDA for GPU (5090 + 3090 Ti)
- Rebuild required for dep changes
- Run: `docker compose up`

## Testing Parity

Tests MUST pass on both:
```bash
# Mac
pytest tests/ -v

# Win11 Docker
docker exec aidev-backend pytest tests/ -v
```

If a test uses GPU, mark it:
```python
@pytest.mark.gpu
def test_embedding_generation():
    ...
```

Run GPU tests only on appropriate platform.
```

---

### 4. Makefile for Unified Commands

Create `Makefile` that works on both platforms:

```makefile
.PHONY: help dev test switch-out switch-in env docker-up docker-down

# Detect OS
UNAME := $(shell uname)
ifeq ($(UNAME), Darwin)
    PLATFORM := mac
else
    PLATFORM := docker
endif

help:
	@echo "AICM Development Commands"
	@echo "========================="
	@echo "  make dev         - Start development server (platform-aware)"
	@echo "  make test        - Run tests (platform-aware)"
	@echo "  make switch-out  - Prepare to switch machines"
	@echo "  make switch-in   - Arriving at new machine"
	@echo "  make env         - Show current environment"
	@echo ""
	@echo "Current platform: $(PLATFORM)"

env:
	@python scripts/detect_env.py

dev:
ifeq ($(PLATFORM), mac)
	@echo "🍎 Starting Mac Native dev server..."
	python -m uvicorn backend.main:app --reload --port 8100
else
	@echo "🪟 Starting Docker containers..."
	docker compose --profile main up
endif

test:
ifeq ($(PLATFORM), mac)
	@echo "🍎 Running tests natively..."
	python -m pytest tests/ -v --tb=short
else
	@echo "🪟 Running tests in Docker..."
	docker exec aidev-backend pytest tests/ -v --tb=short
endif

switch-out:
	@./scripts/switch_out.sh

switch-in:
	@git pull
	@./scripts/switch_in.sh

docker-up:
	docker compose --profile main up -d

docker-down:
	docker compose --profile main down
```

---

### 5. Pre-Commit Hook for Consistency

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Ensure tests pass before commit
echo "🧪 Running pre-commit tests..."

# Detect platform and run appropriate tests
if [[ "$(uname)" == "Darwin" ]]; then
    python -m pytest tests/ -v --tb=short -q
else
    # Check if Docker is running
    if docker ps | grep -q aidev-backend; then
        docker exec aidev-backend pytest tests/ -v --tb=short -q
    else
        echo "⚠️  Docker not running, skipping tests"
    fi
fi

# Check for platform-specific code without guards
echo "🔍 Checking for unguarded platform code..."
if grep -r "torch.cuda" backend/ --include="*.py" | grep -v "is_available"; then
    echo "⚠️  Found unguarded CUDA code - wrap in availability check"
fi
```

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | Use Makefile or just shell scripts? | `decided` | Both - Makefile calls scripts |
| D-2 | Session file location? | `decided` | `.sessions/CURRENT_MACHINE.md` |
| D-3 | Mandatory tests before switch? | `pending` | User preference |

---

## Scope Definition

### In Scope

- Git sync workflow for two machines
- Environment detection for code and AI
- Platform-aware development commands
- Testing parity between native and Docker

### Out of Scope

- CI/CD pipeline (future)
- More than 2 machines
- Kubernetes deployment

---

## Conversation Log

### 2026-01-03 - SESSION_015

**Topics Discussed:**
- User workflow: Mac couch → Win11 desk
- Native execution on Mac vs Docker on Win11
- AI assistant confusion about environments
- Need for deterministic sync protocol

**Key Insights:**
- Environment detection is critical for AI context
- Single command for machine switch reduces errors
- Tests must pass on both platforms
- `.sessions/CURRENT_MACHINE.md` provides state for AI assistants

**Action Items:**
- [x] Create `scripts/detect_env.py`
- [x] Create `scripts/switch_out.sh` and `switch_in.sh`
- [x] Create Makefile with platform-aware commands
- [x] Update AGENTS.md with cross-platform instructions
- [x] Create `.sessions/CURRENT_MACHINE.md` tracking

### 2026-01-03 - SESSION_015 (continued)

**Topics Discussed:**
- Mac native dev environment setup and venv configuration
- Need for `make dev` to start ALL services (backend + frontend + Phoenix)
- Parity with Win11 Docker experience

**Changes Made:**
- Installed missing backend dependencies via `uv pip install -r backend/requirements.txt`
- Installed Phoenix for local observability: `uv pip install arize-phoenix`
- Created `scripts/dev_mac.sh` - orchestrates all 3 services with cleanup
- Updated Makefile with new dev commands:
  - `make dev` → Starts backend + frontend + Phoenix
  - `make dev-backend` → Backend only
  - `make dev-frontend` → Frontend only
  - `make dev-phoenix` → Phoenix only
- Updated README.md with new command reference

**Outcome:**
- Mac and Win11 now have identical dev experience on same ports (8100, 3100, 6006)
- All 48 tests passing on Mac native

---

*Template version: 2.0.0 | Per ADR-0048 (Unified Artifact Model)*
