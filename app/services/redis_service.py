import redis as redis_lib
from config.settings import settings
from typing import Optional, List, Any
import logging
import json

logger = logging.getLogger(__name__)


class RedisService:
    """
    Redis connection manager.
    Singleton pattern — one connection pool shared across the app.
    """

    def __init__(self):
        self._client: Optional[redis_lib.Redis] = None
        self._connect()

    def _connect(self):
        """Establish Redis connection"""
        try:
            self._client = redis_lib.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test connection
            self._client.ping()
            logger.info(
                f"✅ Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            )

        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️  Falling back to in-memory storage")
            self._client = None

    @property
    def client(self) -> Optional[redis_lib.Redis]:
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if Redis is available"""
        if not self._client:
            return False
        try:
            return self._client.ping()
        except Exception:
            return False

    # ============================
    # Key-Value Operations
    # ============================

    def set_key(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a key with optional TTL"""
        if not self._client:
            return False
        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            self._client.set(key, serialized, ex=ttl or settings.REDIS_TTL)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def get_key(self, key: str) -> Optional[Any]:
        """Get a key's value"""
        if not self._client:
            return None
        try:
            value = self._client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def delete_key(self, key: str) -> bool:
        """Delete a key"""
        if not self._client:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DEL error: {e}")
            return False

    def key_exists(self, key: str) -> bool:
        """Check if a key exists"""
        if not self._client:
            return False
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    # ============================
    # List Operations (for message history)
    # ============================

    def list_push(self, key: str, value: Any) -> bool:
        """Push to a Redis list"""
        if not self._client:
            return False
        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            self._client.rpush(key, serialized)
            # Set TTL on the list key
            self._client.expire(key, settings.REDIS_TTL)
            return True
        except Exception as e:
            logger.error(f"Redis RPUSH error: {e}")
            return False

    def list_range(
        self,
        key: str,
        start: int = 0,
        end: int = -1,
    ) -> List[Any]:
        """Get range from a Redis list"""
        if not self._client:
            return []
        try:
            items = self._client.lrange(key, start, end)
            result = []
            for item in items:
                try:
                    result.append(json.loads(item))
                except (json.JSONDecodeError, TypeError):
                    result.append(item)
            return result
        except Exception as e:
            logger.error(f"Redis LRANGE error: {e}")
            return []

    def list_length(self, key: str) -> int:
        """Get length of a Redis list"""
        if not self._client:
            return 0
        try:
            return self._client.llen(key)
        except Exception as e:
            logger.error(f"Redis LLEN error: {e}")
            return 0

    def list_trim(self, key: str, max_length: int) -> bool:
        """Trim list to max length (keep most recent)"""
        if not self._client:
            return False
        try:
            current_len = self._client.llen(key)
            if current_len > max_length:
                # Keep only the last max_length items
                start = 0
                end = current_len - max_length - 1
                self._client.ltrim(key, start + (end + 1), -1)
            return True
        except Exception as e:
            logger.error(f"Redis LTRIM error: {e}")
            return False

    # ============================
    # Keys Operations
    # ============================

    def keys_pattern(self, pattern: str) -> List[str]:
        """Find keys matching a pattern"""
        if not self._client:
            return []
        try:
            return self._client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS error: {e}")
            return []

    # ============================
    # Health
    # ============================

    def get_info(self) -> dict:
        """Get Redis server info"""
        if not self._client:
            return {"status": "disconnected"}
        try:
            info = self._client.info()
            return {
                "status": "connected",
                "version": info.get("redis_version", "unknown"),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": self._client.dbsize(),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}


# ============================
# Singleton instance
# ============================
redis_service = RedisService()