import asyncio
import logging
from typing import Any, Dict, List

import httpx

from app.config import Settings
from app.errors import ai_failed

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def complete_json(self, messages: List[Dict[str, str]]) -> str:
        if not self.settings.openai_api_key:
            raise ai_failed("OPENAI_API_KEY is not configured")

        payload = {
            "model": self.settings.openai_model,
            "messages": messages,
            "temperature": 0.3,
        }

        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        last_error = ""

        for attempt in range(self.settings.ai_http_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.settings.ai_timeout_seconds) as client:
                    response = await client.post(
                        self.settings.chat_completions_url,
                        headers=headers,
                        json=payload,
                    )

                if response.status_code >= 500 and attempt < self.settings.ai_http_retries:
                    last_error = f"AI HTTP {response.status_code}: {response.text[:500]}"
                    await asyncio.sleep(0.6 * (attempt + 1))
                    continue

                response.raise_for_status()
                data = response.json()
                return self._extract_content(data)
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                last_error = str(exc)
                if attempt < self.settings.ai_http_retries:
                    await asyncio.sleep(0.6 * (attempt + 1))
                    continue

        raise ai_failed(last_error)

    @staticmethod
    def _extract_content(data: Dict[str, Any]) -> str:
        choices = data.get("choices")
        if not choices:
            raise ValueError("AI response missing choices")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            combined = "".join(parts).strip()
            if combined:
                return combined

        raise ValueError("AI response missing message content")
