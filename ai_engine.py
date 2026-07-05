import httpx
import base64
import time
import json
import urllib.parse
import logging
from config import Config

logger = logging.getLogger(__name__)

# ==========================================
# LAYER 1: THE CINEMATIC PROMPT INJECTOR
# ==========================================
async def enhance_prompt_cinematic(user_prompt: str) -> str:
    """
    [R&D CONTEXT]: Raw user prompts are boring. We use Groq (Llama-3.1-70B) 
    to rewrite the prompt into a Midjourney v6 / Hollywood Cinematographer style.
    """
    system_prompt = (
        "You are a Hollywood Cinematographer and Master AI Artist. "
        "Convert the user's basic idea into a highly detailed, ultra-realistic cinematic prompt. "
        "Add camera gear (ARRI Alexa 65, 85mm lens), lighting (Volumetric God-rays, Golden Hour), "
        "and render details (Unreal Engine 5, 8k, hyper-detailed skin texture). "
        "Output ONLY the final prompt. No explanations."
    )
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {Config.GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq Prompt Enhancement Error: {e}")
            
    return user_prompt # Fallback to raw prompt if Groq fails

# ==========================================
# LAYER 2: THE FLUX-REALISM GENERATOR
# ==========================================
async def generate_image(final_prompt: str, aspect_ratio: str = "16:9") -> tuple:
    """
    [R&D CONTEXT]: We bypass standard APIs and hit Pollinations 'flux-realism'.
    This specific model is fine-tuned for human skin pores, eye catchlights, and camera bokeh.
    """
    # Map aspect ratios to pixels
    dims = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (1024, 1024)}
    w, h = dims.get(aspect_ratio, (1024, 1024))
    
    encoded_prompt = urllib.parse.quote(final_prompt)
    seed = int(time.time())
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux-realism&width={w}&height={h}&nologo=true&seed={seed}"
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.content, url, "Flux-Realism"
        except Exception as e:
            logger.error(f"Pollinations Generation Error: {e}")
            
    return None, None, "Failed"

# ==========================================
# LAYER 3: THE AUTONOMOUS VISION DIRECTOR
# ==========================================
async def vision_director(image_bytes: bytes, current_context: str) -> dict:
    """
    [R&D CONTEXT]: Gemini 1.5 Flash analyzes the generated image.
    It acts as an Art Director, deciding if the image is perfect or needs evolution.
    """
    img_b64 = base64.b64encode(image_bytes).decode('utf-8')
    
    system_prompt = (
        "You are an Autonomous Art Director. Analyze the provided image. "
        "If it has bad anatomy, plastic skin, or AI artifacts, output a FIXED PROMPT. "
        "If it is a masterpiece, think of ONE subtle cinematic upgrade (e.g., change weather, add neon reflections) "
        "to evolve it for the next iteration. Output STRICT JSON: "
        '{"thought": "your inner monologue", "next_prompt": "the exact new prompt", "caption": "instagram caption with 5 hashtags", "is_perfect": boolean}'
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={Config.GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [
            {"text": f"{system_prompt}\n\nCurrent Context: {current_context}"},
            {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
        ]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini Vision Error: {e}")
    return None
