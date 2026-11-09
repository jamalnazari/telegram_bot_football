"""حافظه‌ی ضدتکرار: state/posted.json با کلیدهای یکتا.

اگر کلید دیده شد، دوباره پست نمی‌کنیم. حداکثر ۴۰۰ کلید آخر حفظ می‌شود.
این تنها راه بقای حافظه بین اجراهای Actions است (فایل در گیت کامیت می‌شود).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

MAX_KEYS = 400


class StateStore:
    def __init__(self, path: str | Path = "state/posted.json"):
        self.path = Path(path)
        self.keys: dict[str, str] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.keys = {}
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.keys = {str(k): str(v) for k, v in data.items()}
        except (json.JSONDecodeError, OSError):
            self.keys = {}

    def seen(self, key: str) -> bool:
        return key in self.keys

    def remember(self, key: str) -> None:
        if key not in self.keys:
            self.keys[key] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _trim(self) -> None:
        items = list(self.keys.items())
        if len(items) > MAX_KEYS:
            self.keys = dict(items[-MAX_KEYS:])

    def save(self) -> None:
        self._trim()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.keys, ensure_ascii=False, indent=2), encoding="utf-8"
        )
