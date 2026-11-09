"""لودر تنظیمات: config.yaml + متغیرهای محیطی + لودر ساده‌ی .env (بدون وابستگی اضافی)."""

from __future__ import annotations

import copy
import os
from pathlib import Path

import yaml

DEFAULTS: dict = {
    "channel": {
        "username": "my_football_channel",
        "brand": "برندِ کانال",
        "source_link": "",
    },
    "timezone": "Asia/Tehran",
    "competitions": [
        {"code": "PL", "fa": "لیگ برتر انگلیس"},
        {"code": "PD", "fa": "لالیگا"},
        {"code": "SA", "fa": "سری آ"},
        {"code": "BL1", "fa": "بوندس‌لیگا"},
        {"code": "CL", "fa": "لیگ قهرمانان اروپا"},
    ],
    "iran_league": {
        "enabled": True,
        "league_id": 4742,
        "fa": "لیگ برتر خلیج فارس",
        "season": "2026-2027",
    },
    "posts": {
        "daily_digest_hour": 9,
        "stat_card_hour": 14,
        "recap_hour": 10,
        "reminder_hours_before": 12,
    },
    "theme": {
        "bg_top": "#0B1B2B",
        "bg_bottom": "#111C26",
        "accent": "#00E08A",
        "accent2": "#FFC247",
        "text": "#FFFFFF",
        "muted": "#93A4B5",
    },
    "model": {
        "enabled": True,
        "provider": "gemini",
        "name": "gemini-2.5-flash",
        "max_output_tokens": 400,
    },
}

ENV_KEYS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHANNEL_ID",
    "FOOTBALL_DATA_TOKEN",
    "THESPORTSDB_KEY",
    "GEMINI_API_KEY",
]


def load_env(path: str | Path = ".env") -> None:
    """لودر ساده‌ی .env: خط به خط، بدون توکن‌سازی اضافی. never override موجودها."""
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str | Path = "config.yaml") -> dict:
    """خواندن config.yaml روی defaults، return یک dict یکدست."""
    data: dict = {}
    p = Path(path)
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return _deep_merge(DEFAULTS, data)
