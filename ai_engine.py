import asyncio
import base64
import json
import logging
import time
import urllib.parse
from typing import Any
import httpx
from config import Config

logger = logging.getLogger(__name__)

_CLIENT: httpx.AsyncClient | None = None

def _get_client() -> httpx.AsyncClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=15.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _CLIENT

async def close_http_client() -> None:
    global _CLIENT
    if _CLIENT is not None:
        await _CLIENT.aclose()
        _CLIENT = None

async def _post_json(url: str, *, headers: dict[str, str] | None = None, json_payload: dict[str, Any] | None = None, retries: int = 2) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            client = _get_client()
            resp = await client.post(url, headers=headers, json=json_payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_error = exc
            logger.exception("HTTP request failed on attempt %s/%s: %s", attempt + 1, retries + 1, exc)
            if attempt < retries:
                await asyncio.sleep(2.0 * (attempt + 1))
                continue
            raise RuntimeError(f"Request failed after {retries + 1} attempts") from last_error

# ==========================================
# LAYER 1: CINEMATIC PROMPT ENHANCEMENT
# ==========================================
async def enhance_prompt_gemini(user_prompt: str) -> str:
    """Primary: Uses Gemini for prompt enhancement (most reliable)"""
    system_prompt = (
        "You are a Hollywood Cinematographer and Master AI Artist. "
        "Convert the user's basic idea into a highly detailed, ultra-realistic cinematic prompt. "
        "Add camera gear (ARRI Alexa 65, 85mm lens), lighting (Volumetric God-rays, Golden Hour), "
        "and render details (Unreal Engine 5, 8k, hyper-detailed skin texture). "
        "Output ONLY the final prompt. No explanations."
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": f"{system_prompt}\n\nUser idea: {user_prompt}"}]
        }],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500}
    }
    
    # Try all Gemini models with multi-key fallback
    for model in Config.GEMINI_MODELS:
        for api_key in Config.GEMINI_API_KEYS:
            try:
                logger.info(f"Trying Gemini Prompt Enhancement: {model}")
                client = _get_client()
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                resp = await client.post(url, json=payload)
                
                if resp.status_code == 429:
                    continue  # Rate limit, try next
                
                resp.raise_for_status()
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                logger.info(f"✅ Gemini prompt enhancement successful with {model}")
                return text
                
            except Exception as exc:
                logger.warning(f"Gemini {model} prompt enhancement failed: {exc}")
                continue
    
    logger.error("All Gemini prompt enhancement attempts failed")
    return user_prompt.strip()

async def enhance_prompt_groq(user_prompt: str) -> str:
    """Fallback: Uses Groq for prompt enhancement (optional)"""
    if not Config.GROQ_API_KEY:
        return user_prompt.strip()
    
    system_prompt = (
        "You are a Hollywood Cinematographer and Master AI Artist. "
        "Convert the user's basic idea into a highly detailed, ultra-realistic cinematic prompt. "
        "Add camera gear (ARRI Alexa 65, 85mm lens), lighting (Volumetric God-rays, Golden Hour), "
        "and render details (Unreal Engine 5, 8k, hyper-detailed skin texture). "
        "Output ONLY the final prompt. No explanations."
    )
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }
    try:
        data = await _post_json(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json_payload=payload,
            retries=1,  # Only 1 retry for Groq
        )
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.error("Groq prompt enhancement failed: %s", exc)
        return user_prompt.strip()

async def enhance_prompt_cinematic(user_prompt: str) -> str:
    """Hybrid: Gemini primary, Groq fallback"""
    # Try Gemini first (most reliable)
    result = await enhance_prompt_gemini(user_prompt)
    if result and result != user_prompt.strip():
        return result
    
    # Fallback to Groq if Gemini fails
    logger.info("Gemini prompt enhancement failed, trying Groq fallback...")
    result = await enhance_prompt_groq(user_prompt)
    return result

