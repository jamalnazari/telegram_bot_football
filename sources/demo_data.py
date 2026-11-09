"""داده‌ی نمونه (demo): بدون هیچ کلیدی، همه‌ی شش نوع بسته با داده‌ی ثابت.

این تابع برای تست و پیش‌نمایش حیاتی است. مقادیر با ارقام لاتين نگه داشته
می‌شوند؛ تبدیل به ارقام فارسی در لایه‌های بالاتر انجام می‌شود.
"""

from __future__ import annotations

from datetime import date

from text.dates import persian_date_str


def _today() -> str:
    return persian_date_str(date.today())


def demo_package(kind: str) -> dict:
    """ برگرداند بسته‌ی demo برای kind: fixtures | recap | scorers | standings | hat_tricks | reminder."""
    today = _today()

    if kind == "fixtures":
        return {
            "type": "fixtures",
            "date": today,
            "count": 5,
            "groups": [
                {
                    "competition": "لیگ برتر انگلیس",
                    "code": "PL",
                    "matches": [
                        {"home": "آرسنال", "away": "تاتنهام", "time": "۲۰:۳۰", "utc": "2026-11-09T17:00:00Z"},
                        {"home": "چلسی", "away": "منچسترسیتی", "time": "۲۳:۰۰", "utc": "2026-11-09T19:30:00Z"},
                    ],
                },
                {
                    "competition": "لالیگا",
                    "code": "PD",
                    "matches": [
                        {"home": "ریالمادرید", "away": "بارسلونا", "time": "۲۲:۰۰", "utc": "2026-11-09T18:30:00Z"},
                    ],
                },
                {
                    "competition": "بوندس‌لیگا",
                    "code": "BL1",
                    "matches": [
                        {"home": "بروسیادورتموند", "away": "بایرنمونیخ", "time": "۲۱:۳۰", "utc": "2026-11-09T18:00:00Z"},
                        {"home": "لیورپول", "away": "منچستريونايتد", "time": "۲۱:۰۰", "utc": "2026-11-09T17:30:00Z"},
                    ],
                },
                {
                    "competition": "لیگ برتر خلیج فارس",
                    "code": "IRN",
                    "matches": [
                        {"home": "پرسپولیس", "away": "استقلال", "time": "۲۱:۰۰", "utc": "2026-11-09T17:30:00Z"},
                    ],
                },
            ],
        }

    if kind == "recap":
        return {
            "type": "recap",
            "date": today,
            "count": 4,
            "matches": [
                {"home": "ریالمادرید", "away": "سوسیداد", "time": "۲۰:۰۰", "utc": "2026-11-08T16:30:00Z", "score": "۴-۲", "total": 6, "competition": "لالیگا", "code": "PD"},
                {"home": "لیورپول", "away": "آرسنال", "time": "۱۸:۰۰", "utc": "2026-11-08T14:30:00Z", "score": "۳-۲", "total": 5, "competition": "لیگ برتر انگلیس", "code": "PL"},
                {"home": "تاتنهام", "away": "چلسی", "time": "۲۱:۰۰", "utc": "2026-11-08T17:30:00Z", "score": "۲-۲", "total": 4, "competition": "لیگ برتر انگلیس", "code": "PL"},
                {"home": "اتلتیکبیلباو", "away": "اسپورتینگخیخون", "time": "۲۲:۰۰", "utc": "2026-11-08T18:30:00Z", "score": "۱-۰", "total": 1, "competition": "لالیگا", "code": "PD"},
            ],
        }

    if kind == "scorers":
        return {
            "type": "scorers",
            "date": today,
            "count": 4,
            "entries": [
                {"rank": 1, "player": "هالند", "team": "منچسترسیتی", "goals": 15, "competition": "لیگ برتر انگلیس"},
                {"rank": 2, "player": "ساکا", "team": "آرسنال", "goals": 13, "competition": "لیگ برتر انگلیس"},
                {"rank": 3, "player": "مسی", "team": "آنژی مکسیکو", "goals": 12, "competition": "لالیگا"},
                {"rank": 4, "player": "هاری کین", "team": "بایرنمونیخ", "goals": 11, "competition": "بوندس‌لیگا"},
            ],
        }

    if kind == "standings":
        return {
            "type": "standings",
            "date": today,
            "count": 5,
            "entries": [
                {"rank": 1, "team": "آرسنال", "competition": "لیگ برتر انگلیس", "played": 12, "won": 9, "drawn": 2, "lost": 1, "gd": 18, "points": 29},
                {"rank": 2, "team": "منچسترسیتی", "competition": "لیگ برتر انگلیس", "played": 12, "won": 8, "drawn": 3, "lost": 1, "gd": 14, "points": 27},
                {"rank": 3, "team": "چلسی", "competition": "لیگ برتر انگلیس", "played": 12, "won": 7, "drawn": 3, "lost": 2, "gd": 9, "points": 24},
                {"rank": 4, "team": "تاتنهام", "competition": "لیگ برتر انگلیس", "played": 12, "won": 6, "drawn": 3, "lost": 3, "gd": 5, "points": 21},
                {"rank": 5, "team": "لیورپول", "competition": "لیگ برتر انگلیس", "played": 12, "won": 6, "drawn": 2, "lost": 4, "gd": 2, "points": 20},
            ],
        }

    if kind == "hat_tricks":
        return {
            "type": "hat_tricks",
            "date": today,
            "count": 1,
            "entries": [
                {"rank": 1, "player": "ساکا", "team": "آرسنال", "goals": 3, "match": "آرسنال — تاتنهام"},
            ],
        }

    if kind == "reminder":
        return {
            "type": "reminder",
            "date": today,
            "hours_before": 12,
            "home": "ریالمادرید",
            "away": "بارسلونا",
            "time": "۲۲:۰۰",
            "utc": "2026-11-10T18:30:00Z",
            "competition": "لالیگا",
            "code": "PD",
        }

    raise ValueError(f"نوع demo نامعتبر: {kind}")


ALL_KINDS = ["fixtures", "recap", "scorers", "standings", "hat_tricks", "reminder"]
