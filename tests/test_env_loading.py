"""Test that .env loading happens correctly.

This test exists because the .env loading bug has occurred multiple times.
It verifies that load_dotenv() is called BEFORE any modules that need env vars.
"""

import ast
import pytest
from pathlib import Path


def test_main_py_loads_dotenv_before_service_imports():
    """Verify load_dotenv() is called before service imports in main.py.
    
    This is a regression test for a recurring bug where env vars weren't
    available when service modules were imported.
    """
    main_py = Path(__file__).parent.parent / "backend" / "main.py"
    content = main_py.read_text()
    
    # Parse the AST to find statement order
    tree = ast.parse(content)
    
    load_dotenv_line = None
    first_backend_import_line = None
    
    for node in ast.walk(tree):
        # Find load_dotenv() call
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "load_dotenv":
                load_dotenv_line = node.lineno
                break
            if isinstance(node.func, ast.Attribute) and node.func.attr == "load_dotenv":
                load_dotenv_line = node.lineno
                break
    
    for node in ast.iter_child_nodes(tree):
        # Find first import from backend.services
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("backend.services"):
                first_backend_import_line = node.lineno
                break
    
    assert load_dotenv_line is not None, "load_dotenv() call not found in main.py"
    assert first_backend_import_line is not None, "No backend.services imports found"
    assert load_dotenv_line < first_backend_import_line, (
        f"CRITICAL: load_dotenv() at line {load_dotenv_line} must come BEFORE "
        f"backend.services imports at line {first_backend_import_line}. "
        f"This causes env vars to be unavailable when services are loaded."
    )


def test_config_py_has_defensive_dotenv():
    """Verify config.py has defensive load_dotenv for import order safety."""
    config_py = Path(__file__).parent.parent / "backend" / "config.py"
    content = config_py.read_text()
    
    assert "load_dotenv" in content, (
        "config.py should have defensive load_dotenv() call to handle "
        "cases where it's imported before main.py"
    )


def test_env_example_exists():
    """Verify .env.example exists as documentation."""
    env_example = Path(__file__).parent.parent / ".env.example"
    assert env_example.exists(), ".env.example must exist"
    
    content = env_example.read_text()
    assert "XAI_API_KEY" in content, ".env.example must document XAI_API_KEY"
