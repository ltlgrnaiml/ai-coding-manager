# DISC-028: GPU-Accelerated RAG Containerization Patterns

> **Status**: `active`
> **Created**: 2026-01-03
> **Updated**: 2026-01-03
> **Author**: AI-Assisted
> **AI Session**: SESSION_015
> **Depends On**: DISC-006
> **Blocks**: None
> **Dependency Level**: L1

---

## Summary

Exploration of GPU-accelerated RAG system architectures in containerized (Docker/K8s) environments. This discussion addresses when separate GPU containers provide performance benefits vs. when they add unnecessary latency, with specific patterns for vector databases, embedding generation, and LLM inference.

---

## Context

### Background

Modern RAG systems involve several GPU-acceleratable operations:
1. **Embedding Generation** - Converting text to vectors (sentence-transformers, OpenAI embeddings)
2. **Vector Similarity Search** - Finding nearest neighbors (FAISS, Qdrant, Milvus)
3. **LLM Inference** - Generating responses with retrieved context (local models)
4. **Re-ranking** - LLM-based relevance scoring

Current AICM architecture (per ADR-0002, DISC-006):
- SQLite-based knowledge archive with FTS5 + vector embeddings
- Local `all-mpnet-base-v2` model for embeddings
- Hybrid search (BM25 + cosine similarity)
- LLM re-ranking via xAI API

### Trigger

User question: "Does it make sense to spin up separate containers whose only purpose is to serve GPU-accelerated DB info? Would that end up faster than code directly calling the DB in its own container?"

---

## Common RAG Flows in Production

### Flow 1: Monolithic (Current AICM Pattern)

```
┌─────────────────────────────────────────────────────────────┐
│                     Backend Container                        │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │ API Layer   │──▶│ RAG Engine  │──▶│ Embedding   │        │
│  │ (FastAPI)   │   │ (retrieval) │   │ (s-trans)   │        │
│  └─────────────┘   └─────────────┘   └─────────────┘        │
│         │                │                   │               │
│         ▼                ▼                   ▼               │
│  ┌─────────────────────────────────────────────────┐        │
│  │              SQLite (knowledge.db)              │        │
│  │   documents | chunks | embeddings | fts5        │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

**Characteristics:**
- Zero network overhead for retrieval
- ~500MB memory for embedding model
- No GPU required (CPU inference acceptable for small corpus)
- Single point of failure

**Best For:** Development, small teams, <100K documents

---

### Flow 2: Dedicated Vector DB Container

```
┌─────────────────────┐        ┌─────────────────────────────┐
│  Backend Container  │        │   Vector DB Container       │
│  ┌───────────────┐  │  gRPC  │  ┌───────────────────────┐  │
│  │   API Layer   │──┼───────▶│  │   Qdrant / Milvus     │  │
│  │   (FastAPI)   │  │  ~1ms  │  │   (GPU-accelerated)   │  │
│  └───────────────┘  │        │  └───────────────────────┘  │
│         │           │        │             │               │
│         ▼           │        │             ▼               │
│  ┌───────────────┐  │        │  ┌───────────────────────┐  │
│  │ SQLite (meta) │  │        │  │    Vector Index       │  │
│  └───────────────┘  │        │  │  (HNSW/IVF on GPU)    │  │
└─────────────────────┘        └─────────────────────────────┘
```

**Characteristics:**
- 0.5-2ms network overhead per query
- GPU accelerates similarity search (10-100x speedup on 1M+ vectors)
- Horizontal scaling of vector search independently
- Built-in batching, caching, sharding

**Best For:** Production, >100K documents, high QPS

---

### Flow 3: GPU Inference Sidecar

```
┌─────────────────────┐        ┌─────────────────────────────┐
│  Backend Container  │  HTTP  │   GPU Inference Container   │
│  ┌───────────────┐  │        │  ┌───────────────────────┐  │
│  │   API Layer   │──┼───────▶│  │  Embedding Service    │  │
│  └───────────────┘  │  ~2ms  │  │  (sentence-trans GPU) │  │
│         │           │        │  └───────────────────────┘  │
│         │           │        │             │               │
│         │           │        │  ┌───────────────────────┐  │
│         │           │◀───────┼──│  Local LLM (Ollama)   │  │
│         │           │ ~50ms  │  │  (llama.cpp + GPU)    │  │
│         ▼           │        │  └───────────────────────┘  │
│  ┌───────────────┐  │        └─────────────────────────────┘
│  │ SQLite/Qdrant │  │
└─────────────────────┘
```

**Characteristics:**
- Centralizes GPU workloads in one container
- Amortizes GPU memory cost across services
- Network overhead for embeddings (batch to amortize)
- Single GPU can serve multiple backend instances

**Best For:** Local LLM inference, shared GPU resources, multi-service

---

### Flow 4: Full Microservices (High Scale)

```
┌─────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────┐
│   API   │──▶│  Retriever  │──▶│  Reranker   │──▶│  LLM     │
│ Gateway │   │  Service    │   │  Service    │   │ Service  │
└─────────┘   └─────────────┘   └─────────────┘   └──────────┘
                    │                  │                │
                    ▼                  ▼                ▼
              ┌──────────┐       ┌──────────┐     ┌──────────┐
              │ Qdrant   │       │ Cross-   │     │ vLLM /   │
              │ Cluster  │       │ Encoder  │     │ TGI      │
              │ (3 nodes)│       │ GPU Pool │     │ GPU Pool │
              └──────────┘       └──────────┘     └──────────┘
