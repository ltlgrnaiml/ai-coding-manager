"""Test that all package imports work correctly."""

import pytest


def test_llm_imports():
    """Test LLM module imports."""
    from ai_dev_orchestrator.llm import (
        get_xai_chat_model,
        XAIChatModel,
        generate_structured,
        generate_text,
        check_health,
        is_available,
        get_llm_usage_stats,
        get_available_models,
        get_current_model,
        set_current_model,
        LLMStatus,
        LLMHealthCheck,
        LLMResponse,
        ModelInfo,
        create_rag_chain,
        RAGChain,
        RAGResponse,
    )
    
    # Basic assertions
    assert LLMStatus.AVAILABLE == "available"
    assert len(get_available_models()) > 0
    assert get_current_model() is not None


def test_knowledge_imports():
    """Test knowledge module imports."""
    from ai_dev_orchestrator.knowledge import (
        init_database,
        get_connection,
        DB_PATH,
        SearchService,
        SearchHit,
        EmbeddingService,
        EmbeddingResult,
        ContextBuilder,
        ContextResult,
        ContextChunk,
        get_context_builder,
        EnhancedRAGBuilder,
        EnhancedRAGConfig,
        EnhancedRAGResult,
        get_enhanced_rag_builder,
        get_enhanced_context,
    )
    
    # Basic assertions
    assert DB_PATH is not None
    config = EnhancedRAGConfig()
    assert config.use_query_enhancement is True


def test_observability_imports():
    """Test observability module imports."""
    from ai_dev_orchestrator.observability import (
        init_phoenix,
        shutdown_phoenix,
        get_tracer,
        trace_span,
        is_tracing_enabled,
    )
    
    # Should not be enabled by default
    assert is_tracing_enabled() is False


def test_workflow_imports():
    """Test workflow module imports."""
    from ai_dev_orchestrator.workflow import (
        create_plan,
        load_plan,
        save_plan,
        get_next_plan_id,
        create_discussion,
        load_discussion,
        save_discussion,
        get_next_discussion_id,
        create_session,
        get_current_session,
        get_next_session_id,
    )
    
    # Basic assertions - these should work without errors
    assert callable(create_plan)
    assert callable(create_discussion)
    assert callable(create_session)


def test_top_level_imports():
    """Test top-level package imports."""
    from ai_dev_orchestrator import (
        __version__,
        get_xai_chat_model,
        generate_structured,
        generate_text,
        check_health,
        is_available,
        create_rag_chain,
        init_database,
        get_connection,
        init_phoenix,
        shutdown_phoenix,
    )
    
    assert __version__ == "2025.12.01"


def test_cli_imports():
    """Test CLI module imports."""
    from ai_dev_orchestrator.cli import main
    
    assert callable(main)


def test_model_info():
    """Test model info structure."""
    from ai_dev_orchestrator.llm import get_available_models, ModelInfo
    
    models = get_available_models()
    assert len(models) > 0
    
    model = models[0]
    assert isinstance(model, ModelInfo)
    assert model.id is not None
    assert model.context_window > 0
    assert model.input_price >= 0
    assert model.output_price >= 0


def test_sanitizer():
    """Test content sanitizer."""
    from ai_dev_orchestrator.knowledge.sanitizer import Sanitizer
    
    sanitizer = Sanitizer()
    
    # Test email redaction
    result = sanitizer.sanitize("Contact me at test@example.com")
    assert "[EMAIL]" in result.content
    assert result.redactions >= 1
    
    # Test phone redaction
    result = sanitizer.sanitize("Call 555-123-4567")
    assert "[PHONE]" in result.content
    
    # Test truncation
    long_text = "x" * 20000
    result = sanitizer.sanitize(long_text)
    assert result.truncated is True
    assert "[TRUNCATED]" in result.content
