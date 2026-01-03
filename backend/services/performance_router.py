"""Performance & Caching API Router.

Endpoints for monitoring and managing caching, connection pools,
vector indices, and lazy loading across all services.
"""

from fastapi import APIRouter, Query
from typing import Optional

from .cache_service import (
    get_cache_stats,
    clear_all_caches,
    research_cache,
    query_cache,
    embedding_cache,
    trace_cache,
    persistent_cache,
)
from .connection_pool import pool_manager
from .vector_search import vector_service, FAISS_AVAILABLE, FAISS_GPU_AVAILABLE

router = APIRouter(prefix="/api/performance", tags=["Performance & Caching"])


@router.get("/stats")
async def get_performance_stats():
    """Get comprehensive performance statistics."""
    return {
        "caches": get_cache_stats(),
        "connection_pools": pool_manager.stats(),
        "vector_indices": vector_service.stats(),
        "capabilities": {
            "faiss_available": FAISS_AVAILABLE,
            "gpu_acceleration": FAISS_GPU_AVAILABLE,
        }
    }


@router.get("/cache/stats")
async def get_cache_statistics():
    """Get detailed cache statistics."""
    return get_cache_stats()


@router.post("/cache/clear")
async def clear_caches(
    cache_name: Optional[str] = Query(None, description="Specific cache to clear (research, query, embedding, trace, all)")
):
    """Clear caches to free memory."""
    if cache_name == "all" or cache_name is None:
        clear_all_caches()
        return {"cleared": "all", "message": "All in-memory caches cleared"}
    
    cache_map = {
        "research": research_cache,
        "query": query_cache,
        "embedding": embedding_cache,
        "trace": trace_cache,
    }
    
    if cache_name in cache_map:
        cache_map[cache_name].clear()
        return {"cleared": cache_name, "message": f"{cache_name} cache cleared"}
    
    return {"error": f"Unknown cache: {cache_name}"}


@router.post("/cache/invalidate")
async def invalidate_cache_key(
    key: str = Query(..., description="Cache key or prefix to invalidate"),
    prefix: bool = Query(False, description="If true, invalidate all keys with this prefix"),
):
    """Invalidate specific cache entries."""
    results = {}
    
    caches = {
        "research": research_cache,
        "query": query_cache,
        "embedding": embedding_cache,
        "trace": trace_cache,
    }
    
    for name, cache in caches.items():
        if prefix:
            count = cache.invalidate_prefix(key)
            results[name] = {"invalidated": count}
        else:
            success = cache.invalidate(key)
            results[name] = {"invalidated": 1 if success else 0}
    
    return {"key": key, "prefix": prefix, "results": results}


@router.get("/pools/stats")
async def get_connection_pool_stats():
    """Get connection pool statistics."""
    return pool_manager.stats()


@router.get("/vectors/stats")
async def get_vector_index_stats():
    """Get vector index statistics."""
    return vector_service.stats()


@router.post("/vectors/rebuild")
async def rebuild_vector_index(
    index_name: str = Query(..., description="Name of index to rebuild")
):
    """Trigger rebuild of vector index."""
    index = vector_service.indices.get(index_name)
    if not index:
        return {"error": f"Index not found: {index_name}"}
    
    index.build()
    return {"index": index_name, "rebuilt": True, "vectors": len(index._vectors)}


@router.post("/vectors/save")
async def save_vector_indices():
    """Save all vector indices to disk."""
    vector_service.save_all()
    return {"saved": list(vector_service.indices.keys())}


@router.get("/health")
async def performance_health_check():
    """Quick health check for performance systems."""
    stats = get_cache_stats()
    
    # Calculate overall health
    issues = []
    
    # Check cache hit rates
    for name, cache_stats in stats.items():
        if cache_stats.get("hit_rate", 1) < 0.3:
            issues.append(f"Low cache hit rate for {name}: {cache_stats.get('hit_rate', 0):.1%}")
    
    # Check pool utilization
    pool_stats = pool_manager.stats()
    for db_path, pool in pool_stats.items():
        utilization = pool.get("active_connections", 0) / max(pool.get("max_connections", 1), 1)
        if utilization > 0.9:
            issues.append(f"High pool utilization for {db_path}: {utilization:.1%}")
    
    return {
        "healthy": len(issues) == 0,
        "issues": issues,
        "summary": {
            "total_cached_items": sum(s.get("items", 0) for s in stats.values()),
            "total_cache_mb": sum(s.get("size_mb", 0) for s in stats.values()),
            "active_connections": sum(p.get("active_connections", 0) for p in pool_stats.values()),
            "gpu_enabled": FAISS_GPU_AVAILABLE,
        }
    }


@router.post("/warmup")
async def warmup_caches():
    """Pre-warm caches with frequently accessed data."""
    warmed = []
    
    # Warm research paper cache with recent papers
    try:
        from .research_service import ResearchPaperService
        service = ResearchPaperService()
        stats = service.get_database_stats()
        research_cache.set("stats", stats, ttl=3600)
        warmed.append("research_stats")
    except Exception as e:
        pass
    
    # Warm model registry
    try:
        from .p2re.model_registry import get_all_models, get_all_providers
        models = get_all_models()
        providers = get_all_providers()
        query_cache.set("models:all", [m.model_dump() for m in models], ttl=3600)
        query_cache.set("providers:all", [p.model_dump() for p in providers], ttl=3600)
        warmed.append("model_registry")
    except Exception as e:
        pass
    
    return {"warmed": warmed, "message": f"Pre-warmed {len(warmed)} cache entries"}
