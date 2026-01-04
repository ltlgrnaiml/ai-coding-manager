# Post-Change Checklist

> **Purpose**: Deterministic verification after ANY code changes to prevent .env and database loading failures.
> **Rule**: Run this checklist BEFORE considering a change complete.

---

## Quick Reference Commands

```bash
# Full verification (run all checks)
make verify  # or ./scripts/verify-changes.sh

# Individual checks
docker compose build backend frontend    # Rebuild containers
docker compose up -d                       # Restart services
docker compose logs -f backend             # Watch backend logs
curl http://localhost:8100/api/health      # Health check
```

---

## Checklist

### 1. Environment (.env) Verification

| Check | Command | Expected |
|-------|---------|----------|
| .env exists | `[ -f .env ] && echo "✅" || echo "❌"` | ✅ |
| .env has API keys | `grep -q "XAI_API_KEY=.\+" .env && echo "✅" || echo "❌"` | ✅ |
| .env not in .gitignore exclusion | `cat .gitignore \| grep -v "^#" \| grep ".env"` | Should see `.env` |

**Common Failures**:
- `.env` file missing (copy from `.env.example`)
- API keys still have placeholder values
- Docker not mounting `.env` into container

**Fix**: 
```bash
cp .env.example .env
# Edit .env with real API keys
```

---

### 2. Docker Container Rebuild

| Check | Command | Expected |
|-------|---------|----------|
| Backend rebuilt | `docker compose build backend` | Exit 0 |
| Frontend rebuilt | `docker compose build frontend` | Exit 0 |
| Containers restarted | `docker compose up -d` | All services "Started" |

**CRITICAL**: After ANY code change:
```bash
docker compose build backend frontend
docker compose up -d
```

**Common Failures**:
- Old code still running (forgot to rebuild)
- Build cache using stale layers
- Volume mounts overriding built code

**Fix**:
```bash
docker compose build --no-cache backend  # Force full rebuild
docker compose down && docker compose up -d  # Full restart
```

---

### 3. Database Initialization Verification

| Database | Log Message | Location |
|----------|-------------|----------|
| Knowledge DB | "SQLite knowledge database initialized" | `~/.aikh/knowledge.db` |
| P2RE Trace DB | "P2RE trace database initialized" | `~/.aikh/p2re.db` |
| Memory DB | "Memory database initialized" | `~/.aikh/memory.db` |

**Verification Command**:
```bash
docker compose logs backend 2>&1 | grep -E "(database initialized|Failed to initialize)"
```

**Expected Output**:
```
SQLite knowledge database initialized
P2RE trace database initialized
Memory database initialized
```

**Common Failures**:
- Database directory doesn't exist
- Permission denied on database file
- SQLite locked by another process
- Schema migration failed

**Fix**:
```bash
# Ensure database directory exists with correct permissions
mkdir -p ~/.aikh
chmod 755 ~/.aikh

# If database is corrupted, backup and recreate
mv ~/.aikh/knowledge.db ~/.aikh/knowledge.db.bak
docker compose restart backend
```

---

### 4. API Health Check

| Endpoint | Command | Expected |
|----------|---------|----------|
| Health | `curl -s http://localhost:8100/api/health` | `{"status": "healthy", ...}` |
| Models | `curl -s http://localhost:8100/api/chat/models` | List of models |
| Workflow Stats | `curl -s http://localhost:8100/api/workflow/stats` | `{"discussions": N, ...}` |

**Full Health Check Script**:
```bash
echo "=== AICM Health Check ==="

# Backend
if curl -sf http://localhost:8100/api/health > /dev/null; then
    echo "✅ Backend: healthy"
else
    echo "❌ Backend: unreachable"
fi

# Frontend  
if curl -sf http://localhost:3100 > /dev/null; then
    echo "✅ Frontend: healthy"
else
    echo "❌ Frontend: unreachable"
fi

# Phoenix (optional)
if curl -sf http://localhost:6006 > /dev/null; then
    echo "✅ Phoenix: healthy"
else
    echo "⚠️  Phoenix: not running (optional)"
fi
```

