"""Bot API تلگرام: sendPhoto (کارت + کپشن) و sendMessage (متن).

- کپشن حداکثر ۱۰۲۴ کاراکتر است → کوتاه می‌کنیم.
- دکمه‌ی شیشه‌ای با inline_keyboard اگر لینک منبع تنظیم شده باشد.
- روی ۴۲۹ مقدار retry_after را می‌خوانیم و صبر می‌کنیم.
- حالت dry_run: بدون توکن چیزی نمی‌فرستد ولی خط لوله اجرا می‌شود.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

API_BASE = "https://api.telegram.org/bot{token}/{method}"
MAX_CAPTION = 1024


class TelegramError(Exception):
    pass


class TelegramClient:
    def __init__(self, token: str | None, chat_id: str | None, dry_run: bool = False):
        self.token = token
        self.chat_id = chat_id
        self.dry_run = dry_run or not token

    def _post(self, method: str, data: dict | None = None, files: dict | None = None) -> dict:
        if self.dry_run:
            print(
                f"[telegram:dry-run] {method} chat={self.chat_id} "
                f"files={list((files or {}).keys())} data_keys={list((data or {}).keys())}"
            )
            return {"ok": True}
        if not self.token:
            raise TelegramError("توکن ربات تنظیم نشده")
        url = API_BASE.format(token=self.token, method=method)
        last_error = ""
        for attempt in range(5):
            try:
                resp = requests.post(url, data=data, files=files, timeout=30)
            except requests.RequestException as exc:
                raise TelegramError(f"خطای شبکه: {exc}") from exc
            if resp.status_code == 429:
                try:
                    payload = resp.json()
                    wait = float(payload["parameters"]["retry_after"])
                except (ValueError, KeyError):
                    wait = 5.0
                time.sleep(wait)
                continue
            if resp.status_code != 200:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                break
            result = resp.json()
            if not result.get("ok"):
                raise TelegramError(str(result.get("description", result)))
            return result
        raise TelegramError(last_error or "خطای ناشناخته")

    def send_photo(self, image_path: str | Path, caption: str, source_link: str = "") -> dict:
        caption = caption[:MAX_CAPTION]  # کپشن حداکثر ۱۰۲۴ کاراکتر است
        data = {"chat_id": self.chat_id, "caption": caption}
        if source_link:
            data["reply_markup"] = json.dumps(
                {"inline_keyboard": [[{"text": "مشاهده منبع", "url": source_link}]]}
            )
        files = {"photo": open(image_path, "rb")}
        try:
            return self._post("sendPhoto", data=data, files=files)
        finally:
            files["photo"].close()

    def send_message(self, text: str) -> dict:
        data = {"chat_id": self.chat_id, "text": text[:MAX_CAPTION]}
        return self._post("sendMessage", data=data)
