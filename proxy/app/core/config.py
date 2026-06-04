"""
Core Configuration Module & Routing Engine.

This module acts as the routing engine for ContextShield. It ensures the proxy
acts as a standard OpenAI-compatible endpoint for IDEs (like Cursor/Antigravity),
while actually routing the underlying traffic to 100% free local or cloud alternatives,
effectively bypassing expensive providers.
"""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    """
    # Core Proxy Settings
    proxy_port: int = 8000

    # Local GPU Engine
    use_local_gpu: bool = True
    local_ollama_url: str = "http://localhost:11434/v1"

    # Free Cloud Endpoints (Fallbacks)
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def get_active_provider_url(self) -> str:
        """
        Determines the active routing endpoint based on user configuration.
        
        Routing Logic:
        1. If USE_LOCAL_GPU is True, routes entirely locally to Ollama.
        2. If False, checks for a GROQ_API_KEY to route to Groq's high-speed API.
        3. If neither is available, defaults to OpenRouter's free tier endpoint.
        
        Returns:
            str: The base URL of the active LLM provider.
        """
        if self.use_local_gpu:
            return self.local_ollama_url
            
        if self.groq_api_key:
            return "https://api.groq.com/openai/v1"
            
        return "https://openrouter.ai/api/v1"


settings = Settings()
