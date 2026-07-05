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
            timeout=httpx.Timeout(30.0, connect=10.0),
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
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
    raise RuntimeError(f"Request failed after {retries + 1} attempts") from last_error


async def enhance_prompt_cinematic(user_prompt: str) -> str:
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
    }

    try:
        data = await _post_json(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json_payload=payload,
        )
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.error("Groq prompt enhancement failed: %s", exc)
        return user_prompt.strip()


async def generate_image(final_prompt: str, aspect_ratio: str = "16:9") -> tuple[None, str | None, str]:
    dims = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (1024, 1024)}
    w, h = dims.get(aspect_ratio, (1024, 1024))
    encoded_prompt = urllib.parse.quote(final_prompt)
    seed = int(time.time())
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?model=flux-realism&width={w}&height={h}&nologo=true&seed={seed}"
    )
    return None, url, "Flux-Realism"


async def vision_director(image_bytes: bytes, current_context: str) -> dict[str, Any] | None:
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    system_prompt = (
        "You are an Autonomous Art Director. Analyze the provided image. "
        "If it has bad anatomy, plastic skin, or AI artifacts, output a FIXED PROMPT. "
        "If it is a masterpiece, think of ONE subtle cinematic upgrade to evolve it for the next iteration. "
        'Output STRICT JSON: {"thought": "...", "next_prompt": "...", "caption": "...", "is_perfect": boolean}'
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_prompt}\n\nCurrent Context: {current_context}"},
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
                ]
            }
        ],
        "generationConfig": {"response_mime_type": "application/json"},
    }

    try:
        data = await _post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={Config.GEMINI_API_KEY}",
            json_payload=payload,
        )
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception as exc:
        logger.error("Gemini vision failed: %s", exc)
    return None
