import json
import logging
import os
from typing import List

import redis
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Redis-backed short-term conversation memory.

    Stores conversation history permanently in Redis/Memurai
    so sessions survive application restarts.
    """

    def __init__(self, max_history: int = 20):
        self._max_history = max_history

        # Redis connection
        redis_url = os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        )

        self._redis = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
        )

        logger.info(
            f"🧠 ConversationMemory initialized "
            f"(Redis, max {max_history} messages per session)"
        )

    # ============================
    # Redis Key
    # ============================

    def _get_key(self, session_id: str) -> str:
        return f"conv:{session_id}"

    # ============================
    # Add Message
    # ============================

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Add a message to Redis."""

        try:
            if role == "human":
                message_type = "human"
            elif role == "ai":
                message_type = "ai"
            else:
                message_type = "human"

            message_data = {
                "type": message_type,
                "content": str(content),
            }

            key = self._get_key(session_id)

            # Store message
            self._redis.rpush(
                key,
                json.dumps(message_data),
            )

            # Keep only latest max_history messages
            self._redis.ltrim(
                key,
                -self._max_history,
                -1,
            )

            logger.info(
                f"💾 Memory saved | Session: {session_id} | Role: {role}"
            )

        except Exception as e:
            logger.error(
                f"❌ Failed to save memory | "
                f"Session: {session_id} | Error: {e}"
            )
            raise

    # ============================
    # Get History
    # ============================

    def get_history(self, session_id: str) -> List[BaseMessage]:
        """Get conversation history from Redis."""

        try:
            key = self._get_key(session_id)

            raw_messages = self._redis.lrange(
                key,
                0,
                -1,
            )

            messages = []

            for raw_message in raw_messages:
                data = json.loads(raw_message)

                if data["type"] == "human":
                    messages.append(
                        HumanMessage(
                            content=data["content"]
                        )
                    )

                elif data["type"] == "ai":
                    messages.append(
                        AIMessage(
                            content=data["content"]
                        )
                    )

            return messages

        except Exception as e:
            logger.error(
                f"❌ Failed to get memory | "
                f"Session: {session_id} | Error: {e}"
            )
            return []

    # ============================
    # Context String
    # ============================

    def get_context_string(self, session_id: str) -> str:
        """Get formatted conversation context."""

        messages = self.get_history(session_id)

        if not messages:
            return ""

        parts = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "Human"
            else:
                role = "AI"

            parts.append(
                f"{role}: {msg.content}"
            )

        return "\n\n".join(parts)

    # ============================
    # Clear Session
    # ============================

    def clear_session(self, session_id: str) -> None:
        """Delete a conversation session."""

        try:
            key = self._get_key(session_id)

            deleted = self._redis.delete(key)

            if deleted:
                logger.info(
                    f"🗑️ Session cleared: {session_id}"
                )
            else:
                logger.info(
                    f"ℹ️ Session not found: {session_id}"
                )

        except Exception as e:
            logger.error(
                f"❌ Failed to clear session: {e}"
            )
            raise

    # ============================
    # List Sessions
    # ============================

    def list_sessions(self) -> List[str]:
        """List all active sessions stored in Redis."""

        try:
            sessions = []

            for key in self._redis.scan_iter(
                match="conv:*"
            ):
                session_id = key.replace(
                    "conv:",
                    "",
                    1,
                )

                sessions.append(session_id)

            return sorted(sessions)

        except Exception as e:
            logger.error(
                f"❌ Failed to list sessions: {e}"
            )
            return []

    # ============================
    # Message Count
    # ============================

    def session_message_count(
        self,
        session_id: str,
    ) -> int:
        """Get number of messages in a session."""

        try:
            key = self._get_key(session_id)

            return self._redis.llen(key)

        except Exception as e:
            logger.error(
                f"❌ Failed to get message count: {e}"
            )
            return 0

    # ============================
    # Redis Health
    # ============================

    def ping(self) -> bool:
        """Check Redis connection."""

        try:
            return self._redis.ping()
        except Exception:
            return False


# ============================
# Singleton instance
# ============================

conversation_memory = ConversationMemory(
    max_history=20
)