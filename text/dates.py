"""تاریخ و ساعت به وقت تهران، با zoneinfo + jdatetime. هرگز از ساعت سیستم استفاده نکنید."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import jdatetime

from .numerals import fa_num

TEHRAN = ZoneInfo("Asia/Tehran")

WEEKDAYS_FA = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]


def now_tehran() -> datetime:
    """اکنون به وقت تهران."""
    return datetime.now(TEHRAN)


def to_utc(dt: datetime) -> datetime:
    """تبدیل datetime به UTC (حالت aware)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TEHRAN)
    return dt.astimezone(timezone.utc)


def tehran_date_of(dt_utc: datetime) -> date:
    """تاریخ تهران یک datetime UTC."""
    return dt_utc.astimezone(TEHRAN).date()


def tehran_day_bounds(day: date, margin_hours: int = 2) -> tuple[datetime, datetime]:
    """محدوده‌ی UTC یک «روز تهران» با حاشیه‌ی margin_hours (جلو و عقب).

    یک روز تهران با یک روز UTC یکی نیست (تهران UTC+3:30)؛ این تابع بازه را
    دقیق محاسبه می‌کند تا بازه‌ی query همیشه روز هدف را پوشش دهد.
    """
    start = datetime.combine(day, time.min, tzinfo=TEHRAN) - timedelta(hours=margin_hours)
    end = datetime.combine(day, time.max, tzinfo=TEHRAN) + timedelta(hours=margin_hours)
    return to_utc(start), to_utc(end)


def _jdatetime(d: date | datetime):
    """تبدیل gregorian date/datetime به jdatetime."""
    if isinstance(d, datetime):
        return jdatetime.datetime.fromgregorian(datetime=d)
    return jdatetime.date.fromgregorian(date=d)


def persian_date_str(d: date | datetime) -> str:
    """تاریخ شمسی فارسی، مثل ۱۴۰۵/۰۸/۱۶."""
    jd = _jdatetime(d)
    return f"{fa_num(str(jd.year))}/{fa_num(f'{jd.month:02d}')}/{fa_num(f'{jd.day:02d}')}"


def persian_datetime_str(d: date | datetime) -> str:
    """تاریخ + روز الأسبوع فارسی، مثل ۱۴۰۵/۰۸/۱۶ — پنجشنبه."""
    jd = _jdatetime(d)
    date_part = f"{fa_num(str(jd.year))}/{fa_num(f'{jd.month:02d}')}/{fa_num(f'{jd.day:02d}')}"
    return f"{date_part} — {WEEKDAYS_FA[jd.weekday()]}"


def persian_time_str(dt: datetime) -> str:
    """ساعت به زمان تهران، مثل ۲۰:۳۰."""
    return fa_num(f"{dt.hour:02d}:{dt.minute:02d}")


def parse_persian_date(s: str) -> date:
    """پارسی تاریخ فارسی (۱۴۰۵/۰۸/۱۸) را به gregorian date تبدیل می‌کند."""
    from .numerals import normalize_digits

    y, m, d = (int(p) for p in normalize_digits(s).split("/"))
    gy, gm, gd = jdatetime.JalaliToGregorian(y, m, d).getGregorianList()
    return date(gy, gm, gd)
