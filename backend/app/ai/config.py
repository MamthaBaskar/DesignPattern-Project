"""
Configuration for AI / LLM services.
Loads settings securely from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class AIConfig:
    # Provider: "openai", "gemini", "anthropic", "custom", "none"
    PROVIDER: str = os.getenv("AI_PROVIDER", "openai").lower()

    # OpenAI / Compatible settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Gemini settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Anthropic settings
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")

    # Timeout
    REQUEST_TIMEOUT: float = float(os.getenv("AI_REQUEST_TIMEOUT", "15.0"))

    @classmethod
    def is_ai_configured(cls) -> bool:
        """Returns True if any valid API key is present."""
        if cls.PROVIDER == "openai" and cls.OPENAI_API_KEY:
            return True
        if cls.PROVIDER == "gemini" and cls.GEMINI_API_KEY:
            return True
        if cls.PROVIDER == "anthropic" and cls.ANTHROPIC_API_KEY:
            return True
        if cls.PROVIDER == "custom" and cls.OPENAI_API_KEY:
            return True
        return False

