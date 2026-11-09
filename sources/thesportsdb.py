"""thesportsdb.com نسخه v1 با کلید (لیگ ایران)."""

from __future__ import annotations

import json
import time

from sources.cache import DiskCache, TTL_MATCHES, TTL_TABLES
from sources.http import HttpError, http_get

BASE = "https://www.thesportsdb.com/api/v1/json"

# نام تیم‌های ایرانی به فارسی (لیگ برتر خلیج فارس)
TEAM_NAMES_FA: dict[str, str] = {
    "Persepolis": "پرسپولیس",
    "Esteghlal": "استقلال",
    "Sepahan": "سپاهان",
    "Zob Ahan": "ذوب‌آهن",
    "Tractor Sazi": "تراکتور",
    "Tractor": "تراکتور",
    "Saipa": "سایرپا",
    "Naft Masjed Soleyman": "نفت مسجدسلیمان",
    "Naft MIS": "نفت مسجدسلیمان",
    "Gostaresh FC": "گوسترس",
    "Aluminium Arak": "آلومینیوم اراک",
    "Shahrdari Tabriz": "شهرداری تبریز",
    "Shahrdari Mahshahr": "شهرداری بندر ماهشهر",
    "Machine Sazi": "ماشین‌سازی",
    "Sanat Naft": "صنعت نفت",
    "Pars Jonoubi": "پرس جونوبی",
    "Kheybar Khorramabad": "خیبر خرم‌آباد",
    "Kheybar": "خیبر",
    "Baadraan Tehran": "بادران",
    "Arman Gohar": "ارمان گهر",
    "Chadormalou": "چادرمال",
    "Fajr Sepasi": "فجر سپاسی",
    "Nassaji Mazandaran": "نساجی مازندران",
    "Nassaji": "نساجی",
    "Gol Gohar": "گل‌گهر",
    "Mes Shahr-e Babak": "مس شهربابک",
    "Aluminium Hormozgan": "آلومینیوم هرمزگان",
    "F.C. Nassaji Mazandaran": "نساجی مازندران",
}


def team_name_fa(name: str) -> str:
    return TEAM_NAMES_FA.get(name, name)


class TheSportsDBError(Exception):
    """خطای کلی thesportsdb."""


class TheSportsDBRateLimit(TheSportsDBError):
    """سرویس rate-limit شده (error code: 1015) — پاسخ JSON نیست."""


class TheSportsDBClient:
    def __init__(self, key: str, cache: DiskCache | None = None):
        self.key = key
        self.cache = cache or DiskCache()

    def _fetch(self, endpoint: str, params: dict, ttl: float, retries: int = 3) -> dict:
        url = f"{BASE}/{self.key}/{endpoint}"
        key = f"{endpoint}{sorted(params.items())}"
        hit = self.cache.get(endpoint, key, ttl)
        if hit is not None:
            return hit
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                resp = http_get(url, params=params, timeout=20.0)
            except HttpError as exc:
                last_error = exc
                if exc.status == 429:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise TheSportsDBError(str(exc)) from exc
            try:
                data = resp.json()
            except json.JSONDecodeError:
                # کلید تست عمومی 123 rate-limit می‌شود و متن برمی‌گرداند:
                #   error code: 1015  (پاسخ JSON نیست)
                if "1015" in resp.text:
                    if attempt + 1 < retries:
                        time.sleep(5)
                        continue
                    raise TheSportsDBRateLimit(
                        "thesportsdb.com rate-limit شده (error code: 1015). "
                        "اگر از کلید تست عمومی استفاده می‌کنید، کلید خاص خود "
                        "بگیر یا چند دقیقه منتظر بمان."
                    )
                raise TheSportsDBError(f"پاسخ غیر JSON: {resp.text[:120]}") from None
            self.cache.set(endpoint, key, data)
            return data
        raise TheSportsDBError(str(last_error or "درخواست ناموفق"))

    def next_events(self, league_id: str | int) -> list[dict]:
        data = self._fetch(
            "eventsnextleague.php", {"id": league_id}, TTL_MATCHES
        )
        return data.get("events", []) or []

    def past_events(self, league_id: str | int) -> list[dict]:
        data = self._fetch(
            "eventspastleague.php", {"id": league_id}, TTL_MATCHES
        )
        return data.get("events", []) or []

    def table(self, league_id: str | int, season: str) -> list[dict]:
        data = self._fetch(
            "lookuptable.php", {"l": league_id, "s": season}, TTL_TABLES
        )
        return data.get("table", []) or []
