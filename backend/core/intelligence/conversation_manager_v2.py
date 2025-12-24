"""
Conversation Manager - Manages multi-speaker dialogue

Accumulates messages from both speakers and provides formatted dialogue for LLM analysis.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Single message in conversation"""
    timestamp: str
    speaker: str  # "YOU" or "OTHER"
    text: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def formatted(self) -> str:
        """Format for display"""
        time = datetime.fromisoformat(self.timestamp).strftime('%H:%M:%S')
        return f"[{time}] {self.speaker}: {self.text}"


class ConversationManager:
    """
    Manages ongoing conversation with multiple speakers
    """
    
    def __init__(self):
        self.conversation_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.messages: List[Message] = []
        logger.info(f"New conversation started: {self.conversation_id}")
    
    def add_message(self, text: str, speaker: str) -> Message:
        """
        Add message to conversation
        
        Args:
            text: Transcribed text
            speaker: "YOU" or "OTHER"
        
        Returns:
            Created message
        """
        message = Message(
            timestamp=datetime.now().isoformat(),
            speaker=speaker,
            text=text
        )
        
        self.messages.append(message)
        logger.info(f"Message added ({speaker}): {text[:50]}...")
        
        return message
    
    def get_formatted_dialogue(self) -> str:
        """
        Get full dialogue formatted for LLM
        
        Returns:
            Formatted string with all messages
        """
        if not self.messages:
            return "(No conversation yet)"
        
        lines = [msg.formatted() for msg in self.messages]
        return "\n".join(lines)
    
    def get_messages(self) -> List[Dict]:
        """
        Get all messages as dictionaries
        
        Returns:
            List of message dictionaries
        """
        return [msg.to_dict() for msg in self.messages]
    
    def clear(self):
        """Clear conversation and start new one"""
        old_id = self.conversation_id
        old_count = len(self.messages)
        
        self.conversation_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.messages = []
        
        logger.info(f"Conversation {old_id} cleared ({old_count} messages). New: {self.conversation_id}")
    
    def get_stats(self) -> Dict:
        """Get conversation statistics"""
        you_count = sum(1 for m in self.messages if m.speaker == "YOU")
        other_count = sum(1 for m in self.messages if m.speaker == "OTHER")
        
        return {
            "conversation_id": self.conversation_id,
            "start_time": self.start_time.isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_messages": len(self.messages),
            "you_messages": you_count,
            "other_messages": other_count
        }
    
    def export_markdown(self) -> str:
        """Export conversation as markdown"""
        stats = self.get_stats()
        
        md = f"""# Conversation {self.conversation_id}

**Started:** {datetime.fromisoformat(stats['start_time']).strftime('%Y-%m-%d %H:%M:%S')}  
**Duration:** {stats['duration_seconds']:.1f}s  
**Messages:** {stats['total_messages']} (You: {stats['you_messages']}, Other: {stats['other_messages']})

---

## Dialogue

"""
        for msg in self.messages:
            md += f"{msg.formatted()}\n"
        
        return md
