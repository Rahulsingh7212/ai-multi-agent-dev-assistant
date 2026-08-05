from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Short-term conversation memory manager.
    Stores message history per session in-memory.

    For production, replace with Redis/DB-backed memory.
    For now, this works perfectly for single-session usage.
    """

    def __init__(self, max_history: int = 20):
        self._store: Dict[str, List[BaseMessage]] = {}
        self._max_history = max_history
        logger.info(f"✅ ConversationMemory initialized (max {max_history} messages per session)")

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Add a message to the session's history"""
        if session_id not in self._store:
            self._store[session_id] = []

        if role == "human":
            msg = HumanMessage(content=content)
        elif role == "ai":
            msg = AIMessage(content=content)
        else:
            msg = HumanMessage(content=content)

        self._store[session_id].append(msg)

        # Trim to max history
        if len(self._store[session_id]) > self._max_history:
            self._store[session_id] = self._store[session_id][-self._max_history:]

    def get_history(self, session_id: str) -> List[BaseMessage]:
        """Get all messages for a session"""
        return self._store.get(session_id, [])

    def get_context_string(self, session_id: str) -> str:
        """Get formatted conversation context for prompting"""
        messages = self.get_history(session_id)

        if not messages:
            return ""

        parts = []
        for msg in messages:
            role = "Human" if isinstance(msg, HumanMessage) else "AI"
            parts.append(f"{role}: {msg.content}")

        return "\n\n".join(parts)

    def clear_session(self, session_id: str) -> None:
        """Clear a session's history"""
        if session_id in self._store:
            del self._store[session_id]
            logger.info(f"🗑️  Session cleared: {session_id}")

    def list_sessions(self) -> List[str]:
        """List all active sessions"""
        return list(self._store.keys())

    def session_message_count(self, session_id: str) -> int:
        """Get number of messages in a session"""
        return len(self._store.get(session_id, []))


# ============================
# Singleton instance
# ============================
conversation_memory = ConversationMemory(max_history=20)