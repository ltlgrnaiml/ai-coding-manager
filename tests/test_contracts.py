"""Tests for contract schemas (Pydantic validation)."""

import pytest
from datetime import date

from contracts.plan_schema import (
    PlanSchema,
    PlanStatus,
    GranularityLevel,
    Milestone,
    MilestoneStatus,
    Task,
    TaskStatus,
    AcceptanceCriterion,
    ACStatus,
)
from contracts.adr_schema import ADRSchema, Guardrail, AlternativeConsidered
from contracts.discussion_schema import (
    DiscussionSchema,
    DiscussionStatus,
    OpenQuestion,
    QuestionStatus,
    FunctionalRequirement,
)


class TestPlanSchema:
    """Tests for Plan contract validation."""

    def test_minimal_plan_creation(self):
        """Test creating a plan with minimal required fields."""
        plan = PlanSchema(
            id="PLAN-001",
            title="Test Plan for Feature X",
            status=PlanStatus.DRAFT,
            created_date="2025-12-31",
            updated_date="2025-12-31",
            author="Test Author",
            summary="Test plan summary",
            objective="Test objective",
        )
        assert plan.id == "PLAN-001"
        assert plan.status == PlanStatus.DRAFT
        assert plan.granularity == GranularityLevel.L1_STANDARD

    def test_plan_with_milestones(self):
        """Test creating a plan with milestones and tasks."""
        task = Task(
            id="T-M1-01",
            title="Implement the feature",
            description="Detailed description of the task",
            status=TaskStatus.PENDING,
            verification_command="pytest tests/ -v",
        )
        milestone = Milestone(
            id="M1",
            name="First Milestone",
            title="First Milestone",
            objective="Complete the first milestone",
            status=MilestoneStatus.PENDING,
            tasks=[task],
        )
        plan = PlanSchema(
            id="PLAN-002",
            title="Complete Plan with Milestones",
            created_date="2025-12-31",
            updated_date="2025-12-31",
            author="Test Author",
            summary="Test plan summary",
            objective="Test objective",
            milestones=[milestone],
        )
        assert len(plan.milestones) == 1
        assert plan.milestones[0].tasks[0].id == "T-M1-01"

    def test_plan_id_validation(self):
        """Test that plan ID must start with PLAN-."""
        with pytest.raises(ValueError):
            PlanSchema(
                id="WRONG-001",
                title="Invalid Plan ID Test",
            )

    def test_granularity_levels(self):
        """Test all granularity levels are valid."""
        for level in GranularityLevel:
            plan = PlanSchema(
                id="PLAN-003",
                title="Granularity Test Plan",
                created_date="2025-12-31",
                updated_date="2025-12-31",
                author="Test Author",
                summary="Test plan summary",
                objective="Test objective",
                granularity=level,
            )
            assert plan.granularity == level


class TestADRSchema:
    """Tests for ADR contract validation."""

    def test_minimal_adr_creation(self):
        """Test creating an ADR with minimal required fields."""
        adr = ADRSchema(
            id="ADR-0001_test-adr",
            title="Test Architecture Decision",
            status="active",
            date="2025-12-31",
            author="Test Author",
            scope="core",
            context="This is the background and problem statement for the ADR that needs to be at least 50 characters.",
            decision_primary="We will implement this decision because it provides the best solution for our needs and requirements.",
        )
        assert adr.id == "ADR-0001_test-adr"
        assert adr.status == "active"

    def test_adr_id_validation(self):
        """Test that ADR ID must start with ADR-."""
        with pytest.raises(ValueError):
            ADRSchema(
                id="WRONG-0001",
                title="Invalid ADR ID Test",
                status="active",
                date="2025-12-31",
                author="Test",
                scope="core",
                context="x" * 50,
                decision_primary="x" * 50,
            )

    def test_adr_date_validation(self):
        """Test that date must be in YYYY-MM-DD format."""
        with pytest.raises(ValueError):
            ADRSchema(
                id="ADR-0001_test",
                title="Date Format Test",
                status="active",
                date="12-31-2025",  # Wrong format
                author="Test",
                scope="core",
                context="x" * 50,
                decision_primary="x" * 50,
            )

    def test_adr_with_guardrails(self):
        """Test ADR with guardrails."""
        guardrail = Guardrail(
            id="GR-001",
            rule="All API calls must be logged",
            enforcement="CI validation",
            scope="api",
        )
        adr = ADRSchema(
            id="ADR-0002_guardrails",
            title="ADR with Guardrails Test",
            status="active",
            date="2025-12-31",
            author="Test",
            scope="core",
            context="x" * 50,
            decision_primary="x" * 50,
            guardrails=[guardrail],
        )
        assert len(adr.guardrails) == 1
        assert adr.guardrails[0].id == "GR-001"


class TestDiscussionSchema:
    """Tests for Discussion contract validation."""

    def test_minimal_discussion_creation(self):
        """Test creating a discussion with minimal fields."""
        disc = DiscussionSchema(
            id="DISC-001",
            title="Test Discussion",
            created_date="2025-12-31",
            updated_date="2025-12-31",
            author="Test Author",
            summary="This is a test discussion about a new feature.",
        )
        assert disc.id == "DISC-001"
        assert disc.status == DiscussionStatus.DRAFT

    def test_discussion_id_validation(self):
        """Test that discussion ID must start with DISC-."""
        with pytest.raises(ValueError):
            DiscussionSchema(
                id="WRONG-001",
                title="Invalid Discussion ID",
                created_date="2025-12-31",
                updated_date="2025-12-31",
                author="Test",
                summary="Test summary",
            )

    def test_discussion_with_open_questions(self):
        """Test discussion with open questions."""
        question = OpenQuestion(
            id="Q-1",
            question="Should we use REST or GraphQL?",
            status=QuestionStatus.OPEN,
        )
        disc = DiscussionSchema(
            id="DISC-002",
            title="API Design Discussion",
            created_date="2025-12-31",
            updated_date="2025-12-31",
            author="Test",
            summary="Discussing API design choices",
            open_questions=[question],
        )
        assert len(disc.open_questions) == 1
        assert disc.open_questions[0].status == QuestionStatus.OPEN

    def test_functional_requirement_id_validation(self):
        """Test that FR IDs must start with FR-."""
        with pytest.raises(ValueError):
            FunctionalRequirement(
                id="WRONG-1",
                description="Invalid requirement",
            )


class TestContractIntegrity:
    """Tests for contract integrity and interoperability."""

    def test_all_contracts_have_version(self):
        """Verify all contract modules have __version__."""
        from contracts import plan_schema, adr_schema, discussion_schema
        from contracts.knowledge import archive, search, rag
        
        assert hasattr(plan_schema, "__version__")
        assert hasattr(adr_schema, "__version__")
        assert hasattr(discussion_schema, "__version__")
        assert hasattr(archive, "__version__")
        assert hasattr(search, "__version__")
        assert hasattr(rag, "__version__")

    def test_status_enums_consistent(self):
        """Test that status enums follow consistent patterns."""
        # All should have PENDING/IN_PROGRESS states
        assert hasattr(TaskStatus, "PENDING")
        assert hasattr(TaskStatus, "IN_PROGRESS")
        assert hasattr(MilestoneStatus, "PENDING")
        assert hasattr(MilestoneStatus, "IN_PROGRESS")
