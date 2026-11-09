"""football-data.org نسخه v4 (پلن رایگان، هدر X-Auth-Token)."""

from __future__ import annotations

from sources.cache import DiskCache, TTL_MATCHES, TTL_TABLES
from sources.http import HttpError, http_get

BASE = "https://api.football-data.org/v4"


class FootballDataError(Exception):
    """خطای کلی football-data."""


class FreePlanError(FootballDataError):
    """endpoint در پلن رایگان نیست (HTTP 403)."""


class FootballDataClient:
    def __init__(self, token: str, cache: DiskCache | None = None):
        self.token = token
        self.cache = cache or DiskCache()

    def _headers(self) -> dict:
        return {"X-Auth-Token": self.token}

    def _cached_get(self, namespace: str, key: str, url: str, params: dict, ttl: float):
        hit = self.cache.get(namespace, key, ttl)
        if hit is not None:
            return hit
        try:
            resp = http_get(url, headers=self._headers(), params=params)
        except HttpError as exc:
            if exc.status == 403:
                raise FreePlanError(
                    "این endpoint در پلن رایگان نیست"
                ) from exc
            raise FootballDataError(str(exc)) from exc
        data = resp.json()
        self.cache.set(namespace, key, data)
        return data

    def get_matches(self, date_from: str, date_to: str, codes: list[str]) -> list[dict]:
        """/v4/matches?dateFrom=&dateTo=&competitions=PL,PD,..."""
        data = self._cached_get(
            "matches",
            f"{date_from}-{date_to}-{','.join(codes)}",
            f"{BASE}/matches",
            {
                "dateFrom": date_from,
                "dateTo": date_to,
                "competitions": ",".join(codes),
            },
            TTL_MATCHES,
        )
        return data.get("matches", [])

    def get_standings(self, code: str) -> list[dict]:
        """/v4/competitions/{code}/standings"""
        data = self._cached_get(
            "standings", code, f"{BASE}/competitions/{code}/standings", {}, TTL_TABLES
        )
        standings = data.get("standings", [])
        if not standings:
            return []
        return standings[0].get("table", [])

    def get_scorers(self, code: str) -> list[dict]:
        """/v4/competitions/{code}/scorers"""
        data = self._cached_get(
            "scorers", code, f"{BASE}/competitions/{code}/scorers", {}, TTL_TABLES
        )
        return data.get("scorers", [])
