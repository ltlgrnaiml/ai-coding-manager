#!/usr/bin/env python3
"""Environment detection for cross-platform development.

Detects whether running on Mac (native), Windows (Docker/WSL2), or in container.
Used by scripts and AI assistants to determine appropriate commands.

Per DISC-029: Cross-Platform Development Workflow Strategy.
"""

import os
import platform
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Platform(Enum):
    MAC_NATIVE = "mac-native"
    WIN_DOCKER = "win-docker"
    WIN_WSL = "win-wsl"
    LINUX_NATIVE = "linux-native"
    DOCKER = "docker"
    UNKNOWN = "unknown"


class GPUBackend(Enum):
    CUDA = "cuda"
    MPS = "mps"
    CPU = "cpu"


@dataclass
class Environment:
    """Detected execution environment."""

    platform: Platform
    gpu_backend: GPUBackend
    in_docker: bool
    workspace_root: Path
    hostname: str

    def summary(self) -> str:
        """One-line summary for logging."""
        return f"[{self.platform.value}] GPU:{self.gpu_backend.value} Docker:{self.in_docker}"

    def is_mac(self) -> bool:
        """Check if running on Mac natively."""
        return self.platform == Platform.MAC_NATIVE

    def is_windows(self) -> bool:
        """Check if running on Windows (Docker or WSL)."""
        return self.platform in (Platform.WIN_DOCKER, Platform.WIN_WSL)

    def use_docker_commands(self) -> bool:
        """Check if Docker commands should be used."""
        return self.platform in (Platform.WIN_DOCKER, Platform.DOCKER)

    def get_run_prefix(self) -> str:
        """Get command prefix for running Python scripts."""
        if self.use_docker_commands():
            return "docker exec aidev-backend "
        return ""


def detect_environment() -> Environment:
    """Detect current execution environment."""

    # Check if running in Docker
    in_docker = os.path.exists("/.dockerenv") or os.environ.get(
        "WORKSPACE_ROOT"
    ) == "/workspace"

    # Detect platform
    system = platform.system()
    hostname = platform.node()

    if in_docker:
        plat = Platform.DOCKER
    elif system == "Darwin":
        plat = Platform.MAC_NATIVE
    elif system == "Linux":
        # Check if WSL
        release = platform.release().lower()
        if "microsoft" in release or "wsl" in release:
            plat = Platform.WIN_WSL
        else:
            plat = Platform.LINUX_NATIVE
    elif system == "Windows":
        plat = Platform.WIN_DOCKER  # Assume Docker context on Windows
    else:
        plat = Platform.UNKNOWN

    # Detect GPU backend
    gpu = GPUBackend.CPU
    try:
        import torch

        if torch.cuda.is_available():
            gpu = GPUBackend.CUDA
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            gpu = GPUBackend.MPS
    except ImportError:
        pass

    # Workspace root
    workspace = Path(os.environ.get("WORKSPACE_ROOT", Path.cwd()))

    return Environment(
        platform=plat,
        gpu_backend=gpu,
        in_docker=in_docker,
        workspace_root=workspace,
        hostname=hostname,
    )


# Singleton for caching
_cached_env: Environment | None = None


def get_env() -> Environment:
    """Get cached environment detection result."""
    global _cached_env
    if _cached_env is None:
        _cached_env = detect_environment()
    return _cached_env


def print_env_report() -> None:
    """Print formatted environment report."""
    env = detect_environment()

    print("=" * 50)
    print("AICM Environment Detection")
    print("=" * 50)
    print(f"Platform:      {env.platform.value}")
    print(f"GPU Backend:   {env.gpu_backend.value}")
    print(f"In Docker:     {env.in_docker}")
    print(f"Workspace:     {env.workspace_root}")
    print(f"Hostname:      {env.hostname}")
    print("-" * 50)

    if env.is_mac():
        print("🍎 Mac Native Mode")
        print("   Run backend:  python -m uvicorn backend.main:app --reload --port 8100")
        print("   Run tests:    pytest tests/ -v")
    elif env.use_docker_commands():
        print("🐳 Docker Mode")
        print("   Run backend:  docker compose --profile main up -d")
        print("   Run tests:    docker exec aidev-backend pytest tests/ -v")
    else:
        print("🐧 Linux Native Mode")
        print("   Run backend:  python -m uvicorn backend.main:app --reload --port 8100")
        print("   Run tests:    pytest tests/ -v")

    print("=" * 50)


if __name__ == "__main__":
    print_env_report()
