"""نگهبان اعداد: هیچ عدد در کپشن نباید از داده‌ی واقعیت جداگانه ایجاد شود.

روش: همه‌ی اعداد موجود در بسته (بازگشتی روی مقادیر، بدون فیلد utc) جمع می‌کنیم؛
ارقام فارسی را به لاتین تبدیل می‌کنیم؛ تمام توکن‌های عددی متن تولیدشده را استخراج
می‌کنیم؛ اگر عددی در مجموعه‌ی مجاز نبود، کل خروجی مدل رد می‌شود.
"""

from __future__ import annotations

import re

from text.numerals import normalize_digits

NUM_RE = re.compile(r"\d+")


def allowed_numbers(facts) -> set[str]:
    """هر آرایه‌ی رقمی در بسته (به استثنای فیلد utc) را به مجموعه‌ی مجاز اضافه می‌کند."""
    allowed: set[str] = set()

    def walk(value) -> None:
        if isinstance(value, dict):
            for key, val in value.items():
                if key == "utc":
                    continue
                walk(val)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, bool):
            pass
        elif isinstance(value, (int, float)):
            allowed.add(normalize_digits(str(value)))
        elif isinstance(value, str):
            for m in NUM_RE.findall(normalize_digits(value)):
                allowed.add(m)

    walk(facts)
    return allowed


def text_numbers(text: str) -> set[str]:
    """توکن‌های عددی متن (ارقام فارسی ابتدا به لاتین تبدیل می‌شود)."""
    return set(NUM_RE.findall(normalize_digits(text)))


def check(text: str, facts) -> tuple[bool, str]:
    """بررسی نگهبان: (مجاز، دلیل رد شدن)."""
    allowed = allowed_numbers(facts)
    found = text_numbers(text)
    bogus = found - allowed
    if bogus:
        ordered = sorted(bogus, key=lambda x: (len(x), x))
        return False, f"عدد خارج از داده‌ی بسته: {ordered}"
    return True, ""
