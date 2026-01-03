#!/usr/bin/env python3
"""Basic usage examples for AI Dev Orchestrator.

This script demonstrates the core features of the ai-dev-orchestrator package:
1. Knowledge database initialization and document storage
2. Full-text search with FTS5
3. LLM service configuration (without API calls)
4. Contract validation with Pydantic schemas

Run with: python examples/basic_usage.py
"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path for contracts imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# =============================================================================
# 1. Knowledge Database
# =============================================================================

def demo_knowledge_database():
    """Demonstrate knowledge database operations."""
    print("\n=== Knowledge Database Demo ===\n")
    
    from ai_dev_orchestrator.knowledge.database import init_database
    
    # Create a temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "demo_knowledge.db"
        conn = init_database(db_path)
        
        print(f"✓ Initialized database at: {db_path}")
        
        # Insert some sample documents
        docs = [
            ("ADR-0001", "adr", "AI Development Workflow", 
             "This ADR defines the 6-tier workflow for AI-assisted development."),
            ("DISC-001", "discussion", "API Design Discussion",
             "Discussing whether to use REST or GraphQL for the new API."),
            ("PLAN-001", "plan", "MVP Implementation Plan",
             "Plan for implementing the minimum viable product."),
        ]
        
        for doc_id, doc_type, title, content in docs:
            conn.execute("""
                INSERT INTO documents (id, type, title, content, file_path, file_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, doc_type, title, content, f"{doc_type}s/{doc_id}.md", "hash"))
        conn.commit()
        print(f"✓ Inserted {len(docs)} sample documents")
        
        # Full-text search
        print("\n--- Full-Text Search ---")
        cursor = conn.execute("""
            SELECT d.id, d.type, d.title FROM content_fts f
            JOIN documents d ON f.rowid = d.rowid
            WHERE content_fts MATCH ?
        """, ("API",))
        
        results = cursor.fetchall()
        print(f"Search for 'API': found {len(results)} result(s)")
        for row in results:
            print(f"  - [{row['type']}] {row['id']}: {row['title']}")
        
        conn.close()


# =============================================================================
# 2. LLM Service Configuration
# =============================================================================

def demo_llm_service():
    """Demonstrate LLM service configuration."""
    print("\n=== LLM Service Demo ===\n")
    
    from ai_dev_orchestrator.llm.service import (
        get_available_models,
        get_current_model,
        set_current_model,
        check_health,
    )
    
    # List available models
    models = get_available_models()
    print(f"✓ {len(models)} models available:")
    for m in models[:3]:  # Show first 3
        print(f"  - {m.name} ({m.id})")
        print(f"    Context: {m.context_window:,} tokens, Category: {m.category}")
    if len(models) > 3:
        print(f"  ... and {len(models) - 3} more")
    
    # Get/set current model
    current = get_current_model()
    print(f"\n✓ Current model: {current}")
    
    # Check health (will show NO_API_KEY if not configured)
    health = check_health()
    print(f"✓ Health check: {health.status.value}")
    if health.status.value == "no_api_key":
        print("  (Set XAI_API_KEY environment variable to enable LLM calls)")


# =============================================================================
# 3. Contract Validation
# =============================================================================

def demo_contracts():
    """Demonstrate Pydantic contract validation."""
    print("\n=== Contract Validation Demo ===\n")
    
    from contracts.plan_schema import (
        PlanSchema,
        PlanStatus,
        GranularityLevel,
        Milestone,
        MilestoneStatus,
        Task,
        TaskStatus,
    )
    from contracts.adr_schema import ADRSchema
    from contracts.discussion_schema import DiscussionSchema, DiscussionStatus
    
    # Create a valid plan
    task = Task(
        id="T-M1-01",
        title="Implement feature X",
        description="Build the core feature",
        status=TaskStatus.PENDING,
        verification_command="pytest tests/test_feature.py -v",
    )
    
    milestone = Milestone(
        id="M1",
        name="Core Feature",
        title="Core Feature",
        objective="Complete the core feature implementation",
        status=MilestoneStatus.PENDING,
        tasks=[task],
    )
    
    plan = PlanSchema(
        id="PLAN-001",
        title="Feature X Implementation",
        created_date="2025-12-31",
        updated_date="2025-12-31",
        author="Developer",
        summary="Plan to implement Feature X",
        objective="Deliver working Feature X",
        granularity=GranularityLevel.L1_STANDARD,
        milestones=[milestone],
    )
    
    print(f"✓ Created valid plan: {plan.id}")
    print(f"  Title: {plan.title}")
    print(f"  Granularity: {plan.granularity.value}")
    print(f"  Milestones: {len(plan.milestones)}")
    print(f"  Tasks: {len(plan.milestones[0].tasks)}")
    
    # Demonstrate validation error
    print("\n--- Validation Error Demo ---")
    try:
        invalid_plan = PlanSchema(
            id="WRONG-001",  # Invalid ID format
            title="Test",
        )
    except Exception as e:
        print(f"✓ Caught validation error for invalid plan ID")
        print(f"  Error: {type(e).__name__}")


# =============================================================================
# 4. CLI Commands
# =============================================================================

def demo_cli():
    """Demonstrate CLI commands."""
    print("\n=== CLI Commands ===\n")
    
    print("Available CLI commands (run with 'ai-dev <command>'):")
    print("  ai-dev health      - Check LLM API health")
    print("  ai-dev models      - List available models")
    print("  ai-dev init-db     - Initialize knowledge database")
    print("  ai-dev new-plan    - Create a new plan artifact")
    print("  ai-dev new-discussion - Create a new discussion artifact")
    print("  ai-dev new-session - Create a new session log")
    print("  ai-dev stats       - Show usage statistics")


# =============================================================================
# Main
# =============================================================================

def main():
    """Run all demos."""
    print("=" * 60)
    print("  AI Dev Orchestrator - Basic Usage Examples")
    print("=" * 60)
    
    demo_knowledge_database()
    demo_llm_service()
    demo_contracts()
    demo_cli()
    
    print("\n" + "=" * 60)
    print("  Demo Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Set XAI_API_KEY to enable LLM calls")
    print("2. Run 'ai-dev init-db' to create your knowledge database")
    print("3. Create discussions and plans with the CLI")
    print("4. Read the ADRs in .adrs/ for architecture details")


if __name__ == "__main__":
    main()
