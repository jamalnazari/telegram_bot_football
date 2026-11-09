"""client Gemini generateContent. کلید اختیاری است: اگر نبود، generate None برمی‌گرداند
و سیستم با قالب آماده کامل کار می‌کند."""

from __future__ import annotations

import json
import sys

import requests

BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiClient:
    def __init__(
        self,
        api_key: str | None,
        model: str = "gemini-2.5-flash",
        max_output_tokens: int = 400,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or None
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def generate(self, system: str, user: str) -> str | None:
        """خروجی متن کپشن از مدل، يا None در صورت عدم دسترسی/خطا."""
        if not self.api_key:
            return None
        url = f"{BASE}/models/{self.model}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "maxOutputTokens": self.max_output_tokens,
                "temperature": 0.7,
            },
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            print(f"[gemini] خطای شبکه: {exc}", file=sys.stderr)
            return None
        if resp.status_code != 200:
            print(
                f"[gemini] خطای API {resp.status_code}: {resp.text[:200]}",
                file=sys.stderr,
            )
            return None
        try:
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, json.JSONDecodeError):
            return None