---

### 5. Import Order Verification (Code Changes Only)

If you modified Python imports, verify `.env` loads BEFORE other imports:

```python
# CORRECT - .env loaded first
from dotenv import load_dotenv
load_dotenv()

import os  # Now os.getenv() works
from backend.services import something  # Other imports after

# WRONG - imports before .env
import os
from backend.services import something  # May read unset env vars!
from dotenv import load_dotenv
load_dotenv()  # Too late!
```

**Verification**:
```bash
head -20 backend/main.py | grep -A5 "load_dotenv"
```

---

### 6. Volume Mount Verification (Docker)

Check that database files persist across restarts:

```bash
# List mounted volumes
docker compose config | grep -A5 "volumes:"

# Verify database files are on host, not in container
ls -la ~/.aikh/
```

**Expected**:
```
-rw-r--r--  knowledge.db
-rw-r--r--  p2re.db
-rw-r--r--  memory.db
```

---

## Automated Verification Script

Create `scripts/verify-changes.sh`:

```bash
#!/bin/bash
set -e

echo "🔍 AICM Post-Change Verification"
echo "================================"

ERRORS=0

# 1. Check .env
echo -n "1. .env file: "
if [ -f .env ]; then
    if grep -q "XAI_API_KEY=.\+" .env 2>/dev/null; then
        echo "✅"
    else
        echo "⚠️  Missing API keys"
        ((ERRORS++))
    fi
else
    echo "❌ Missing"
    ((ERRORS++))
fi

# 2. Rebuild containers
echo "2. Rebuilding containers..."
docker compose build backend frontend --quiet || ((ERRORS++))
echo "   ✅ Build complete"

# 3. Restart services
echo "3. Restarting services..."
docker compose up -d --quiet-pull || ((ERRORS++))
sleep 3  # Wait for startup

# 4. Check database initialization
echo -n "4. Database init: "
if docker compose logs backend 2>&1 | grep -q "database initialized"; then
    echo "✅"
else
    echo "❌ Check logs: docker compose logs backend"
    ((ERRORS++))
fi

# 5. Health checks
echo -n "5. Backend health: "
if curl -sf http://localhost:8100/api/health > /dev/null; then
    echo "✅"
else
    echo "❌"
    ((ERRORS++))
fi

echo -n "6. Frontend health: "
if curl -sf http://localhost:3100 > /dev/null; then
    echo "✅"
else
    echo "❌"
    ((ERRORS++))
fi

# Summary
echo ""
echo "================================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ All checks passed!"
    exit 0
else
    echo "❌ $ERRORS check(s) failed"
    exit 1
fi
```

---

## Failure Recovery Procedures

### .env Not Loading

1. Check file exists: `ls -la .env`
2. Check Docker mounts it: `docker compose config | grep env`
3. Check load order in `backend/main.py` (must be first import)
4. Restart container: `docker compose restart backend`

### Database Not Initializing

1. Check logs: `docker compose logs backend | grep -i database`
2. Check permissions: `ls -la ~/.aikh/`
3. Check disk space: `df -h ~/.aikh`
4. Try fresh database:
   ```bash
   docker compose down
   rm ~/.aikh/*.db  # Backup first if needed!
   docker compose up -d
   ```

### Container Running Old Code

1. Force rebuild: `docker compose build --no-cache backend`
2. Remove old containers: `docker compose down --remove-orphans`
3. Fresh start: `docker compose up -d --force-recreate`

---

## Add to SPROMPT Verification Gates

Include in every SPROMPT's verification section:

```markdown
## Verification Gates

### Post-Change Checklist (Required)
- [ ] `./scripts/verify-changes.sh` passes
- [ ] All databases initialized (check logs)
- [ ] Health endpoints return 200
- [ ] Frontend loads without console errors
```

---

*Last Updated: 2026-01-03 | Part of: AI Coding Manager (AICM)*
