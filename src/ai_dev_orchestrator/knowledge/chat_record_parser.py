"""Chat Record Parser - Process RAW CHAT RECORDS from Cascade downloads.

Specialized parser for Cascade conversation logs that can:
- Extract conversation structure (user/assistant exchanges)
- Identify key topics, decisions, and action items
- Generate DISC conversation log entries
- Provide contextual snippets for manual document creation
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai_dev_orchestrator.llm.service import generate_structured, is_available
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single message in a chat conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None
    message_id: Optional[str] = None


@dataclass
class ChatSession:
    """A parsed chat session from Cascade."""
    session_id: str
    title: str
    date: str
    messages: List[ChatMessage] = field(default_factory=list)
    total_messages: int = 0
    user_messages: int = 0
    assistant_messages: int = 0


@dataclass
class ConversationInsights:
    """Extracted insights from a chat conversation."""
    topics_discussed: List[str] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    decisions_made: List[str] = field(default_factory=list)
    technical_concepts: List[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class DiscConversationLogEntry:
    """DISC-compatible conversation log entry."""
    date: str
    session_id: Optional[str]
    topics_discussed: List[str]
    key_insights: List[str]
    action_items: List[str]


class ChatRecordParser:
    """Parser for Cascade chat records and conversation logs."""
    
    class ConversationAnalysis(BaseModel):
        """Pydantic model for AI-powered conversation analysis."""
        topics_discussed: List[str]
        key_insights: List[str]
        action_items: List[str]
        decisions_made: List[str]
        technical_concepts: List[str]
        summary: str
    
    def __init__(self):
        """Initialize chat record parser."""
        self.cascade_patterns = {
            'session_start': r'(?:Session|Conversation) (?:ID|#):\s*([^\n]+)',
            'timestamp': r'(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)',
            'user_message': r'(?:^|\n)(?:User|Human|You):\s*(.*?)(?=\n(?:Assistant|AI|Claude|Cascade):|$)',
            'assistant_message': r'(?:^|\n)(?:Assistant|AI|Claude|Cascade):\s*(.*?)(?=\n(?:User|Human|You):|$)',
            'message_separator': r'\n(?:---+|===+|\*\*\*+)\n',
        }
    
    def detect_format(self, content: str) -> str:
        """Detect the format of the chat record.
        
        Args:
            content: Raw content of the chat record.
            
        Returns:
            Format type: 'cascade_markdown', 'cascade_json', 'plain_text', or 'unknown'
        """
        content_lower = content.lower().strip()
        
        # Check for JSON format
        if content.strip().startswith('{') and content.strip().endswith('}'):
            try:
                json.loads(content)
                return 'cascade_json'
            except json.JSONDecodeError:
                pass
        
        # Check for Cascade markdown patterns
        cascade_indicators = [
            'user:', 'assistant:', 'human:', 'ai:', 'claude:', 'cascade:',
            'session id:', 'conversation id:', '# conversation'
        ]
        
        if any(indicator in content_lower for indicator in cascade_indicators):
            return 'cascade_markdown'
        
        # Check for plain conversation text
        if re.search(r'(?:^|\n)[A-Za-z\s]+:\s*', content, re.MULTILINE):
            return 'plain_text'
        
        return 'unknown'
    
    def parse_cascade_markdown(self, content: str, file_path: Path) -> ChatSession:
        """Parse Cascade markdown format chat records.
        
        Args:
            content: Markdown content from Cascade export.
            file_path: Path to the source file.
            
        Returns:
            Parsed ChatSession object.
        """
        lines = content.split('\n')
        
        # Extract session metadata
        session_id = self._extract_session_id(content, file_path)
        title = self._extract_title(content, file_path)
        date = self._extract_date(content, file_path)
        
        # Parse messages
        messages = []
        current_role = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check for role indicators
            user_match = re.match(r'^(?:User|Human|You):\s*(.*)', line, re.IGNORECASE)
            assistant_match = re.match(r'^(?:Assistant|AI|Claude|Cascade):\s*(.*)', line, re.IGNORECASE)
            
            if user_match:
                # Save previous message
                if current_role and current_content:
                    messages.append(ChatMessage(
                        role=current_role,
                        content='\n'.join(current_content).strip()
                    ))
                
                current_role = 'user'
                current_content = [user_match.group(1)] if user_match.group(1) else []
                
            elif assistant_match:
                # Save previous message
                if current_role and current_content:
                    messages.append(ChatMessage(
                        role=current_role,
                        content='\n'.join(current_content).strip()
                    ))
                
                current_role = 'assistant'
                current_content = [assistant_match.group(1)] if assistant_match.group(1) else []
                
            elif current_role and line and not re.match(r'^(?:---+|===+|\*\*\*+)$', line):
                # Continue current message
                current_content.append(line)
        
        # Save final message
        if current_role and current_content:
            messages.append(ChatMessage(
                role=current_role,
                content='\n'.join(current_content).strip()
            ))
        
        # Filter out empty messages
        messages = [msg for msg in messages if msg.content.strip()]
        
        return ChatSession(
            session_id=session_id,
            title=title,
            date=date,
            messages=messages,
            total_messages=len(messages),
            user_messages=sum(1 for msg in messages if msg.role == 'user'),
            assistant_messages=sum(1 for msg in messages if msg.role == 'assistant')
        )
    
    def parse_cascade_json(self, content: str, file_path: Path) -> ChatSession:
        """Parse Cascade JSON format chat records.
        
        Args:
            content: JSON content from Cascade export.
            file_path: Path to the source file.
            
        Returns:
            Parsed ChatSession object.
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        
        # Extract session metadata
        session_id = data.get('session_id', self._extract_session_id('', file_path))
        title = data.get('title', self._extract_title('', file_path))
        date = data.get('date', self._extract_date('', file_path))
        
        # Parse messages
        messages = []
        if 'messages' in data:
            for msg_data in data['messages']:
                messages.append(ChatMessage(
                    role=msg_data.get('role', 'unknown'),
                    content=msg_data.get('content', ''),
                    timestamp=msg_data.get('timestamp'),
                    message_id=msg_data.get('id')
                ))
        elif 'conversation' in data:
            # Alternative format
            for msg_data in data['conversation']:
                messages.append(ChatMessage(
                    role=msg_data.get('speaker', 'unknown').lower(),
                    content=msg_data.get('text', ''),
                    timestamp=msg_data.get('time')
                ))
        
        return ChatSession(
            session_id=session_id,
            title=title,
            date=date,
            messages=messages,
            total_messages=len(messages),
            user_messages=sum(1 for msg in messages if msg.role == 'user'),
            assistant_messages=sum(1 for msg in messages if msg.role == 'assistant')
        )
    
    def parse_chat_record(self, content: str, file_path: Path) -> ChatSession:
        """Parse a chat record file.
        
        Args:
            content: Raw file content.
            file_path: Path to the source file.
            
        Returns:
            Parsed ChatSession object.
        """
        format_type = self.detect_format(content)
        
        if format_type == 'cascade_markdown':
            return self.parse_cascade_markdown(content, file_path)
        elif format_type == 'cascade_json':
            return self.parse_cascade_json(content, file_path)
        elif format_type == 'plain_text':
            # Fallback to markdown parser for plain text
            return self.parse_cascade_markdown(content, file_path)
        else:
            # Create minimal session for unknown formats
            return ChatSession(
                session_id=self._extract_session_id(content, file_path),
                title=self._extract_title(content, file_path),
                date=self._extract_date(content, file_path),
                messages=[ChatMessage(role='unknown', content=content[:1000] + '...' if len(content) > 1000 else content)]
            )
    
    def analyze_conversation(self, session: ChatSession) -> ConversationInsights:
        """Analyze conversation to extract insights using AI.
        
        Args:
            session: Parsed chat session.
            
        Returns:
            ConversationInsights with extracted information.
        """
        if not is_available():
            return self._fallback_analysis(session)
        
        try:
            # Prepare conversation text for analysis
            conversation_text = self._format_conversation_for_analysis(session)
            
            # Truncate if too long (keep first and last parts)
            if len(conversation_text) > 4000:
                first_part = conversation_text[:2000]
                last_part = conversation_text[-2000:]
                conversation_text = f"{first_part}\n\n[... conversation continues ...]\n\n{last_part}"
            
            prompt = f"""Analyze this conversation and extract key information:

CONVERSATION:
{conversation_text}

Extract the following:
- topics_discussed: Main topics and subjects covered (3-8 items)
- key_insights: Important insights, learnings, or conclusions (3-6 items)
- action_items: Specific actions, tasks, or next steps mentioned (2-5 items)
- decisions_made: Decisions or choices that were made (1-4 items)
- technical_concepts: Technical terms, technologies, or concepts discussed (2-6 items)
- summary: 2-3 sentence summary of the conversation's purpose and outcome

Focus on actionable and specific information that would be useful for project documentation."""

            response = generate_structured(
                prompt=prompt,
                schema=self.ConversationAnalysis,
                system_prompt="You are a conversation analyst specializing in extracting structured information from technical discussions."
            )
            
            if response.success and response.data:
                data = response.data
                return ConversationInsights(
                    topics_discussed=data.get("topics_discussed", []),
                    key_insights=data.get("key_insights", []),
                    action_items=data.get("action_items", []),
                    decisions_made=data.get("decisions_made", []),
                    technical_concepts=data.get("technical_concepts", []),
                    summary=data.get("summary", "")
                )
            
        except Exception as e:
            logger.warning(f"AI conversation analysis failed: {e}")
        
        return self._fallback_analysis(session)
    
    def create_disc_log_entry(self, session: ChatSession, insights: ConversationInsights) -> DiscConversationLogEntry:
        """Create a DISC-compatible conversation log entry.
        
        Args:
            session: Parsed chat session.
            insights: Extracted conversation insights.
            
        Returns:
            DiscConversationLogEntry ready for DISC schema.
        """
        return DiscConversationLogEntry(
            date=session.date,
            session_id=session.session_id,
            topics_discussed=insights.topics_discussed,
            key_insights=insights.key_insights,
            action_items=insights.action_items
        )
    
    def extract_copyable_snippets(self, session: ChatSession, insights: ConversationInsights) -> Dict[str, str]:
        """Extract copyable text snippets for manual document creation.
        
        Args:
            session: Parsed chat session.
            insights: Extracted conversation insights.
            
        Returns:
            Dictionary of snippet types to formatted text.
        """
        snippets = {}
        
        # Summary snippet
        if insights.summary:
            snippets['summary'] = insights.summary
        
        # Requirements snippet (from user messages)
        user_requirements = []
        for msg in session.messages:
            if msg.role == 'user' and any(keyword in msg.content.lower() for keyword in ['need', 'want', 'should', 'require', 'must']):
                # Extract requirement-like sentences
                sentences = re.split(r'[.!?]+', msg.content)
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in ['need', 'want', 'should', 'require', 'must']):
                        user_requirements.append(sentence.strip())
        
        if user_requirements:
            snippets['requirements'] = '\n'.join(f"- {req}" for req in user_requirements[:5])
        
        # Technical details snippet
        if insights.technical_concepts:
            snippets['technical_concepts'] = '\n'.join(f"- {concept}" for concept in insights.technical_concepts)
        
        # Action items snippet
        if insights.action_items:
            snippets['action_items'] = '\n'.join(f"- [ ] {item}" for item in insights.action_items)
        
        # Decisions snippet
        if insights.decisions_made:
            snippets['decisions'] = '\n'.join(f"- {decision}" for decision in insights.decisions_made)
        
        # Full conversation snippet (truncated)
        conversation_lines = []
        for msg in session.messages[:10]:  # First 10 messages
            role_label = "User" if msg.role == 'user' else "Assistant"
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            conversation_lines.append(f"**{role_label}**: {content}")
        
        if len(session.messages) > 10:
            conversation_lines.append(f"... ({len(session.messages) - 10} more messages)")
        
        snippets['conversation_excerpt'] = '\n\n'.join(conversation_lines)
        
        return snippets
    
    def _extract_session_id(self, content: str, file_path: Path) -> str:
        """Extract session ID from content or filename."""
        # Try to find session ID in content
        session_match = re.search(self.cascade_patterns['session_start'], content, re.IGNORECASE)
        if session_match:
            return session_match.group(1).strip()
        
        # Fallback to filename-based ID
        filename = file_path.stem
        # Remove common prefixes/suffixes
        session_id = re.sub(r'^(chat|conversation|session)[-_]?', '', filename, flags=re.IGNORECASE)
        session_id = re.sub(r'[-_]?(chat|conversation|session)$', '', session_id, flags=re.IGNORECASE)
        
        return session_id or filename
    
    def _extract_title(self, content: str, file_path: Path) -> str:
        """Extract title from content or filename."""
        lines = content.split('\n')
        
        # Look for markdown title
        for line in lines[:5]:
            if line.startswith('# '):
                return line[2:].strip()
        
        # Look for title-like patterns
        title_patterns = [
            r'(?:Title|Subject|Topic):\s*(.+)',
            r'(?:Conversation about|Discussion on|Chat about):\s*(.+)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback to filename
        return file_path.stem.replace('_', ' ').replace('-', ' ').title()
    
    def _extract_date(self, content: str, file_path: Path) -> str:
        """Extract date from content or filename."""
        # Try to find date in content
        date_match = re.search(self.cascade_patterns['timestamp'], content)
        if date_match:
            date_str = date_match.group(1)
            # Normalize date format
            try:
                if len(date_str) == 10:  # YYYY-MM-DD
                    return date_str
                else:
                    # Parse and reformat
                    dt = datetime.fromisoformat(date_str.replace(' ', 'T'))
                    return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        # Try to extract from filename
        filename = file_path.name
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}_\d{2}_\d{2})',
            r'(\d{8})'  # YYYYMMDD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                if len(date_str) == 8:  # YYYYMMDD
                    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                else:
                    return date_str.replace('_', '-')
        
        # Fallback to today's date
        return datetime.now().strftime('%Y-%m-%d')
    
    def _format_conversation_for_analysis(self, session: ChatSession) -> str:
        """Format conversation for AI analysis."""
        lines = [f"Session: {session.title} ({session.date})"]
        lines.append("")
        
        for i, msg in enumerate(session.messages):
            role_label = "User" if msg.role == 'user' else "Assistant"
            lines.append(f"{role_label}: {msg.content}")
            if i < len(session.messages) - 1:
                lines.append("")
        
        return '\n'.join(lines)
    
    def _fallback_analysis(self, session: ChatSession) -> ConversationInsights:
        """Fallback analysis using simple text processing."""
        all_text = ' '.join(msg.content for msg in session.messages).lower()
        
        # Extract basic topics using keyword matching
        topic_keywords = {
            'frontend': ['react', 'vue', 'angular', 'ui', 'ux', 'component', 'css', 'html'],
            'backend': ['api', 'server', 'database', 'endpoint', 'service', 'microservice'],
            'architecture': ['design', 'pattern', 'structure', 'architecture', 'system'],
            'development': ['code', 'implement', 'develop', 'build', 'create', 'feature'],
            'testing': ['test', 'testing', 'qa', 'validation', 'verify'],
            'deployment': ['deploy', 'deployment', 'production', 'release', 'ci/cd']
        }
        
        topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                topics.append(topic)
        
        # Extract action-like phrases
        action_patterns = [
            r'(?:need to|should|must|will|going to)\s+([^.!?]+)',
            r'(?:action|task|todo):\s*([^.!?]+)',
            r'(?:next step|follow up):\s*([^.!?]+)'
        ]
        
        action_items = []
        for pattern in action_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            action_items.extend(matches[:3])
        
        return ConversationInsights(
            topics_discussed=topics[:5],
            key_insights=[f"Discussion covered {len(session.messages)} messages"],
            action_items=action_items[:3],
            decisions_made=[],
            technical_concepts=[],
            summary=f"Conversation with {session.user_messages} user messages and {session.assistant_messages} assistant responses."
        )


def create_chat_parser() -> ChatRecordParser:
    """Create a new chat record parser instance."""
    return ChatRecordParser()


def parse_chat_file(file_path: Path) -> Tuple[ChatSession, ConversationInsights, DiscConversationLogEntry]:
    """Convenience function to parse a chat file and extract all information.
    
    Args:
        file_path: Path to the chat record file.
        
    Returns:
        Tuple of (ChatSession, ConversationInsights, DiscConversationLogEntry).
    """
    parser = create_chat_parser()
    content = file_path.read_text(encoding='utf-8')
    
    session = parser.parse_chat_record(content, file_path)
    insights = parser.analyze_conversation(session)
    disc_entry = parser.create_disc_log_entry(session, insights)
    
    return session, insights, disc_entry
