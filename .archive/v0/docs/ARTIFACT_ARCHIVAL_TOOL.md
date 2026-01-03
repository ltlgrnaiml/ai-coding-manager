# Artifact Archival Tool - RAW CHAT RECORDS Integration

## Overview

The Artifact Archival Tool provides comprehensive processing of markdown files, with specialized support for RAW CHAT RECORDS from Cascade downloads. It integrates seamlessly with the document viewer interface to support DISC conversation logs and manual document creation workflows.

## Features

### 🤖 AI-Powered Processing
- **Metadata Extraction**: Automatically extracts title, document type, tags, and summary
- **Chat Record Analysis**: Specialized parsing for Cascade conversation logs
- **Conversation Insights**: Extracts topics, key insights, action items, and decisions
- **DISC Integration**: Generates conversation log entries compatible with DISC schema

### 📁 File Processing
- **Batch Processing**: Process entire directories or Downloads folder
- **Format Detection**: Supports Cascade markdown, JSON, and plain text formats
- **Smart Chunking**: RAG-optimized chunking with overlap for better retrieval
- **Vector Embeddings**: Automatic embedding generation for semantic search

### 🔍 RAG Integration
- **Knowledge Archive**: Full integration with existing RAG system
- **Hybrid Search**: Combines full-text and vector similarity search
- **Enhanced Retrieval**: Multi-level context building with LLM re-ranking

## Usage

### Command Line Interface

#### Process Downloads Folder
```bash
# Process all markdown files in Downloads
ai-dev archive downloads

# With verbose output
ai-dev archive downloads --verbose

# Custom Downloads path
ai-dev archive downloads -d /path/to/downloads

# Initialize database first
ai-dev archive downloads --init-db
```

#### Process Specific Files
```bash
# Process individual files
ai-dev archive files document.md chat-record.md

# Process with verbose output
ai-dev archive files *.md --verbose
```

#### Process Directory
```bash
# Process directory
ai-dev archive directory /path/to/docs

# Recursive processing
ai-dev archive directory /path/to/docs --recursive

# Custom file pattern
ai-dev archive directory /path/to/docs -p "*.txt"
```

#### Check Status
```bash
# Basic status
ai-dev archive status

# Detailed statistics
ai-dev archive status --verbose
```

### Standalone Script
```bash
# Direct script execution
./scripts/archive_tool.py downloads --verbose
```

### Python API

#### Basic Processing
```python
from ai_dev_orchestrator.knowledge.artifact_processor import create_processor

processor = create_processor()
result = processor.process_file(Path("chat-record.md"))

if result.success:
    print(f"Processed: {result.chunks_created} chunks, {result.embeddings_created} embeddings")
    if result.chat_session:
        print(f"Chat: {result.chat_session.total_messages} messages")
```

#### Chat Record Analysis
```python
from ai_dev_orchestrator.knowledge.chat_record_parser import parse_chat_file

session, insights, disc_entry = parse_chat_file(Path("cascade-chat.md"))

print(f"Topics: {insights.topics_discussed}")
print(f"Action Items: {insights.action_items}")
print(f"DISC Entry: {disc_entry.date}")
```

## Document Viewer Integration

### Chat Record Detection
The system automatically detects chat records based on:
- **Filename patterns**: `chat`, `conversation`, `cascade`, `session`, `dialogue`, `transcript`
- **Content patterns**: `user:`, `assistant:`, `human:`, `ai:`, `claude:`

### Specialized Viewer
When a chat record is detected, the document viewer displays:

#### Overview Tab
- Conversation summary
- Topics discussed (as tags)
- Key insights with bullet points
- Action items as checkboxes
- Decisions made

#### Messages Tab
- Full conversation with role indicators
- User/Assistant message distinction
- Timestamp display (if available)
- Message count statistics

#### Copy Snippets Tab
- **Summary**: Ready-to-paste summary text
- **Requirements**: Extracted user requirements
- **Technical Concepts**: Mentioned technologies/concepts
- **Action Items**: Formatted as checkboxes
- **Decisions**: Key decisions made
- **Conversation Excerpt**: Truncated conversation for reference

#### DISC Entry Tab
- JSON-formatted conversation log entry
- Compatible with DISC schema `conversation_log` field
- One-click copy for manual document creation

## DISC Schema Integration

### Conversation Log Entry Format
```json
{
  "date": "2026-01-01",
  "session_id": "cascade-session-123",
  "topics_discussed": [
    "frontend migration",
    "component architecture",
    "user experience"
  ],
  "key_insights": [
    "Current components need refactoring",
    "User feedback indicates confusion",
    "Performance improvements needed"
  ],
  "action_items": [
    "Create migration plan",
    "Update component library",
    "Conduct user testing"
  ]
}
```

### Manual Document Creation Workflow

1. **Process Chat Record**: Use archive tool to process Cascade download
2. **View in Interface**: Open processed file in document viewer
3. **Extract Insights**: Review Overview tab for key information
4. **Copy Snippets**: Use Copy Snippets tab for manual document creation
5. **DISC Integration**: Copy DISC entry JSON for conversation log field

## File Format Support

### Cascade Markdown Format
```markdown
# Conversation: Feature Discussion

User: I need to implement a new feature for user management.
