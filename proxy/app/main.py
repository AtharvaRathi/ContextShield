import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.interceptors.base_proxy import intercept_and_forward, intercept_gemini_and_forward
from app.storage.db import metrics_db

# Configure descriptive terminal logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("contextshield.main")

# Initialize FastAPI app
app = FastAPI(
    title="ContextShield",
    description="Active Context Optimizer & Token Firewall Proxy",
    version="0.1.0"
)

# Standard CORS Middleware for the React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# OPENAI & ANTHROPIC ROUTES
# ---------------------------------------------------------

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Standard OpenAI-compatible endpoint."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}
        
    base_url = settings.get_active_provider_url()
    provider_url = f"{base_url.rstrip('/')}/chat/completions"
    
    logger.info("Received OpenAI format /v1/chat/completions request")
    return await intercept_and_forward(payload, provider_url)

@app.post("/v1/messages")
async def messages(request: Request):
    """Standard Anthropic-compatible endpoint."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}
        
    base_url = settings.get_active_provider_url()
    provider_url = f"{base_url.rstrip('/')}/messages"
    
    logger.info("Received Anthropic format /v1/messages request")
    return await intercept_and_forward(payload, provider_url)

# ---------------------------------------------------------
# GEMINI ROUTES
# ---------------------------------------------------------

@app.post("/v1beta/models/{model}:generateContent")
async def gemini_generate_content(model: str, request: Request):
    """Google Gemini-compatible endpoint for standard generation."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}
        
    if settings.gemini_api_key:
        provider_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.gemini_api_key}"
    else:
        query_string = request.url.query
        provider_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        if query_string:
            provider_url += f"?{query_string}"
            
    logger.info(f"Received Gemini format generateContent request for model: {model}")
    return await intercept_gemini_and_forward(payload, provider_url)

@app.post("/v1beta/models/{model}:streamGenerateContent")
async def gemini_stream_generate_content(model: str, request: Request):
    """Google Gemini-compatible endpoint for streaming generation."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}
        
    # Append alt=sse so the proxy can consume the chunk stream correctly
    if settings.gemini_api_key:
        provider_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={settings.gemini_api_key}"
    else:
        query_string = request.url.query
        provider_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"
        if query_string:
            provider_url += f"?{query_string}"
            if "alt=sse" not in query_string:
                provider_url += "&alt=sse"
        else:
            provider_url += "?alt=sse"
            
    logger.info(f"Received Gemini format streamGenerateContent request for model: {model}")
    return await intercept_gemini_and_forward(payload, provider_url)

# ---------------------------------------------------------

@app.get("/api/stats")
async def get_stats():
    """Returns real, live telemetry data for the React frontend dashboard."""
    return metrics_db.get_savings_stats()

@app.get("/")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "ContextShield"}
