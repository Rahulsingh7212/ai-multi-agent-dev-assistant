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
    APP_VERSION: str = "0.2.0"  # Updated for Stage 1

    # ==================
    # LLM Config
    # ==================
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3.5-flash")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    LLM_STREAMING: bool = os.getenv("LLM_STREAMING", "true").lower() == "true"

    # ==================
    # Validation
    # ==================
    def validate_keys(self) -> dict:
        status = {}
        status["gemini"] = "✅" if self.GEMINI_API_KEY else "❌ MISSING"
        status["tavily"] = "✅" if self.TAVILY_API_KEY else "❌ MISSING"
        status["github"] = "✅" if self.GITHUB_PAT else "❌ MISSING"
        return status

    def is_ready(self) -> bool:
        """Check if minimum required keys are present"""
        return bool(self.GEMINI_API_KEY)


settings = Settings()