```

**Characteristics:**
- Each component scales independently
- Multiple network hops (higher latency)
- Maximum flexibility and fault isolation
- Complex orchestration required

**Best For:** Enterprise, millions of documents, 1000s QPS

---

## When GPU Containers Add Value

### DO Use Separate GPU Containers When:

| Scenario | Why It Helps |
|----------|--------------|
| **Batch embedding generation** | Process 1000s of texts, amortize network overhead |
| **Vector DB >100K docs** | GPU-accelerated HNSW search provides 10-100x speedup |
| **Local LLM inference** | GPU memory isolated, can serve multiple backends |
| **Multi-tenant architecture** | Shared GPU pool across services |
| **Independent scaling** | Scale GPU containers separately from API layer |

### DON'T Use Separate GPU Containers When:

| Scenario | Why It Hurts |
|----------|--------------|
| **Real-time per-request embeddings** | Network round-trip (1-5ms) dominates small inference |
| **Small corpus (<10K docs)** | CPU similarity search is fast enough |
| **Simple CRUD + occasional search** | Complexity not justified |
| **Single-user/dev environment** | Overhead outweighs benefits |

---

## Performance Comparison

### Network Overhead Analysis

| Operation | Direct (in-process) | Container Call | Overhead |
|-----------|---------------------|----------------|----------|
| Cosine similarity (1 query, 10K vectors) | 2ms | 4ms | +100% |
| Cosine similarity (1 query, 1M vectors) | 200ms | 205ms | +2.5% |
| Embedding generation (1 text) | 15ms | 18ms | +20% |
| Embedding generation (100 texts) | 150ms | 155ms | +3% |
| LLM inference (100 tokens) | 500ms | 510ms | +2% |

**Key Insight:** Network overhead is *constant* (~1-5ms), so it becomes negligible for larger operations.

### Batching Strategy Recommendations

```python
# ANTI-PATTERN: Per-request embedding calls
for doc in documents:
    embedding = gpu_container.embed(doc.text)  # 18ms × N = slow
    
# PATTERN: Batch operations
embeddings = gpu_container.embed_batch([d.text for d in documents])  # 155ms total
```

**Batching Thresholds:**
- Embeddings: Batch 32+ texts per call
- Vector search: Batch queries if <10ms importance
- LLM: Batch where possible (structured extraction)

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: Document GPU vs CPU performance tradeoffs for AICM use cases
- [ ] **FR-2**: Provide decision matrix for containerization patterns
- [ ] **FR-3**: Define batching strategies for GPU container calls
- [ ] **FR-4**: Identify upgrade path from current SQLite-based architecture

### Non-Functional Requirements

- [ ] **NFR-1**: Any GPU container pattern must maintain <100ms p95 latency for search
- [ ] **NFR-2**: Solution must work with Docker Compose (current deployment method)

---

## Constraints

- **C-1**: Must maintain compatibility with existing `knowledge.db` schema
- **C-2**: GPU not required for dev/test environments (graceful fallback)
- **C-3**: No vendor lock-in to specific vector DB

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | What is current document count in knowledge archive? | `answered` | Core docs small; chat logs, research papers, traces will grow LARGE |
| Q-2 | Is local LLM inference a priority? | `open` | TBD - hardware supports it |
| Q-3 | What GPU hardware is available? | `answered` | See Hardware Profile below |
| Q-4 | Is horizontal scaling required? | `answered` | No - single-user dev environments |

---

## Hardware Profile (Answered Q-3)

### Windows 11 Workstation (Primary GPU)

| Component | Spec | Notes |
|-----------|------|-------|
| **GPU 1** | MSI RTX 5090 32GB (Liquid Cooled) | Primary - PCIe 16x |
| **GPU 2** | EVGA RTX 3090 Ti 24GB (Air Cooled) | Secondary - PCIe 4x |
| **CPU** | AMD Ryzen 9 7950X | 16C/32T |
| **Motherboard** | MSI MEG ACE | Supports 16x + 4x GPU config |
| **Environment** | Docker Desktop + WSL2 (Ubuntu) | Containers + workspace in WSL |

**GPU Strategy for Win11:**
- **5090 (32GB)**: LLM inference, large embedding batches, reranking
- **3090 Ti (24GB)**: Vector DB (Qdrant GPU), parallel embedding
- Both cards can work simultaneously for different workloads

### MacBook Pro 2024 (Unified Memory)

| Component | Spec | Notes |
|-----------|------|-------|
| **Chip** | Apple M4 Max | GPU cores share unified memory |
| **RAM** | 128GB Unified | Available to both CPU and GPU |
| **Environment** | Docker Desktop for Mac | ARM containers |

**GPU Strategy for Mac:**
- M4 Max GPU acceleration via Metal (MPS backend in PyTorch)
- 128GB unified memory = can load very large models
- Limited Docker GPU passthrough (no CUDA) - prefer native Python for GPU workloads

---

## Corpus Size Projection (Answered Q-1)

| Content Type | Initial | 6 Months | 1 Year | GPU Benefit |
|--------------|---------|----------|--------|-------------|
| Core docs (ADRs, DISCs, Plans) | ~100 | ~500 | ~1K | Low |
| Chat logs | ~50 sessions | ~500 | ~2K | Medium |
| Research papers | ~100 | ~1K | ~5K | **HIGH** |
| Traces (Phoenix) | ~1K | ~50K | ~500K | **HIGH** |

**Projection**: Within 6 months, corpus will justify GPU-accelerated vector search.

---

## Options Considered

### Option A: Stay Monolithic (Current)

**Description**: Keep current architecture with SQLite + local embedding model in backend container.

**Pros:**
- Zero network overhead
- Simple deployment and debugging
- No additional containers to manage

**Cons:**
- Embedding model consumes ~500MB RAM in every backend instance
- No GPU acceleration for large corpus
- Scales only vertically

### Option B: Add GPU Inference Sidecar

**Description**: Add single container with GPU for embeddings + optional local LLM.

```yaml
services:
  aidev-backend:
    # ... existing config
  
  aidev-gpu:
    image: ai-inference:latest
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    ports:
      - "8200:8200"
