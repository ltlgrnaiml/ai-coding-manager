# Concurrent Development Policy

> **Scope**: Multi-device, multi-AI-session development workflow  
> **Environments**: macOS, WSL2 Ubuntu (Windows)

---

## Core Principle

**Git is the single source of truth.** All code synchronization happens through Git. Local uncommitted changes exist only on that device until pushed.

---

## 1. Branching Strategy

### Device-Based Branches (Recommended for Solo Dev)

When working across multiple devices concurrently:

```
master (or main)
  ├── dev/mac          # Mac development work
  ├── dev/windows      # Windows/WSL2 development work
  └── feature/xyz      # Specific feature work
```

### Workflow

```bash
# On Mac - start work
git checkout -b dev/mac
# ... make changes ...
git add -A && git commit -m "Mac: description"
git push origin dev/mac

# On Windows - pull and continue
git fetch origin
git checkout dev/windows
git merge origin/dev/mac  # or cherry-pick specific commits
```

### When to Merge to Master

- Feature complete and tested
- Docker builds successfully
- All tests pass

---

## 2. Conflict Resolution

### Prevention (Best Practice)

| Strategy | Description |
|----------|-------------|
| **File ownership** | Each device focuses on different files/modules |
| **Small commits** | Commit frequently, push often |
| **Pull before work** | Always `git pull` before starting |
| **Communication** | Document which device is working on what |

### When Conflicts Occur

**Yes, conflicts require manual review.** Git cannot auto-merge conflicting changes.

```bash
# After a merge with conflicts
git status                    # Shows conflicting files
# Edit files manually - look for <<<<<<< ======= >>>>>>>
git add <resolved-files>
git commit -m "Resolved merge conflicts"
```

### AI Session Conflicts

When multiple AI sessions work on the same codebase:

1. **Each AI session = unique SESSION_XXX file** (per AGENTS.md)
2. AI sessions should check `.sessions/` before starting
3. If same files modified → manual review required

---

## 3. Current Situation: 128 Uncommitted Files

### Immediate Action Required

```bash
# On Mac (where changes exist)
git add -A
git commit -m "feat: Docker containerization and cross-platform support

- Added frontend/src/lib/utils.ts
- Fixed backend.Dockerfile with main package installation
- Added .gitattributes for cross-platform line endings
- Fixed .gitignore to allow frontend/src/lib/
- Added PDF extraction dependencies
- Fixed type imports in devtools_service.py"

git push origin master
```

```bash
# On Windows (to get changes)
git pull origin master
```

### Why Windows Shows No Changes

Windows has the **last pushed state**. The 128 modified files on Mac haven't been committed/pushed yet, so they don't exist on Windows.

---

## 4. Recommended Daily Workflow

### Starting Work (Any Device)

```bash
git fetch origin
git status                    # Check for local changes
git pull origin master        # Get latest (if no conflicts)
```

### Ending Work Session

```bash
git add -A
git status                    # Review what's being committed
git commit -m "type: description"
git push origin master        # Or your branch
```

### Switching Devices Mid-Work

```bash
# Device A: Save work-in-progress
git add -A
git commit -m "WIP: description"
git push origin dev/device-a

# Device B: Continue work
git fetch origin
git checkout dev/device-a     # Or merge into your branch
```

---

## 5. Docker-Specific Considerations

### Image Consistency

Docker images are built from committed code. Uncommitted changes:
- ❌ Won't appear in Docker builds on other devices
- ✅ Will appear if you build locally

### Shared Volumes

The `docker-compose.yml` mounts local directories:
```yaml
volumes:
  - ./.adrs:/workspace/.adrs
  - ./.sessions:/workspace/.sessions
```

These reflect **local filesystem state**, not Git state.

---

## 6. Emergency Recovery

### Accidentally Overwrote Changes

```bash
git reflog                    # Find previous state
git reset --hard HEAD@{n}     # Restore to that state
```

### Merge Gone Wrong

```bash
git merge --abort             # Cancel in-progress merge
# or
git reset --hard HEAD~1       # Undo last commit
```

### Lost Uncommitted Work

If not committed, Git can't help. Consider:
- IDE local history (VS Code, JetBrains)
- Time Machine (Mac) / File History (Windows)

---

## 7. Checklist: Before Switching Devices

- [ ] All changes committed (`git status` shows clean)
- [ ] Changes pushed to remote (`git push`)
- [ ] Docker containers stopped (if applicable)
- [ ] Note current work state in `.sessions/` file

---

## 8. AI Knowledge Hub (AIKH) - Cross-Platform Data

### Centralized Database Location

All AIKH databases are stored in a centralized, platform-agnostic location:

| Platform | AIKH Home |
|----------|-----------|
| **macOS** | `~/.aikh/` → `/Users/<user>/.aikh/` |
| **WSL2/Linux** | `~/.aikh/` → `/home/<user>/.aikh/` |
| **Docker** | `/aikh/` (mounted volume) |

### Database Files

| Database | File | Purpose |
|----------|------|---------|
| **Artifacts** | `artifacts.db` | Documents, chunks, embeddings, RAG |
| **Chat Logs** | `chatlogs.db` | Cross-project conversation history |
| **Research** | `research.db` | Academic papers, citations, PDFs |

### Syncing AIKH Data

AIKH databases are **local per machine** and NOT synced via Git. Options:

1. **Manual sync**: Copy `~/.aikh/*.db` between machines
2. **Cloud sync**: Use Dropbox/OneDrive symlink to `~/.aikh/`
3. **Fresh rebuild**: Re-ingest from source files

---

## 9. GPU/ML Acceleration Strategy

### GPU-First Policy

All ML operations (embeddings, inference) should use GPU acceleration when available.

### Platform Configuration

| Platform | Hardware | Framework | PyTorch Device |
|----------|----------|-----------|----------------|
| **Windows/WSL2** | NVIDIA RTX 5090 | CUDA/cuDNN | `cuda` |
| **macOS** | Apple M4 Max | Metal Performance Shaders | `mps` |
| **Fallback** | CPU | - | `cpu` |

### Detection Code

```python
import torch

def get_device():
    if torch.cuda.is_available():
        return "cuda"  # NVIDIA GPU
    elif torch.backends.mps.is_available():
        return "mps"   # Apple Silicon
    return "cpu"
```

### M4 Max Specifics (macOS)

The M4 Max chip provides:
- **38-core GPU** for ML inference via Metal
- **16-core Neural Engine** (not directly accessible via PyTorch)
- **Unified Memory** (up to 128GB shared between CPU/GPU)

To enable MPS acceleration:
```bash
# Ensure PyTorch with MPS support
pip install torch torchvision torchaudio

# Verify MPS availability
python -c "import torch; print(torch.backends.mps.is_available())"
```

### RTX 5090 Specifics (Windows/WSL2)

The RTX 5090 provides:
- **32GB GDDR7** dedicated VRAM
- **CUDA 12.x** compute capability
- **Tensor Cores** for accelerated inference

To enable CUDA acceleration:
```bash
# Ensure CUDA toolkit installed
nvidia-smi  # Verify driver

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

## Summary

| Question | Answer |
|----------|--------|
| How to sync between devices? | Git push/pull |
| Are conflicts automatic? | No, manual review required |
| Why doesn't Windows have my changes? | Not committed/pushed yet |
| Best practice? | Commit often, push before switching devices |
| Can AI sessions conflict? | Yes, use SESSION files to coordinate |
| Where is AIKH data? | `~/.aikh/` (local per machine) |
| GPU on Mac? | MPS (Metal) via `torch.device("mps")` |
| GPU on Windows? | CUDA via `torch.device("cuda")` |
