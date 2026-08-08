from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    # ==================
    # API Keys
    # ==================
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    GITHUB_PAT: str = os.getenv("GITHUB_PAT", "")
    GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "")

    # ==================
    # App Config
    # ==================
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_NAME: str = "AI Multi-Agent Developer Assistant"
    APP_VERSION: str = "0.6.0"  # Updated for Stage 5

    # ==================
    # LLM Config
    # ==================
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    LLM_STREAMING: bool = os.getenv("LLM_STREAMING", "true").lower() == "true"

    # ==================
    # Redis Config (NEW)
    # ==================
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_TTL: int = int(os.getenv("REDIS_TTL", "86400"))

    # ==================
    # Memory Config (NEW)
    # ==================
    MEMORY_BACKEND: str = os.getenv("MEMORY_BACKEND", "redis")
    MAX_CONVERSATION_TURNS: int = int(os.getenv("MAX_CONVERSATION_TURNS", "50"))
    MEMORY_TTL_SECONDS: int = int(os.getenv("MEMORY_TTL_SECONDS", "86400"))

    # ==================
    # Retry Config (NEW)
    # ==================
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_WAIT_MIN: float = 1.0
    RETRY_WAIT_MAX: float = 10.0

    # ==================
    # Validation
    # ==================
    def validate_keys(self) -> dict:
        status = {}
        status["gemini"] = "✅" if self.GEMINI_API_KEY else "❌ MISSING"
        status["tavily"] = "✅" if self.TAVILY_API_KEY else "❌ MISSING"
        status["github"] = "✅" if self.GITHUB_PAT else "❌ MISSING"
        status["redis"] = "✅" if self._check_redis() else "❌ MISSING"
        return status

    def _check_redis(self) -> bool:
        """Check if Redis is reachable"""
        try:
            import redis as redis_lib
            client = redis_lib.Redis(
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                db=self.REDIS_DB,
                password=self.REDIS_PASSWORD or None,
                socket_timeout=2,
            )
            return client.ping()
        except Exception:
            return False

    def is_ready(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    def is_redis_ready(self) -> bool:
        return self._check_redis()


settings = Settings()