"""ReelIQ Backend — Groq AI Client"""
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from app.config import get_settings

settings = get_settings()

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are ReelIQ, an elite Instagram content strategist and video analyst with 10 years of experience growing creator accounts from 0 to 1M. You are direct, data-driven, and slightly critical when work is mediocre. You give specific, actionable recommendations backed by performance data. You never give generic advice. Respond only in the requested JSON format."""


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }


def _message_content(prompt: str, images: Optional[List[Dict[str, Any]]] = None) -> Any:
    if not images:
        return prompt

    content: List[Dict[str, Any]] = []
    for image in images:
        media_type = image.get("media_type", "image/jpeg")
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{image['data']}",
            },
        })
    content.append({"type": "text", "text": prompt})
    return content


def _payload(
    prompt: str,
    system: str,
    max_tokens: int,
    temperature: float,
    images: Optional[List[Dict[str, Any]]] = None,
    stream: bool = False,
) -> Dict[str, Any]:
    return {
        "model": settings.GROQ_VISION_MODEL if images else settings.GROQ_TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": _message_content(prompt, images)},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }


def call_groq(
    prompt: str,
    system: str = SYSTEM_PROMPT,
    max_tokens: int = 4096,
    temperature: float = 0.3,
    images: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Synchronous Groq call for Celery workers."""
    with httpx.Client(timeout=120) as client:
        response = client.post(
            GROQ_CHAT_COMPLETIONS_URL,
            headers=_headers(),
            json=_payload(prompt, system, max_tokens, temperature, images),
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def call_groq_async(
    prompt: str,
    system: str = SYSTEM_PROMPT,
    max_tokens: int = 4096,
    temperature: float = 0.3,
    images: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Async Groq call for FastAPI endpoints."""
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            GROQ_CHAT_COMPLETIONS_URL,
            headers=_headers(),
            json=_payload(prompt, system, max_tokens, temperature, images),
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def stream_groq(
    prompt: str,
    system: str = SYSTEM_PROMPT,
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> AsyncGenerator[str, None]:
    """Streaming Groq response for real-time AI output."""
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            GROQ_CHAT_COMPLETIONS_URL,
            headers=_headers(),
            json=_payload(prompt, system, max_tokens, temperature, stream=True),
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                event = line.removeprefix("data: ").strip()
                if event == "[DONE]":
                    break
                chunk = json.loads(event)
                delta = chunk["choices"][0].get("delta", {})
                if delta.get("content"):
                    yield delta["content"]


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """Parse JSON responses, handling markdown code blocks."""
    text = response_text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            try:
                return {"items": json.loads(text[start:end])}
            except json.JSONDecodeError:
                pass

        return {"raw_response": response_text, "error": "Failed to parse JSON"}
