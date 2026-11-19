import asyncio
import json
import google.generativeai as genai
from core.config import settings

genai.configure(api_key=settings.gemini_api_key)
_model = genai.GenerativeModel("gemini-2.0-flash")


async def call_gemini(prompt: str) -> str:
    response = await asyncio.to_thread(_model.generate_content, prompt)
    return response.text


async def call_gemini_json(prompt: str) -> dict | list:
    text = await call_gemini(prompt + "\n\nReturn valid JSON only. No markdown code blocks.")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return json.loads(cleaned)
