#!/usr/bin/env python3
"""Standalone archive tool for quick markdown processing.

A simple script to quickly process markdown files from Downloads or custom paths
into the knowledge database for RAG retrieval.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_dev_orchestrator.cli_commands.archive_artifacts import archive

if __name__ == '__main__':
    archive()
