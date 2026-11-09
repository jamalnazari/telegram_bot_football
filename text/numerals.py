"""تبدیل ارقام لاتين ↔ فارسی و نحوه‌ی نمایش اعداد."""

import re

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
FA_TO_LATIN = str.maketrans(FA_DIGITS, "0123456789")
LATIN_TO_FA = str.maketrans("0123456789", FA_DIGITS)

_DECIMAL_RE = re.compile(r"(?<=\d)\.(?=\d)")


def fa_num(text: str) -> str:
    """ارداف كل متن: ارقام لاتين → فارسی و نقطه ركاب decimal → نيم‌فاصله."""
    out = text.translate(LATIN_TO_FA)
    return _DECIMAL_RE.sub("٫", out)


def normalize_digits(text: str) -> str:
    """ارقام فارسی → لاتين (برای مقایسه‌ی اعداد در نگهبان اعداد)."""
    return text.translate(FA_TO_LATIN)


def to_persian_number(value) -> str:
    """تبدیل عدد (int/float) به رشته‌ی ارقام فارسی."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return fa_num(str(value))
