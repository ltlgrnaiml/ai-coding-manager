"""Plan Manager - Create and manage execution plans.

Supports L1/L2/L3 plan granularity levels for different AI model capabilities.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


PLANS_DIR = Path(".plans")


def get_next_plan_id() -> str:
    """Get the next available plan ID.
    
    Returns:
        Next plan ID in format PLAN-XXX.
    """
    PLANS_DIR.mkdir(exist_ok=True)
    
    existing = list(PLANS_DIR.glob("PLAN-*.json"))
    if not existing:
        return "PLAN-001"
    
    # Extract numbers and find max
    numbers = []
    for f in existing:
        match = re.search(r'PLAN-(\d+)', f.stem)
        if match:
            numbers.append(int(match.group(1)))
    
    next_num = max(numbers) + 1 if numbers else 1
    return f"PLAN-{next_num:03d}"


def create_plan(
    title: str,
    objective: str,
    granularity: str = "L1",
    milestones: list[dict[str, Any]] | None = None,
) -> dict:
    """Create a new plan.
    
    Args:
        title: Plan title.
        objective: Plan objective/goal.
        granularity: Plan granularity level (L1, L2, L3).
        milestones: Optional list of milestones.
        
    Returns:
        Plan dictionary.
    """
    plan_id = get_next_plan_id()
    
    plan = {
        "id": plan_id,
        "title": title,
        "status": "draft",
        "granularity": granularity,
        "objective": objective,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "milestones": milestones or [],
        "acceptance_criteria": [],
        "context": [],
    }
    
    # Add L2/L3 specific fields
    if granularity in ("L2", "L3"):
        plan["constraints"] = []
        plan["existing_patterns"] = []
    
    if granularity == "L3":
        plan["steps"] = []
    
    # Save plan
    save_plan(plan)
    
    return plan


def load_plan(plan_id: str) -> dict | None:
    """Load a plan by ID.
    
    Args:
        plan_id: Plan ID (e.g., PLAN-001).
        
    Returns:
        Plan dictionary or None if not found.
    """
    # Try JSON first
    json_path = PLANS_DIR / f"{plan_id}.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Try with title suffix
    for path in PLANS_DIR.glob(f"{plan_id}*.json"):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return None


def save_plan(plan: dict) -> Path:
    """Save a plan to disk.
    
    Args:
        plan: Plan dictionary.
        
    Returns:
        Path to saved file.
    """
    PLANS_DIR.mkdir(exist_ok=True)
    
    # Update timestamp
    plan["updated_at"] = datetime.utcnow().isoformat()
    
    # Create filename
    title_slug = re.sub(r'[^a-zA-Z0-9]+', '-', plan.get("title", ""))[:30]
    filename = f"{plan['id']}_{title_slug}.json"
    path = PLANS_DIR / filename
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
    
    return path


def list_plans() -> list[dict]:
    """List all plans.
    
    Returns:
        List of plan summaries.
    """
    PLANS_DIR.mkdir(exist_ok=True)
    
    plans = []
    for path in sorted(PLANS_DIR.glob("PLAN-*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                plan = json.load(f)
                plans.append({
                    "id": plan.get("id"),
                    "title": plan.get("title"),
                    "status": plan.get("status"),
                    "granularity": plan.get("granularity"),
                })
        except Exception:
            continue
    
    return plans
