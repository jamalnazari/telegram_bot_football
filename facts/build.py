"""لایه‌ی واقعیت (facts).

تنها جایی که عدد ساخته می‌شود. خروجی یک دیکشنری JSON با کلید type که یکی از
fixtures | recap | scorers | standings | hat_tricks | reminder است.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

from sources.football_data import FootballDataClient, FreePlanError
from sources.thesportsdb import TheSportsDBClient, TheSportsDBRateLimit, TheSportsDBError, team_name_fa
from text.dates import (
    TEHRAN,
    persian_date_str,
    persian_time_str,
    tehran_date_of,
    tehran_day_bounds,
)


class FactsUnavailable(Exception):
    """داده در دسترس نیست (کلیدهای لازم وجود ندارد / سرویس پاسخ نمی‌دهد)."""


def parse_utc(text: str) -> datetime:
    """درک زمان UTC از رشته: حتی اگر Z نداشت، باز هم aware UTC برمی‌گرداند."""
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _comp_fa(cfg: dict, code: str) -> str:
    for comp in cfg["competitions"]:
        if comp["code"] == code:
            return comp["fa"]
    return code


def _fd_match(m: dict, cfg: dict) -> dict:
    """همخوانشی match football-data به روی مدل داخلی."""
    utc = parse_utc(m["utcTime"])
    score = m.get("score", {}).get("fullTime", {})
    return {
        "home": m["homeTeam"]["longName"],
        "away": m["awayTeam"]["longName"],
        "time": persian_time_str(utc.astimezone(TEHRAN)),
        "utc": m["utcTime"],
        "competition": _comp_fa(cfg, m.get("competition", {}).get("code", "")),
        "code": m.get("competition", {}).get("code", ""),
        "home_goals": score.get("home"),
        "away_goals": score.get("away"),
    }


def _tsdb_event(e: dict) -> dict:
    """همخوانشی event thesportsdb به روی مدل داخلی."""
    utc = parse_utc(e["strTime"])
    home_goals = e.get("intHomeScore")
    away_goals = e.get("intAwayScore")
    return {
        "home": team_name_fa(e["strHomeTeam"]),
        "away": team_name_fa(e["strAwayTeam"]),
        "time": persian_time_str(utc.astimezone(TEHRAN)),
        "utc": utc.isoformat(),
        "competition": "لیگ برتر خلیج فارس",
        "code": "IRN",
        "score": f"{home_goals}-{away_goals}" if home_goals is not None and away_goals is not None else None,
        "total": (home_goals or 0) + (away_goals or 0) if home_goals is not None else 0,
    }


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _iran_clients(cfg: dict, tsdb: TheSportsDBClient | None) -> TheSportsDBClient | None:
    if not cfg["iran_league"].get("enabled"):
        return None
    return tsdb


def build_fixtures(cfg: dict, fd: FootballDataClient | None, tsdb: TheSportsDBClient | None,
                   now_utc: datetime) -> dict:
    """برنامه‌ی امروز: بازی‌های امروز لیگ‌های انتخابی، گروه‌بندی‌شده."""
    day = tehran_date_of(now_utc)
    bounds_lo, bounds_hi = tehran_day_bounds(day)
    matches: list[dict] = []

    if fd is not None:
        codes = [c["code"] for c in cfg["competitions"]]
        try:
            raw = fd.get_matches(bounds_lo.date().isoformat(), bounds_hi.date().isoformat(), codes)
            for m in raw:
                nm = _fd_match(m, cfg)
                if tehran_date_of(parse_utc(m["utcTime"])) == day:
                    matches.append(nm)
        except FreePlanError as exc:
            _log(f"[facts] football-data: {exc}")

    if _iran_clients(cfg, tsdb):
        try:
            for e in tsdb.next_events(cfg["iran_league"]["league_id"]):
                nm = _tsdb_event(e)
                if tehran_date_of(parse_utc(e["strTime"])) == day:
                    matches.append(nm)
        except TheSportsDBRateLimit as exc:
            _log(f"[facts] {exc}")
        except TheSportsDBError as exc:
            _log(f"[facts] thesportsdb: {exc}")

    matches.sort(key=lambda x: x["utc"])
    groups: dict[str, dict] = {}
    for m in matches:
        g = groups.setdefault(
            m["competition"], {"competition": m["competition"], "code": m["code"], "matches": []}
        )
        g["matches"].append({k: m[k] for k in ("home", "away", "time", "utc")})

    if not matches:
        raise FactsUnavailable(
            f"داده در دسترس نیست: امروز ({persian_date_str(day)}) هیچ بازی‌ای برای "
            "لیگ‌های انتخابی پیدا نشد. کلید FOOTBALL_DATA_TOKEN و/یا THESPORTSDB_KEY بررسی شود."
        )

    return {
        "type": "fixtures",
        "date": persian_date_str(day),
        "count": len(matches),
        "groups": list(groups.values()),
    }


def build_recap(cfg: dict, fd: FootballDataClient | None, tsdb: TheSportsDBClient | None,
                now_utc: datetime) -> dict:
    """مرور نتایج دیروز: بازی‌های پرگل‌تر اول."""
    today = tehran_date_of(now_utc)
    day = today - timedelta(days=1)
    bounds_lo, bounds_hi = tehran_day_bounds(day)
    matches: list[dict] = []

    if fd is not None:
        codes = [c["code"] for c in cfg["competitions"]]
        try:
            raw = fd.get_matches(bounds_lo.date().isoformat(), bounds_hi.date().isoformat(), codes)
            for m in raw:
                nm = _fd_match(m, cfg)
                if nm["home_goals"] is None or nm["away_goals"] is None:
                    continue
                if tehran_date_of(parse_utc(m["utcTime"])) == day:
                    nm["score"] = f"{nm['home_goals']}-{nm['away_goals']}"
                    nm["total"] = nm["home_goals"] + nm["away_goals"]
                    matches.append(nm)
        except FreePlanError as exc:
            _log(f"[facts] football-data: {exc}")

    if _iran_clients(cfg, tsdb):
        try:
            for e in tsdb.past_events(cfg["iran_league"]["league_id"]):
                nm = _tsdb_event(e)
                if tehran_date_of(parse_utc(e["strTime"])) == day and nm["score"]:
                    matches.append(nm)
        except TheSportsDBRateLimit as exc:
            _log(f"[facts] {exc}")
        except TheSportsDBError as exc:
            _log(f"[facts] thesportsdb: {exc}")

    matches.sort(key=lambda x: (-x["total"], x["utc"]))
    if not matches:
        raise FactsUnavailable(
            f"داده در دسترس نیست: دیروز ({persian_date_str(day)}) هیچ نتیجه‌ی ثبت‌شده‌ی "
            "بازی پیدا نشد."
        )

    return {
        "type": "recap",
        "date": persian_date_str(day),
        "count": len(matches),
        "matches": matches,
    }


def build_scorers(cfg: dict, fd: FootballDataClient | None) -> dict:
    """جدول گلزنان: مرز گلزنان هر لیگ، تخلیفه اصلی."""
    if fd is None:
        raise FactsUnavailable("داده در دسترس نیست: کلید FOOTBALL_DATA_TOKEN تنظیم نشده.")
    entries: list[dict] = []
    for comp in cfg["competitions"]:
        try:
            raw = fd.get_scorers(comp["code"])
        except FreePlanError as exc:
            _log(f"[facts] {comp['fa']}: {exc}")
            continue
        for s in raw:
            entries.append(
                {
                    "player": s.get("player", {}).get("name", "نامشخص"),
                    "team": s.get("team", {}).get("longName", "نامشخص"),
                    "goals": int(s.get("numberOfGoals", 0)),
                    "competition": comp["fa"],
                }
            )
    entries.sort(key=lambda x: (-x["goals"], x["player"]))
    entries = entries[:8]
    for i, e in enumerate(entries, 1):
        e["rank"] = i
    if not entries:
        raise FactsUnavailable("داده در دسترس نیست: هیچ گلزنی یافت نشد (پلن رایگان ممکن است محدودیت داشته باشد).")
    return {
        "type": "scorers",
        "date": persian_date_str(datetime.now(timezone.utc)),
        "count": len(entries),
        "entries": entries,
    }


def build_standings(cfg: dict, fd: FootballDataClient | None,
                    tsdb: TheSportsDBClient | None = None) -> dict:
    """بالاترین جدول: صدرنشینان هر لیگ."""
    entries: list[dict] = []
    if fd is not None:
        for comp in cfg["competitions"]:
            try:
                table = fd.get_standings(comp["code"])
            except FreePlanError as exc:
                _log(f"[facts] {comp['fa']}: {exc}")
                continue
            for row in table[:5]:
                entries.append(
                    {
                        "team": row.get("team", {}).get("longName", "نامشخص"),
                        "competition": comp["fa"],
                        "played": int(row.get("playedGames", 0)),
                        "won": int(row.get("won", 0)),
                        "drawn": int(row.get("draw", 0)),
                        "lost": int(row.get("lost", 0)),
                        "gd": int(row.get("goalDifference", 0)),
                        "points": int(row.get("points", 0)),
                    }
                )
    if _iran_clients(cfg, tsdb):
        try:
            rows = tsdb.table(cfg["iran_league"]["league_id"], cfg["iran_league"]["season"])
            for row in rows[:5]:
                entries.append(
                    {
                        "team": team_name_fa(row.get("teamName", "نامشخص")),
                        "competition": cfg["iran_league"]["fa"],
                        "played": int(row.get("intPlayed", 0)),
                        "won": int(row.get("intWon", 0)),
                        "drawn": int(row.get("intDraw", 0)),
                        "lost": int(row.get("intLost", 0)),
                        "gd": int(row.get("intGoalDifference", 0)),
                        "points": int(row.get("intPoints", 0)),
                    }
                )
        except (TheSportsDBRateLimit, TheSportsDBError) as exc:
            _log(f"[facts] thesportsdb: {exc}")
    if not entries:
        raise FactsUnavailable("داده در دسترس نیست: هیچ‌کدام از جدول‌ها در دسترس نبود (پلن رایگان ممکن است محدودیت داشته باشد).")
    entries.sort(key=lambda x: (-x["points"], -x["gd"]))
    entries = entries[:8]
    for i, e in enumerate(entries, 1):
        e["rank"] = i
    return {
        "type": "standings",
        "date": persian_date_str(datetime.now(timezone.utc)),
        "count": len(entries),
        "entries": entries,
    }


def _count_hat_tricks(events: list[dict]) -> list[dict]:
    """از آرایه‌ی goals همان بازی‌ها بشمار: هر بازیکن با ۳ گل یا بیشتر.

    گل به خودی (type OWN) را نشمار.
    """
    counts: dict[tuple[str, str], int] = {}
    details: dict[tuple[str, str], dict] = {}
    for e in events:
        match_name = f"{team_name_fa(e['strHomeTeam'])} — {team_name_fa(e['strAwayTeam'])}"
        goals = e.get("goals") or {}
        for side in ("home", "away"):
            team = e["strHomeTeam"] if side == "home" else e["strAwayTeam"]
            for g in goals.get(side) or []:
                goal_type = str(g.get("type", "")).upper()
                if "OWN" in goal_type:
                    continue
                player = g.get("player", "نامشخص")
                k = (player, team)
                counts[k] = counts.get(k, 0) + 1
                if k not in details:
                    details[k] = {"player": player, "team": team, "match": match_name}
    entries = [
        {**details[k], "goals": n}
        for k, n in counts.items()
        if n >= 3
    ]
    entries.sort(key=lambda x: (-x["goals"], x["player"]))
    for i, e in enumerate(entries, 1):
        e["rank"] = i
    return entries


def build_hat_tricks(cfg: dict, tsdb: TheSportsDBClient | None) -> dict:
    """هتریک‌های اخیر: از آرایه‌ی goals بازی‌های اخیر لیگ ایران."""
    entries: list[dict] = []
    events: list[dict] = []
    if _iran_clients(cfg, tsdb):
        try:
            events = tsdb.past_events(cfg["iran_league"]["league_id"])
        except TheSportsDBRateLimit as exc:
            _log(f"[facts] {exc}")
        except TheSportsDBError as exc:
            _log(f"[facts] thesportsdb: {exc}")
    entries = _count_hat_tricks(events)

    date_str = persian_date_str(datetime.now(timezone.utc))
    if entries:
        return {"type": "hat_tricks", "date": date_str, "count": len(entries), "entries": entries}

    # اگر goals خالی بود، بسته را count: 0 بده؛ لایه‌ی بالاتر (cards) باید به
    # کارت جدول fallback کند — داده‌ی fallback اینجا لیست می‌شود (لایه‌ی facts
    # تنها جایی است که می‌تواند داده اضافه کند).
    fallback: list[dict] = []
    if _iran_clients(cfg, tsdb):
        try:
            rows = tsdb.table(cfg["iran_league"]["league_id"], cfg["iran_league"]["season"])
            for row in rows[:5]:
                fallback.append(
                    {
                        "team": team_name_fa(row.get("teamName", "نامشخص")),
                        "competition": cfg["iran_league"]["fa"],
                        "played": int(row.get("intPlayed", 0)),
                        "won": int(row.get("intWon", 0)),
                        "drawn": int(row.get("intDraw", 0)),
                        "lost": int(row.get("intLost", 0)),
                        "gd": int(row.get("intGoalDifference", 0)),
                        "points": int(row.get("intPoints", 0)),
                    }
                )
        except (TheSportsDBRateLimit, TheSportsDBError) as exc:
            _log(f"[facts] thesportsdb: {exc}")
    fallback.sort(key=lambda x: (-x["points"], -x["gd"]))
    for i, e in enumerate(fallback, 1):
        e["rank"] = i
    if not fallback:
        raise FactsUnavailable("داده در دسترس نیست: برای کارت هتریک، داده‌ی بازی‌های اخیر در دسترس نبود.")
    return {
        "type": "hat_tricks",
        "date": date_str,
        "count": 0,
        "entries": [],
        "fallback_standings": fallback,
    }


def build_reminder(cfg: dict, fd: FootballDataClient | None, tsdb: TheSportsDBClient | None,
                   now_utc: datetime) -> dict:
    """یادآور: بازی‌هایی که شروعش بین الان + ۱۲ ساعت − ۳۰ دقیقه و + ۳۰ دقیقه است."""
    hours = int(cfg["posts"].get("reminder_hours_before", 12))
    window_lo = now_utc + timedelta(hours=hours) - timedelta(minutes=30)
    window_hi = now_utc + timedelta(hours=hours) + timedelta(minutes=30)
    matches: list[dict] = []

    if fd is not None:
        codes = [c["code"] for c in cfg["competitions"]]
        try:
            raw = fd.get_matches(window_lo.date().isoformat(), window_hi.date().isoformat(), codes)
            for m in raw:
                utc = parse_utc(m["utcTime"])
                if window_lo <= utc <= window_hi:
                    nm = _fd_match(m, cfg)
                    matches.append(nm)
        except FreePlanError as exc:
            _log(f"[facts] football-data: {exc}")

    if _iran_clients(cfg, tsdb):
        try:
            for e in tsdb.next_events(cfg["iran_league"]["league_id"]):
                utc = parse_utc(e["strTime"])
                if window_lo <= utc <= window_hi:
                    matches.append(_tsdb_event(e))
        except TheSportsDBRateLimit as exc:
            _log(f"[facts] {exc}")
        except TheSportsDBError as exc:
            _log(f"[facts] thesportsdb: {exc}")

    matches.sort(key=lambda x: x["utc"])
    for m in matches:
        m["date"] = persian_date_str(tehran_date_of(parse_utc(m["utc"])))
    return {"type": "reminder", "hours_before": hours, "count": len(matches), "matches": matches}


def build(kind: str, cfg: dict, fd: FootballDataClient | None,
          tsdb: TheSportsDBClient | None, now_utc: datetime) -> dict:
    """dispatcher اصلی لایه‌ی واقعیت."""
    if kind == "fixtures":
        return build_fixtures(cfg, fd, tsdb, now_utc)
    if kind == "recap":
        return build_recap(cfg, fd, tsdb, now_utc)
    if kind == "scorers":
        return build_scorers(cfg, fd)
    if kind == "standings":
        return build_standings(cfg, fd, tsdb)
    if kind == "hat_tricks":
        return build_hat_tricks(cfg, tsdb)
    if kind == "reminder":
        return build_reminder(cfg, fd, tsdb, now_utc)
    raise ValueError(f"نوع بسته نامعتبر: {kind}")