```

**Pros:**
- GPU acceleration for embeddings
- Can add local LLM later
- Backend instances share GPU resources

**Cons:**
- Network overhead for each embedding call
- Must implement batching to be efficient
- Additional container to manage

### Option C: Dedicated Vector DB (Qdrant)

**Description**: Replace SQLite vector storage with Qdrant container.

```yaml
services:
  aidev-backend:
    # ... existing config
    
  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
```

**Pros:**
- Purpose-built for vector search
- Built-in GPU acceleration (with qdrant-gpu image)
- Handles batching, caching, sharding
- Active development and community

**Cons:**
- Migration effort from SQLite embeddings table
- Additional dependency
- Overkill for <100K documents

### Option D: Hybrid (Recommended for Scale)

**Description**: Keep SQLite for metadata, use Qdrant for vectors, GPU sidecar for embeddings.

```yaml
services:
  aidev-backend:
    # Metadata in SQLite, vectors in Qdrant
    
  qdrant:
    image: qdrant/qdrant:v1.7.0
    
  aidev-embedder:
    image: ai-embedder:latest
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
```

**Pros:**
- Best of both worlds
- Clear separation of concerns
- Each component scales independently

**Cons:**
- Most complex to set up
- Multiple network hops

### Recommendation

**Given your hardware profile, recommend Option D (Hybrid) with phased rollout:**

#### Phase 1: Now (Low Effort)
Stay monolithic but prepare for GPU containers:
```yaml
# docker-compose.yml addition
services:
  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
```

#### Phase 2: When Research Papers Hit 500+ 
Add GPU-accelerated Qdrant:
```yaml
  qdrant:
    image: qdrant/qdrant:v1.7.0-cuda  # GPU version
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['1']  # 3090 Ti
              capabilities: [gpu]
```

#### Phase 3: When Local LLM Desired
Add inference sidecar on 5090:
```yaml
  aidev-inference:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']  # 5090
              capabilities: [gpu]
    volumes:
      - ollama_models:/root/.ollama
    ports:
      - "11434:11434"
```

**Rationale:**
- 5090 (32GB) handles LLM inference (needs most VRAM)
- 3090 Ti (24GB) handles vector DB + embeddings (parallel)
- Both can run simultaneously on your MEG ACE board
- Mac uses native Python for GPU (no Docker GPU passthrough on macOS)

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | Should AICM adopt GPU containers now? | `pending` | Depends on Q-1, Q-2 |
| D-2 | Which vector DB if scaling? | `pending` | Qdrant recommended |
| D-3 | Batch size for GPU container calls? | `decided` | 32+ for embeddings |

---

## Scope Definition

### In Scope

- GPU containerization patterns for RAG systems
- Performance tradeoff analysis
- Upgrade path recommendations for AICM

### Out of Scope

- Kubernetes-specific deployment (Docker Compose focus)
- Multi-node vector DB clustering
- Model fine-tuning infrastructure

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| ADR | (pending) | GPU Containerization Strategy | `draft` |

---

## Conversation Log

### 2026-01-03 - SESSION_015

**Topics Discussed:**
- When separate GPU containers make sense vs add overhead
- Common RAG deployment patterns (monolithic → microservices)
- Batching strategies for network overhead amortization
- Current AICM architecture analysis

**Key Insights:**
- Network overhead is constant (~1-5ms), becomes negligible for large operations
- Batch operations are key to making GPU containers worthwhile
- Current AICM scale likely doesn't need GPU containers
- Qdrant is recommended vector DB when scaling needed

**Action Items:**
- [ ] Answer open questions about document count, GPU availability
- [ ] Decide on upgrade trigger criteria
- [ ] Document batching patterns in code

---

*Template version: 2.0.0 | Per ADR-0048 (Unified Artifact Model)*
