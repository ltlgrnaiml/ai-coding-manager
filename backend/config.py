"""AICM Configuration - Single Source of Truth for ports and settings.

All port and host configuration should be read from here.
Values come from environment variables with sensible defaults.

IMPORTANT: This module loads .env defensively to ensure env vars are available
even if this module is imported before main.py runs load_dotenv().
"""

import os
from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel

# Defensive .env loading - ensures env vars are available regardless of import order
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # dotenv not installed, rely on system env vars


class PortConfig(BaseModel):
    """Port configuration for all AICM services."""
    backend: int = 8100
    frontend: int = 3100
    phoenix: int = 6006
    phoenix_grpc: int = 4317


class Config(BaseModel):
    """AICM Configuration."""
    ports: PortConfig
    
    @property
    def backend_url(self) -> str:
        return f"http://localhost:{self.ports.backend}"
    
    @property
    def frontend_url(self) -> str:
        return f"http://localhost:{self.ports.frontend}"
    
    @property
    def phoenix_url(self) -> str:
        return f"http://localhost:{self.ports.phoenix}"
    
    @property
    def phoenix_grpc_url(self) -> str:
        return f"http://localhost:{self.ports.phoenix_grpc}"


@lru_cache()
def get_config() -> Config:
    """Get configuration from environment variables."""
    return Config(
        ports=PortConfig(
            backend=int(os.getenv("AICM_BACKEND_PORT", "8100")),
            frontend=int(os.getenv("AICM_FRONTEND_PORT", "3100")),
            phoenix=int(os.getenv("AICM_PHOENIX_PORT", "6006")),
            phoenix_grpc=int(os.getenv("AICM_PHOENIX_GRPC_PORT", "4317")),
        )
    )


# Convenience exports
def get_backend_port() -> int:
    return get_config().ports.backend

def get_frontend_port() -> int:
    return get_config().ports.frontend

def get_phoenix_port() -> int:
    return get_config().ports.phoenix

def get_phoenix_grpc_port() -> int:
    return get_config().ports.phoenix_grpc
