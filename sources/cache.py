"""کش دیسکی با TTL: تا زمانی که API پلن رایگان (مثلاً ۱۰ درخواست در دقیقه)
پشت سر هم فراخوانی نشود."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

# TTL انیستی: برنامه‌ی بازی‌ها ۲۰ دقیقه، جدول و گلزنان ۶ ساعت
TTL_MATCHES = 20 * 60
TTL_TABLES = 6 * 60 * 60


class DiskCache:
    def __init__(self, root: str | Path = ".cache"):
        self.root = Path(root) / "sources"
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, namespace: str, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
        return self.root / f"{namespace}-{digest}.json"

    def get(self, namespace: str, key: str, ttl: float):
        p = self._path(namespace, key)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - data.get("ts", 0) > ttl:
            return None
        return data.get("data")

    def set(self, namespace: str, key: str, data) -> None:
        p = self._path(namespace, key)
        p.write_text(
            json.dumps({"ts": time.time(), "data": data}, ensure_ascii=False),
            encoding="utf-8",
        )
