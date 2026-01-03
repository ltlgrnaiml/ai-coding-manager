"""AI Knowledge Hub (AIKH) Configuration.

Centralized configuration for AIKH databases and GPU acceleration.
Supports cross-platform deployment: macOS (M4 Max/MPS), Windows/Linux (CUDA).
"""

import os
import sys
import json
from pathlib import Path
from typing import Literal, Optional
from dataclasses import dataclass


# =============================================================================
# AIKH Path Configuration
# =============================================================================

def get_aikh_home() -> Path:
    """Get the AIKH home directory.
    
    Priority:
    1. AIKH_HOME environment variable
    2. Docker path (/aikh) if it exists
    3. User home ~/.aikh/
    
    Returns:
        Path to AIKH home directory.
    """
    # Check environment variable first
    env_home = os.environ.get("AIKH_HOME")
    if env_home:
        return Path(env_home)
    
    # Check for Docker mount
    docker_path = Path("/aikh")
    if docker_path.exists():
        return docker_path
    
    # Default to user home
    return Path.home() / ".aikh"


def ensure_aikh_home() -> Path:
    """Ensure AIKH home directory exists and return path."""
    aikh_home = get_aikh_home()
    aikh_home.mkdir(parents=True, exist_ok=True)
    return aikh_home


# Database paths
AIKH_HOME = get_aikh_home()
ARTIFACTS_DB_PATH = AIKH_HOME / "artifacts.db"
CHATLOGS_DB_PATH = AIKH_HOME / "chatlogs.db"
RESEARCH_DB_PATH = AIKH_HOME / "research.db"


# =============================================================================
# GPU/ML Configuration
# =============================================================================

DeviceType = Literal["cuda", "mps", "cpu"]


@dataclass
class GPUConfig:
    """GPU configuration for ML operations."""
    device: DeviceType
    device_name: str
    framework: str
    is_available: bool
    memory_gb: Optional[float] = None


def detect_gpu_device() -> GPUConfig:
    """Detect the best available GPU device for ML operations.
    
    Priority:
    1. CUDA (NVIDIA GPUs) - Windows/Linux with RTX 5090
    2. MPS (Metal) - macOS with Apple Silicon M4 Max
    3. CPU fallback
    
    Returns:
        GPUConfig with detected device information.
    """
    # Try CUDA first (NVIDIA)
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            return GPUConfig(
                device="cuda",
                device_name=device_name,
                framework="CUDA/cuDNN",
                is_available=True,
                memory_gb=memory_gb
            )
    except ImportError:
        pass
    
    # Try MPS (Apple Silicon)
    try:
        import torch
        if torch.backends.mps.is_available():
            return GPUConfig(
                device="mps",
                device_name="Apple Silicon (Metal Performance Shaders)",
                framework="MPS",
                is_available=True,
                memory_gb=None  # MPS shares unified memory
            )
    except (ImportError, AttributeError):
        pass
    
    # CPU fallback
    return GPUConfig(
        device="cpu",
        device_name="CPU",
        framework="CPU",
        is_available=True,
        memory_gb=None
    )


def get_torch_device() -> str:
    """Get the PyTorch device string for the best available accelerator.
    
    Returns:
        Device string: 'cuda', 'mps', or 'cpu'
    """
    config = detect_gpu_device()
    return config.device


def get_embedding_device() -> str:
    """Get the device for embedding model inference.
    
    For sentence-transformers and similar models.
    
    Returns:
        Device string compatible with sentence-transformers.
    """
    config = detect_gpu_device()
    
    # sentence-transformers uses 'cuda' or 'cpu'
    # For MPS, we return 'mps' which newer versions support
    if config.device == "cuda":
        return "cuda"
    elif config.device == "mps":
        return "mps"
    return "cpu"


# =============================================================================
# Configuration Loading
# =============================================================================

def load_aikh_config() -> dict:
    """Load AIKH configuration from config.json if it exists."""
    config_path = AIKH_HOME / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}


def get_database_path(db_name: Literal["artifacts", "chatlogs", "research"]) -> Path:
    """Get the path for a specific AIKH database.
    
    Args:
        db_name: One of 'artifacts', 'chatlogs', or 'research'
        
    Returns:
        Path to the database file.
    """
    ensure_aikh_home()
    
    paths = {
        "artifacts": ARTIFACTS_DB_PATH,
        "chatlogs": CHATLOGS_DB_PATH,
        "research": RESEARCH_DB_PATH,
    }
    return paths[db_name]


# =============================================================================
# Diagnostic Functions
# =============================================================================

def print_aikh_status():
    """Print AIKH configuration status for diagnostics."""
    print("=" * 60)
    print("AI Knowledge Hub (AIKH) Status")
    print("=" * 60)
    
    # Paths
    print(f"\nAIKH Home: {AIKH_HOME}")
    print(f"  Artifacts DB: {ARTIFACTS_DB_PATH} (exists: {ARTIFACTS_DB_PATH.exists()})")
    print(f"  Chatlogs DB:  {CHATLOGS_DB_PATH} (exists: {CHATLOGS_DB_PATH.exists()})")
    print(f"  Research DB:  {RESEARCH_DB_PATH} (exists: {RESEARCH_DB_PATH.exists()})")
    
    # GPU
    gpu = detect_gpu_device()
    print(f"\nGPU Configuration:")
    print(f"  Device: {gpu.device}")
    print(f"  Name: {gpu.device_name}")
    print(f"  Framework: {gpu.framework}")
    print(f"  Available: {gpu.is_available}")
    if gpu.memory_gb:
        print(f"  Memory: {gpu.memory_gb:.1f} GB")
    
    # Platform
    print(f"\nPlatform: {sys.platform}")
    print("=" * 60)


if __name__ == "__main__":
    print_aikh_status()
