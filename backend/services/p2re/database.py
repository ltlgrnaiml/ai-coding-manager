"""P2RE Database Schema and Initialization.

Prompts to Response Ecosystem (P2RE) - Trace Store
Separate SQLite database for LLM interaction observability.

Stores:
- Traces: Individual LLM calls with full context
- Prompt Templates: Reusable prompt patterns with versions
- Evaluations: Response quality metrics and feedback
- Sessions: Conversation groupings for traces
"""

import os
import sqlite3
from pathlib import Path

# P2RE database path - separate from artifacts.db
AIKH_DIR = Path(os.getenv("AIKH_DIR", Path.home() / ".aikh"))
P2RE_DB_PATH = AIKH_DIR / "p2re.db"

SCHEMA = """
-- =============================================================================
-- Traces: Individual LLM API calls
-- =============================================================================
CREATE TABLE IF NOT EXISTS traces (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    parent_trace_id TEXT,
    
    -- Request details
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    request_timestamp TEXT NOT NULL,
    
    -- Prompt content
    system_prompt TEXT,
    user_prompt TEXT NOT NULL,
    prompt_template_id TEXT,
    prompt_variables TEXT,  -- JSON dict of template variables
    
    -- Full messages (for multi-turn)
    messages TEXT,  -- JSON array of {role, content}
    
    -- Response
    response_timestamp TEXT,
    response_content TEXT,
    response_role TEXT DEFAULT 'assistant',
    finish_reason TEXT,
    
    -- Tool calls (if any)
    tool_calls TEXT,  -- JSON array of tool call objects
    tool_results TEXT,  -- JSON array of tool results
    
    -- Metrics
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    latency_ms INTEGER,
    cost_usd REAL DEFAULT 0.0,
    
    -- Status
    status TEXT DEFAULT 'success',  -- success, error, timeout, cancelled
    error_message TEXT,
    error_type TEXT,
    
    -- Context
    source_file TEXT,  -- Which code file initiated this call
    source_function TEXT,
    tags TEXT,  -- JSON array of tags
    metadata TEXT,  -- JSON object for extensibility
    
    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    
    FOREIGN KEY (prompt_template_id) REFERENCES prompt_templates(id),
    FOREIGN KEY (parent_trace_id) REFERENCES traces(id)
);

-- =============================================================================
-- Prompt Templates: Reusable prompt patterns
-- =============================================================================
CREATE TABLE IF NOT EXISTS prompt_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,  -- system, task, extraction, generation, etc.
    
    -- Template content
    system_template TEXT,
    user_template TEXT,
    
    -- Variables schema
    variables_schema TEXT,  -- JSON schema for template variables
    
    -- Versioning
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT 1,
    
    -- Metrics (aggregated)
    usage_count INTEGER DEFAULT 0,
    avg_tokens_in REAL DEFAULT 0,
    avg_tokens_out REAL DEFAULT 0,
    avg_latency_ms REAL DEFAULT 0,
    avg_quality_score REAL,
    
    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- Prompt Template Versions: Version history
-- =============================================================================
CREATE TABLE IF NOT EXISTS prompt_template_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    
    system_template TEXT,
    user_template TEXT,
    variables_schema TEXT,
    
    change_notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    created_by TEXT,
    
    FOREIGN KEY (template_id) REFERENCES prompt_templates(id),
    UNIQUE(template_id, version)
);

-- =============================================================================
-- Evaluations: Response quality metrics
-- =============================================================================
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL,
    
    -- Evaluation type
    eval_type TEXT NOT NULL,  -- human, auto, llm_judge
    evaluator TEXT,  -- human ID or model name
    
    -- Scores (0.0 - 1.0 normalized)
    overall_score REAL,
    relevance_score REAL,
    accuracy_score REAL,
    helpfulness_score REAL,
    safety_score REAL,
    
    -- Detailed feedback
    feedback_text TEXT,
    issues TEXT,  -- JSON array of issue tags
    
    -- For A/B testing
    experiment_id TEXT,
    variant TEXT,
    
    created_at TEXT DEFAULT (datetime('now')),
    
    FOREIGN KEY (trace_id) REFERENCES traces(id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

-- =============================================================================
-- Experiments: A/B testing for prompts
-- =============================================================================
CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft',  -- draft, running, paused, completed
    
    -- Variants
    variants TEXT NOT NULL,  -- JSON array of {id, name, template_id, weight}
    
    -- Targeting
    target_percentage REAL DEFAULT 100.0,
    target_filters TEXT,  -- JSON filters for targeting
    
    -- Results
    started_at TEXT,
    ended_at TEXT,
    winner_variant TEXT,
    
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- Trace Sessions: Group related traces
-- =============================================================================
CREATE TABLE IF NOT EXISTS trace_sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    
    -- Aggregated metrics
    trace_count INTEGER DEFAULT 0,
    total_tokens_in INTEGER DEFAULT 0,
    total_tokens_out INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    avg_latency_ms REAL,
    
    -- Context
    source TEXT,  -- chat, api, batch, etc.
    user_id TEXT,
    metadata TEXT,  -- JSON
    
    first_trace_at TEXT,
    last_trace_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- Daily Rollups: Aggregated statistics
-- =============================================================================
CREATE TABLE IF NOT EXISTS daily_rollups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    
    -- Counts
    trace_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    
    -- Token metrics
    total_tokens_in INTEGER DEFAULT 0,
    total_tokens_out INTEGER DEFAULT 0,
    
    -- Cost
    total_cost_usd REAL DEFAULT 0.0,
    
    -- Latency (percentiles in ms)
    latency_p50 INTEGER,
    latency_p90 INTEGER,
    latency_p99 INTEGER,
    
    -- Quality (if evaluations exist)
    avg_quality_score REAL,
    
    created_at TEXT DEFAULT (datetime('now')),
    
    UNIQUE(date, provider, model)
);

-- =============================================================================
-- Model Registry: Providers
-- =============================================================================
CREATE TABLE IF NOT EXISTS providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    api_base_url TEXT,
    auth_type TEXT DEFAULT 'api_key',
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- Model Registry: Models (SSoT for all AI models)
-- =============================================================================
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    name TEXT NOT NULL,
    family TEXT,
    category TEXT,
    
    -- Context & Limits
    context_window INTEGER,
    max_output_tokens INTEGER,
    
    -- Pricing (per 1M tokens, in USD)
    input_price_per_mtok REAL,
    output_price_per_mtok REAL,
    cache_read_price_per_mtok REAL,
    cache_write_price_per_mtok REAL,
    batch_input_price_per_mtok REAL,
    batch_output_price_per_mtok REAL,
    
    -- Capabilities (boolean flags stored as INTEGER 0/1)
    supports_streaming INTEGER DEFAULT 1,
    supports_tools INTEGER DEFAULT 0,
    supports_vision INTEGER DEFAULT 0,
    supports_audio INTEGER DEFAULT 0,
    supports_video INTEGER DEFAULT 0,
    supports_code_execution INTEGER DEFAULT 0,
    supports_web_search INTEGER DEFAULT 0,
    supports_caching INTEGER DEFAULT 0,
    supports_batch INTEGER DEFAULT 0,
    supports_reasoning INTEGER DEFAULT 0,
    supports_json_mode INTEGER DEFAULT 0,
    supports_mcp INTEGER DEFAULT 0,
    
    -- Metadata
    release_date TEXT,
    deprecation_date TEXT,
    status TEXT DEFAULT 'active',
    notes TEXT,
    
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

-- =============================================================================
-- Model Registry: Tools (provider-specific tools with pricing)
-- =============================================================================
CREATE TABLE IF NOT EXISTS model_tools (
    id TEXT PRIMARY KEY,
    provider_id TEXT,
    name TEXT NOT NULL,
    display_name TEXT,
    description TEXT,
    
    -- Pricing
    price_per_use REAL,
    price_per_1k_uses REAL,
    token_overhead INTEGER DEFAULT 0,
    
    -- Availability
    models_supported TEXT,  -- JSON array of model IDs
    free_tier_limit INTEGER,
    
    -- Tool schema for invocation
    parameters_schema TEXT,  -- JSON schema
    
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now')),
    
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

-- =============================================================================
-- Model Registry: MCP Servers (external tool servers)
-- =============================================================================
CREATE TABLE IF NOT EXISTS mcp_servers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    
    -- Connection
    server_type TEXT,  -- 'stdio', 'sse', 'http'
    command TEXT,      -- For stdio servers
    url TEXT,          -- For http/sse servers
    
    -- Status
    status TEXT DEFAULT 'active',
    last_connected_at TEXT,
    
    -- Discovered tools (cached)
    tools_json TEXT,  -- JSON array of tool definitions
    resources_json TEXT,  -- JSON array of resources
    
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- Model Registry: Routing Rules (deterministic model selection)
-- =============================================================================
CREATE TABLE IF NOT EXISTS routing_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    
    -- Conditions (JSON)
    conditions TEXT,  -- {"task_type": "code", "context_gt": 100000}
    
    -- Action
    model_id TEXT,
    fallback_model_id TEXT,
    
    enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    
    FOREIGN KEY (model_id) REFERENCES models(id),
    FOREIGN KEY (fallback_model_id) REFERENCES models(id)
);

-- =============================================================================
-- Model Registry: Pricing History
-- =============================================================================
CREATE TABLE IF NOT EXISTS pricing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL,
    input_price REAL,
    output_price REAL,
    recorded_at TEXT DEFAULT (datetime('now')),
    source TEXT,
    
    FOREIGN KEY (model_id) REFERENCES models(id)
);

-- =============================================================================
-- Indexes
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_traces_session ON traces(session_id);
CREATE INDEX IF NOT EXISTS idx_traces_provider_model ON traces(provider, model);
CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON traces(request_timestamp);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
CREATE INDEX IF NOT EXISTS idx_traces_template ON traces(prompt_template_id);

CREATE INDEX IF NOT EXISTS idx_evaluations_trace ON evaluations(trace_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_experiment ON evaluations(experiment_id);

CREATE INDEX IF NOT EXISTS idx_daily_rollups_date ON daily_rollups(date);
CREATE INDEX IF NOT EXISTS idx_daily_rollups_provider ON daily_rollups(provider, model);

CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider_id);
CREATE INDEX IF NOT EXISTS idx_models_status ON models(status);
CREATE INDEX IF NOT EXISTS idx_model_tools_provider ON model_tools(provider_id);
CREATE INDEX IF NOT EXISTS idx_pricing_history_model ON pricing_history(model_id);

-- =============================================================================
-- Triggers
-- =============================================================================

-- Update trace_sessions on new trace
CREATE TRIGGER IF NOT EXISTS update_session_on_trace_insert
AFTER INSERT ON traces
WHEN NEW.session_id IS NOT NULL
BEGIN
    UPDATE trace_sessions SET
        trace_count = trace_count + 1,
        total_tokens_in = total_tokens_in + COALESCE(NEW.tokens_in, 0),
        total_tokens_out = total_tokens_out + COALESCE(NEW.tokens_out, 0),
        total_cost_usd = total_cost_usd + COALESCE(NEW.cost_usd, 0),
        last_trace_at = NEW.request_timestamp,
        updated_at = datetime('now')
    WHERE id = NEW.session_id;
END;

-- Update prompt_template usage count
CREATE TRIGGER IF NOT EXISTS update_template_usage
AFTER INSERT ON traces
WHEN NEW.prompt_template_id IS NOT NULL
BEGIN
    UPDATE prompt_templates SET
        usage_count = usage_count + 1,
        updated_at = datetime('now')
    WHERE id = NEW.prompt_template_id;
END;
"""


def get_database_path() -> Path:
    """Get the P2RE database path, creating directory if needed."""
    AIKH_DIR.mkdir(parents=True, exist_ok=True)
    return P2RE_DB_PATH


def init_database() -> sqlite3.Connection:
    """Initialize the P2RE database with schema."""
    db_path = get_database_path()
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def get_connection() -> sqlite3.Connection:
    """Get a connection to the P2RE database."""
    db_path = get_database_path()
    if not db_path.exists():
        return init_database()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn
