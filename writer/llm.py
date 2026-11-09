"""مسیر مدل زبانی: پرامپت سیستمی فارسی + فراخوانی Gemini."""

from __future__ import annotations

import json

SYSTEM_PROMPT = (
    "تو یک نویسنده‌ی محتوای فوتبالی برای کانال تلگرام فارسی هستی.\n"
    "قواعد سخت:\n"
    "۱) فقط از اطلاعات دقیق JSON داده‌شده استفاده کن؛ هیچ عدد، آمار، نام تیم، "
    "نام بازیکن یا تاریخچه‌ی که در JSON نیست اضافه نکن.\n"
    "۲) لحن محاوره‌ای، پرانرژی و جذاب.\n"
    "۳) ۳ تا ۸ خط.\n"
    "۴) حداکثر ۴ هشتگ فارسی.\n"
    "۵) خروجی فقط متن کپشن، بدون توضیح اضافی و بدون عنوان."
)


def build_user_prompt(facts: dict) -> str:
    return (
        f"نوع پست: {facts.get('type', '')}\n"
        "JSON:\n" + json.dumps(facts, ensure_ascii=False, indent=2)
    )


def generate_caption(facts: dict, gemini, model_cfg: dict) -> str | None:
    """خروجی مدل زبانی، يا None اگر مدل غیرفعال باشد/خطا دهد."""
    if not model_cfg.get("enabled", True):
        return None
    if gemini is None or not getattr(gemini, "enabled", False):
        return None
    return gemini.generate(
        SYSTEM_PROMPT,
        build_user_prompt(facts),
    )
