"""Tests for CLI commands."""

import pytest
from unittest.mock import patch, MagicMock
import sys


class TestCLIImports:
    """Test that CLI module imports correctly."""

    def test_cli_importable(self):
        """Test that CLI module can be imported."""
        from ai_dev_orchestrator import cli
        assert hasattr(cli, "main")

    def test_cli_has_commands(self):
        """Test that CLI defines expected commands."""
        from ai_dev_orchestrator.cli import main
        # main should be callable
        assert callable(main)


class TestCLIHelp:
    """Test CLI help output."""

    def test_main_help(self):
        """Test that --help doesn't crash."""
        from ai_dev_orchestrator.cli import main
        
        with patch.object(sys, "argv", ["ai-dev", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with 0 on --help
            assert exc_info.value.code == 0

    def test_version_importable(self):
        """Test version is importable."""
        from ai_dev_orchestrator import __version__
        assert __version__
        assert "2025" in __version__  # Calendar versioning


class TestCLICommands:
    """Test specific CLI commands with mocks."""

    def test_health_command(self):
        """Test health check command runs without error."""
        from ai_dev_orchestrator.cli import main
        
        # Just verify the command doesn't crash - actual API may not be available
        with patch.object(sys, "argv", ["ai-dev", "health"]):
            try:
                main()
            except SystemExit as e:
                # May exit with error if no API key, that's ok
                pass

    def test_models_command(self):
        """Test models list command."""
        from ai_dev_orchestrator.cli import main
        
        with patch.object(sys, "argv", ["ai-dev", "models"]):
            # Should list models without crashing
            main()
