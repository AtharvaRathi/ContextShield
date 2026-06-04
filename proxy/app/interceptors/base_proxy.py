import json
import logging
import httpx
import re
from fastapi.responses import StreamingResponse, JSONResponse
from app.core.config import settings
from app.optimizers.ast_parser import optimize_context, optimize_python_code, minify_generic_code
from app.storage.db import metrics_db

# Setup interceptor logger
logger = logging.getLogger("contextshield.interceptor")
logger.setLevel(logging.INFO)

async def intercept_and_forward(payload: dict, provider_url: str):
    """
    Intercepts the incoming OpenAI/Anthropic request, performs active token optimization on the context,
    strips conflicting headers, and forwards the payload safely.
    """
    original_payload_str = json.dumps(payload)
    original_size = len(original_payload_str)
    
    if "messages" in payload and isinstance(payload["messages"], list):
        try:
            optimized_messages, _ = optimize_context(payload["messages"])
            payload["messages"] = optimized_messages
            
            optimized_payload_str = json.dumps(payload)
            optimized_size = len(optimized_payload_str)
            chars_saved = original_size - optimized_size
            
            metrics_db.log_request(original_size, optimized_size)
            
            if chars_saved > 0:
                logger.info(f"[ContextShield Proxy] OpenAI/Anthropic payload optimized. Chars saved: {chars_saved} ({(chars_saved/original_size)*100:.1f}%)")
        except Exception as e:
            logger.error(f"Context optimization failed, forwarding original payload. Error: {e}")
            optimized_size = original_size
    else:
        optimized_size = original_size

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if "api.groq.com" in provider_url and settings.groq_api_key:
        headers["Authorization"] = f"Bearer {settings.groq_api_key}"
    elif "openrouter.ai" in provider_url and settings.openrouter_api_key:
        headers["Authorization"] = f"Bearer {settings.openrouter_api_key}"

    is_stream = payload.get("stream", False)
    
    if is_stream:
        async def stream_generator():
            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    logger.info(f"Forwarding optimized STREAM request to {provider_url}")
                    async with client.stream("POST", provider_url, json=payload, headers=headers) as response:
                        async for chunk in response.aiter_bytes():
                            yield chunk
                    logger.info("Stream completed successfully.")
                except httpx.RequestError as e:
                    logger.error(f"Stream connection failed: {e}")
                    yield b'data: {"error": "Connection failed."}\n\n'
                except Exception as e:
                    logger.error(f"Unexpected stream error: {e}")
                    
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                logger.info(f"Forwarding optimized STANDARD request to {provider_url}")
                response = await client.post(provider_url, json=payload, headers=headers)
                
                try:
                    data = response.json()
                except ValueError:
                    return JSONResponse(
                        content={"error": "Provider returned invalid JSON", "details": response.text},
                        status_code=502
                    )
                return JSONResponse(content=data, status_code=response.status_code)
            except httpx.RequestError as e:
                logger.error(f"Connection error to {provider_url}: {e}")
                return JSONResponse(
                    content={"error": f"Failed to connect. Details: {e}"},
                    status_code=502
                )
            except Exception as e:
                logger.error(f"Unexpected error handling standard response: {e}")
                return JSONResponse(
                    content={"error": "Internal Server Error"},
                    status_code=500
                )

async def intercept_gemini_and_forward(payload: dict, provider_url: str):
    """
    Intercepts the incoming Gemini API request, parses the unique {"contents": [{"parts": ...}]} structure,
    optimizes code blocks in-flight, and forwards cleanly to the Google Gemini endpoint.
    """
    original_payload_str = json.dumps(payload)
    original_size = len(original_payload_str)
    
    try:
        # Traverse Gemini structure: payload -> contents -> parts -> text
        contents = payload.get("contents", [])
        if isinstance(contents, list):
            for content in contents:
                parts = content.get("parts", [])
                if isinstance(parts, list):
                    for part in parts:
                        if isinstance(part, dict) and "text" in part and isinstance(part["text"], str):
                            original_text = part["text"]
                            
                            # Apply the AST/Regex markdown optimization engine to the raw Gemini text
                            pattern = re.compile(r'```([a-zA-Z0-9+\-.]*)\s*\n(.*?)```', re.DOTALL)
                            
                            def optimize_match(match):
                                lang = match.group(1).lower().strip()
                                code = match.group(2)
                                
                                if lang in ['python', 'py']:
                                    optimized_code = optimize_python_code(code)
                                else:
                                    optimized_code = minify_generic_code(code)
                                    
                                return f"```{lang}\n{optimized_code}\n```"
                                
                            optimized_text = pattern.sub(optimize_match, original_text)
                            part["text"] = optimized_text
                            
        optimized_payload_str = json.dumps(payload)
        optimized_size = len(optimized_payload_str)
        chars_saved = original_size - optimized_size
        
        # Broadcast savings to dashboard metrics DB
        metrics_db.log_request(original_size, optimized_size)
        
        if chars_saved > 0:
            logger.info(f"[ContextShield Proxy] Gemini payload optimized. Chars saved: {chars_saved} ({(chars_saved/original_size)*100:.1f}%)")
    except Exception as e:
        logger.error(f"Gemini context optimization failed, forwarding original payload gracefully. Error: {e}")
        optimized_size = original_size

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Inject Google API Key if it's set in the backend config
    if settings.gemini_api_key and "generativelanguage.googleapis.com" in provider_url:
        headers["x-goog-api-key"] = settings.gemini_api_key

    # Gemini uses specific API routes for streams instead of a payload "stream" boolean
    is_stream = "streamGenerateContent" in provider_url
    
    if is_stream:
        async def stream_generator():
            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    logger.info(f"Forwarding optimized GEMINI STREAM request to {provider_url}")
                    async with client.stream("POST", provider_url, json=payload, headers=headers) as response:
                        async for chunk in response.aiter_bytes():
                            yield chunk
                    logger.info("Stream completed successfully.")
                except httpx.RequestError as e:
                    logger.error(f"Stream connection failed: {e}")
                    yield b'data: {"error": "Connection failed."}\n\n'
                except Exception as e:
                    logger.error(f"Unexpected stream error: {e}")
                    
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                logger.info(f"Forwarding optimized GEMINI STANDARD request to {provider_url}")
                response = await client.post(provider_url, json=payload, headers=headers)
                
                try:
                    data = response.json()
                except ValueError:
                    return JSONResponse(
                        content={"error": "Provider returned invalid JSON", "details": response.text},
                        status_code=502
                    )
                return JSONResponse(content=data, status_code=response.status_code)
            except httpx.RequestError as e:
                logger.error(f"Connection error to {provider_url}: {e}")
                return JSONResponse(
                    content={"error": f"Failed to connect. Details: {e}"},
                    status_code=502
                )
            except Exception as e:
                logger.error(f"Unexpected error handling standard response: {e}")
                return JSONResponse(
                    content={"error": "Internal Server Error"},
                    status_code=500
                )
