"""متن‌نویسی bidi‌آگاه با Pillow.

تل فنی: دو مسیر exists:
- اگر Pillow با libraqm کامپایل شده (PIL.features.check("raqm") == True)،
  خود پی‌ال bidi و shaping را انجام می‌دهد؛ در این حالت باید متن خام را با
  direction="rtl"/"ltr" و language="fa" بدمد. از arabic_reshaper + get_display
  استفاده نکنید (متن دوبار معکوس و خوانا نمی‌شود).
- اگر raqm نیست، مسیر reshaper + python-bidi را برو: reshape → get_display.

جهت را از محتوا تشخیص می‌دهیم (وجود حروف عربی/فارسی → rtl، وگرنه ltr)،
وگرنه نام تیم‌های لاتین برعکس می‌شوند. textlength هم همان پارامترها را می‌گیرد.

نیم‌فاصله (ZWNJ) با raqm درست کار می‌کند؛ متن را pre-process نکنید که ZWNJ را
حذف کنید.
"""

from __future__ import annotations

import re

from PIL import ImageDraw, features

HAS_RAQM = bool(features.check("raqm"))

# حروف عربی، فارسی و نمادهای مرتبط
_RTL_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)

# سراغ‌رسانی چیدمان برای تست (environment variable LAYOUT_AUDIT=1)
_RECORDED: list | None = None


def enable_recording() -> None:
    global _RECORDED
    _RECORDED = []


def get_recorded() -> list:
    return list(_RECORDED or [])


def detect_direction(text: str) -> str:
    """جهت متن را از محتوا تشخیص می‌دهد: فارسی/عربی → rtl، وگرنه ltr."""
    return "rtl" if _RTL_RE.search(text) else "ltr"


def _shape(text: str, direction: str) -> str:
    """shaping متن برای مسیر بدون raqm."""
    if HAS_RAQM or direction == "ltr" or not text:
        return text
    import arabic_reshaper

    return arabic_reshaper.reshape(text)


def _display(text: str, direction: str) -> str:
    """bidi reordering برای مسیر بدون raqm."""
    if HAS_RAQM or not text:
        return text
    from bidi.algorithm import get_display

    # python-bidi ۰٫۴+: direction به base_dir تبدیل شد ("R" برای rtl، "L" برای ltr)
    return get_display(text, base_dir="R" if direction == "rtl" else "L")


def _language(direction: str) -> str:
    return "fa" if direction == "rtl" else "en"


def prepare(text: str) -> tuple[str, str]:
    """داده‌ی آماده برای draw/textlength: (متن ظاهری، جهت)."""
    direction = detect_direction(text)
    return _display(_shape(text, direction), direction), direction


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy,
    text: str,
    font,
    fill,
    anchor: str = "la",
) -> None:
    """متن‌نویسی bidi‌آگاه. textlength هم باید همین پارامترها را استفاده کند."""
    if not text:
        return
    direction = detect_direction(text)
    if HAS_RAQM:
        draw.text(
            xy,
            text,
            font=font,
            fill=fill,
            anchor=anchor,
            direction=direction,
            language=_language(direction),
        )
    else:
        drawn = _display(_shape(text, direction), direction)
        draw.text(xy, drawn, font=font, fill=fill, anchor=anchor)
    if _RECORDED is not None:
        _RECORDED.append(
            {
                "text": text,
                "xy": tuple(xy),
                "size": getattr(font, "size", 0),
                "anchor": anchor,
                "direction": direction,
                "width": text_length(draw, text, font),
            }
        )


def text_length(draw: ImageDraw.ImageDraw, text: str, font) -> float:
    """پهنه‌ی ظاهری متن با همان تنظیمات draw_text."""
    if not text:
        return 0.0
    direction = detect_direction(text)
    if HAS_RAQM:
        return draw.textlength(
            text, font=font, direction=direction, language=_language(direction)
        )
    drawn = _display(_shape(text, direction), direction)
    return draw.textlength(drawn, font=font)


def fit_font(draw: ImageDraw.ImageDraw, text: str, font, max_width: float, min_size: int = 24):
    """سایز font را تا جایی کاهش می‌دهد که متن در max_width بگنجد."""
    size = font.size
    while size > min_size:
        if text_length(draw, text, font) <= max_width:
            return font
        size -= 2
        font = font.font_variant(size=size)
    return font