# ==========================================
# LAYER 2: IMAGE GENERATION
# ==========================================
async def generate_image(final_prompt: str, aspect_ratio: str = "16:9") -> tuple[None, str | None, str]:
    """Generates high-quality images with quality boosters"""
    dims = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (1024, 1024)}
    w, h = dims.get(aspect_ratio, (1024, 1024))
    
    # Add quality boosters
    quality_boosters = ", masterpiece, best quality, ultra-detailed, 8k, photorealistic, cinematic lighting"
    enhanced_prompt = f"{final_prompt}{quality_boosters}"
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    seed = int(time.time())
    
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?model=flux-realism&width={w}&height={h}&nologo=true&seed={seed}"
    )
    
    logger.info(f"Generating image with Flux-Realism")
    return None, url, "Flux-Realism"

# ==========================================
# LAYER 3: VISION DIRECTOR
# ==========================================
async def vision_director_gemini(image_bytes: bytes, current_context: str) -> dict[str, Any] | None:
    """Primary: Gemini Vision with multi-model + multi-key fallback"""
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    system_prompt = (
        "You are an Autonomous Art Director. Analyze the provided image. "
        "If it has bad anatomy, plastic skin, or AI artifacts, output a FIXED PROMPT. "
        "If it is a masterpiece, think of ONE subtle cinematic upgrade to evolve it for the next iteration. "
        'Output STRICT JSON: {"thought": "...", "next_prompt": "...", "caption": "...", "is_perfect": boolean}'
    )
    
    payload = {
        "contents": [{
            "parts": [
                {"text": f"{system_prompt}\nCurrent Context: {current_context}"},
                {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
            ]
        }],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    # Try all Gemini models with multi-key fallback
    for model in Config.GEMINI_MODELS:
        for api_key in Config.GEMINI_API_KEYS:
            try:
                logger.info(f"Trying Gemini Vision: {model}")
                client = _get_client()
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                resp = await client.post(url, json=payload)
                
                if resp.status_code == 429:
                    continue  # Rate limit, try next
                
                resp.raise_for_status()
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                
                if isinstance(parsed, dict) and "next_prompt" in parsed:
                    logger.info(f"✅ Gemini Vision successful with {model}")
                    return parsed
                    
            except Exception as exc:
                logger.warning(f"Gemini Vision {model} failed: {exc}")
                continue
    
    logger.error("All Gemini Vision attempts failed")
    return None

async def vision_director_groq(image_bytes: bytes, current_context: str) -> dict[str, Any] | None:
    """Fallback: Groq Vision (optional)"""
    if not Config.GROQ_API_KEY:
        return None
    
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    system_prompt = (
        "You are an Autonomous Art Director. Analyze the provided image. "
        "If it has bad anatomy, plastic skin, or AI artifacts, output a FIXED PROMPT. "
        "If it is a masterpiece, think of ONE subtle cinematic upgrade to evolve it for the next iteration. "
        'Output STRICT JSON: {"thought": "...", "next_prompt": "...", "caption": "...", "is_perfect": boolean}'
    )
    
    payload = {
        "model": "llama-3.2-90b-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{system_prompt}\nContext: {current_context}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }
        ],
        "temperature": 0.6,
        "max_tokens": 1024,
    }
    
    try:
        data = await _post_json(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json_payload=payload,
            retries=1,
        )
        text = data["choices"][0]["message"]["content"].strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "next_prompt" in parsed:
            logger.info("✅ Groq Vision successful")
            return parsed
    except Exception as exc:
        logger.error("Groq vision failed: %s", exc)
        return None

async def vision_director(image_bytes: bytes, current_context: str) -> dict[str, Any] | None:
    """Hybrid: Gemini primary, Groq fallback"""
    # Try Gemini first (most reliable with multi-key fallback)
    result = await vision_director_gemini(image_bytes, current_context)
    if result:
        return result
    
    # Fallback to Groq if Gemini fails
    logger.info("Gemini Vision failed, trying Groq fallback...")
    result = await vision_director_groq(image_bytes, current_context)
    return result