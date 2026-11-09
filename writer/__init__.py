"""لایه‌ی نوشتار: کپشن فارسی از دو مسیر — قالب آماده (تکاملی قطعی) و مدل زبانی
(با نگهبان اعداد)."""

from __future__ import annotations

import sys

from text.numerals import fa_num
from writer import guard, llm, templates

__all__ = ["make_caption"]


def make_caption(facts: dict, cfg: dict, gemini=None) -> str:
    """کپشن نهایی: مسیر مدل زبانی با نگهبان اعداد، و در صورت عدم مجاز بودن fallback به قالب آماده قالب آماده."""
    model_cfg = (cfg or {}).get("model", {})
    caption: str | None = None
    if model_cfg.get("enabled", True) and gemini is not None:
        raw = llm.generate_caption(facts, gemini, model_cfg)
        if raw:
            ok, reason = guard.check(raw, facts)
            if ok:
                caption = raw
            else:
                print(
                    f"[writer] خروجی مدل رد شد، استفاده از قالب آماده: {reason}",
                    file=sys.stderr,
                )
    if caption is None:
        caption = templates.render(facts)
    return fa_num(caption)
