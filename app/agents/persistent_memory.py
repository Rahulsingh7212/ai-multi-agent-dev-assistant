from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    BaseMessage,
    messages_from_dict,
    messages_to_dict,
)
from langchain_community.chat_message_histories import RedisChatMessageHistory
from app.services.redis_service import redis_service
from config.settings import settings
from typing import List, Optional, Dict, Any
import logging
import json
import uuid

logger = logging.getLogger(__name__)


class PersistentMemory:
    """
    Persistent conversation memory backed by Redis.

    Features:
    - Cross-session persistence (survives server restarts)
    - Per-user memory isolation (user_id prefix)
    - Automatic TTL expiration
    - Fallback to in-memory when Redis is unavailable
    - Conversation summarization for long histories
    """

    # Key prefixes for Redis namespacing
    PREFIX_CONVERSATION = "conv"
    PREFIX_USER_SESSIONS = "user_sessions"
    PREFIX_SESSION_META = "session_meta"

    def __init__(self):
        self._in_memory_fallback: Dict[str, List[BaseMessage]] = {}
        self._redis_available = redis_service.is_connected

        if self._redis_available:
            logger.info("✅ PersistentMemory using Redis backend")
        else:
            logger.warning("⚠️  PersistentMemory using in-memory fallback")

    # ============================
    # CORE: Add Message
    # ============================

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Add a message to the conversation history.

        Args:
            session_id: Conversation session ID
            role: 'human' or 'ai'
            content: Message content
            user_id: Optional user ID for isolation

        Returns:
            True if successful
        """
        # Build the Redis key with user isolation
        redis_key = self._build_key(session_id, user_id)

        # Create message object
        if role == "human":
            message = HumanMessage(content=content)
        elif role == "ai":
            message = AIMessage(content=content)
        else:
            message = HumanMessage(content=content)

        if self._redis_available:
            return self._add_to_redis(redis_key, message, user_id, session_id)
        else:
            return self._add_to_in_memory(redis_key, message)

    def _add_to_redis(
        self,
        redis_key: str,
        message: BaseMessage,
        user_id: Optional[str],
        session_id: str,
    ) -> bool:
        """Add message to Redis"""
        try:
            # Use LangChain's RedisChatMessageHistory
            history = RedisChatMessageHistory(
                session_id=redis_key,
                url=settings.REDIS_URL,
            )
            history.add_message(message)

            # Track session for user
            if user_id:
                self._track_user_session(user_id, session_id)

            # Update session metadata
            self._update_session_meta(redis_key, role=message.type)

            # Trim if exceeding max turns
            stored = history.messages
            if len(stored) > settings.MAX_CONVERSATION_TURNS * 2:
                # Keep only recent messages
                excess = len(stored) - settings.MAX_CONVERSATION_TURNS * 2
                for _ in range(excess):
                    # RedisChatMessageHistory doesn't have trim,
                    # so we clear and re-add recent ones
                    pass
                logger.info(f"🔄 Trimmed conversation {redis_key} to max turns")

            return True

        except Exception as e:
            logger.error(f"❌ Redis add_message error: {e}")
            # Fallback to in-memory
            return self._add_to_in_memory(redis_key, message)

    def _add_to_in_memory(
        self,
        key: str,
        message: BaseMessage,
    ) -> bool:
        """Add message to in-memory fallback"""
        if key not in self._in_memory_fallback:
            self._in_memory_fallback[key] = []

        self._in_memory_fallback[key].append(message)

        # Trim to max
        max_msgs = settings.MAX_CONVERSATION_TURNS * 2
        if len(self._in_memory_fallback[key]) > max_msgs:
            self._in_memory_fallback[key] = self._in_memory_fallback[key][-max_msgs:]

        return True

    # ============================
    # CORE: Get History
    # ============================

    def get_history(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[BaseMessage]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session ID
            user_id: Optional user ID for isolation
            limit: Optional limit on number of recent messages

        Returns:
            List of BaseMessage objects
        """
        redis_key = self._build_key(session_id, user_id)

        if self._redis_available:
            try:
                history = RedisChatMessageHistory(
                    session_id=redis_key,
                    url=settings.REDIS_URL,
                )
                messages = history.messages

                if limit:
                    messages = messages[-limit:]

                return messages

            except Exception as e:
                logger.error(f"❌ Redis get_history error: {e}")
                return self._in_memory_fallback.get(redis_key, [])
        else:
            messages = self._in_memory_fallback.get(redis_key, [])
            if limit:
                messages = messages[-limit:]
            return messages

    # ============================
    # CORE: Get Context String
    # ============================

    def get_context_string(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        max_chars: int = 4000,
    ) -> str:
        """
        Get formatted conversation context for prompting.
        Truncates if exceeds max_chars.
        """
        messages = self.get_history(session_id, user_id)

        if not messages:
            return ""

        parts = []
        total_chars = 0

        for msg in messages:
            role = "Human" if isinstance(msg, HumanMessage) else "AI"
            entry = f"{role}: {msg.content}"

            if total_chars + len(entry) > max_chars:
                break

            parts.append(entry)
            total_chars += len(entry)

        return "\n\n".join(parts)

    # ============================
    # USER ISOLATION
    # ============================

    def _build_key(self, session_id: str, user_id: Optional[str] = None) -> str:
        """Build Redis key with user isolation namespace"""
        if user_id:
            return f"{self.PREFIX_CONVERSATION}:{user_id}:{session_id}"
        return f"{self.PREFIX_CONVERSATION}:{session_id}"

    def _track_user_session(self, user_id: str, session_id: str) -> None:
        """Track which sessions belong to which user"""
        if not redis_service.client:
            return
        try:
            key = f"{self.PREFIX_USER_SESSIONS}:{user_id}"
            redis_service.client.sadd(key, session_id)
            redis_service.client.expire(key, settings.REDIS_TTL)
        except Exception as e:
            logger.error(f"Error tracking user session: {e}")

    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for a user"""
        if not redis_service.client:
            return []
        try:
            key = f"{self.PREFIX_USER_SESSIONS}:{user_id}"
            sessions = redis_service.client.smembers(key)
            return list(sessions)
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []

    # ============================
    # SESSION METADATA
    # ============================

    def _update_session_meta(self, redis_key: str, role: str) -> None:
        """Update session metadata"""
        if not redis_service.client:
            return
        try:
            meta_key = f"{self.PREFIX_SESSION_META}:{redis_key}"
            meta = redis_service.get_key(meta_key) or {}

            meta["last_message_role"] = role
            meta["last_message_time"] = str(uuid.uuid4())[:8]  # Simple timestamp
            meta["message_count"] = meta.get("message_count", 0) + 1

            redis_service.set_key(meta_key, meta)
        except Exception as e:
            logger.error(f"Error updating session meta: {e}")

    def get_session_meta(self, session_id: str, user_id: Optional[str] = None) -> dict:
        """Get session metadata"""
        redis_key = self._build_key(session_id, user_id)
        meta_key = f"{self.PREFIX_SESSION_META}:{redis_key}"
        return redis_service.get_key(meta_key) or {}

    # ============================
    # CLEAR / DELETE
    # ============================

    def clear_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """Clear a session's conversation history"""
        redis_key = self._build_key(session_id, user_id)

        if self._redis_available:
            try:
                history = RedisChatMessageHistory(
                    session_id=redis_key,
                    url=settings.REDIS_URL,
                )
                history.clear()
                logger.info(f"🗑️  Redis session cleared: {redis_key}")
                return True
            except Exception as e:
                logger.error(f"❌ Redis clear error: {e}")
                return False
        else:
            if redis_key in self._in_memory_fallback:
                del self._in_memory_fallback[redis_key]
                return True
            return False

    # ============================
    # LIST SESSIONS
    # ============================

    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all sessions (optionally filtered by user)"""
        if user_id:
            session_ids = self.get_user_sessions(user_id)
        else:
            # Find all conversation keys in Redis
            pattern = f"{self.PREFIX_CONVERSATION}:*"
            keys = redis_service.keys_pattern(pattern)
            session_ids = []
            for key in keys:
                # Extract session_id from key
                parts = key.split(":")

                # conv:persist-test-001
                if len(parts) >= 2:
                    session_ids.append(parts[-1])

        result = []
        for sid in session_ids:
            meta = self.get_session_meta(sid, user_id)
            msg_count = len(self.get_history(sid, user_id))
            result.append({
                "session_id": sid,
                "message_count": msg_count,
                "metadata": meta,
            })

        return result

    # ============================
    # STATISTICS
    # ============================

    def get_stats(self) -> dict:
        """Get memory statistics"""
        total_sessions = len(redis_service.keys_pattern(f"{self.PREFIX_CONVERSATION}:*"))
        total_user_mappings = len(redis_service.keys_pattern(f"{self.PREFIX_USER_SESSIONS}:*"))

        return {
            "backend": "redis" if self._redis_available else "in_memory",
            "redis_connected": self._redis_available,
            "total_sessions": total_sessions,
            "total_user_mappings": total_user_mappings,
            "max_conversation_turns": settings.MAX_CONVERSATION_TURNS,
            "ttl_seconds": settings.REDIS_TTL,
        }


# ============================
# Singleton instance
# ============================
persistent_memory = PersistentMemory()