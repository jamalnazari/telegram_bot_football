"""تست یکپارچه خط لوله با منگ‌پچ‌ی requests: خط لوله‌ی واقعی (APIها، ۴۰۳، ۱۰۱۵،
telegram، state) را بدون کلیدی واقعی تست می‌کند."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import requests  # noqa: E402

from text.dates import tehran_date_of  # noqa: E402

FAILURES: list[str] = []


def expect(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


class FakeResponse:
    def __init__(self, status: int = 200, json_data=None, text: str = "", headers: dict | None = None):
        self.status_code = status
        self._json = json_data
        self.text = text
        self.headers = headers or {}

    def json(self):
        if self._json is None:
            raise json.JSONDecodeError("no json", "", 0)
        return self._json


# ---------------------------------------------------------------- state
NOW = datetime.now(timezone.utc)
TODAY = tehran_date_of(NOW)
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)

FD_MATCHES_TODAY = [
    {
        "utcTime": f"{TODAY.isoformat()}T17:30:00Z",
        "homeTeam": {"longName": "Arsenal FC"},
        "awayTeam": {"longName": "Tottenham Hotspur FC"},
        "competition": {"code": "PL", "name": "Premier League"},
        "score": {"fullTime": {"home": None, "away": None}},
    },
    {
        "utcTime": f"{TODAY.isoformat()}T19:30:00Z",
        "homeTeam": {"longName": "Chelsea FC"},
        "awayTeam": {"longName": "Manchester City FC"},
        "competition": {"code": "PD", "name": "La Liga"},
        "score": {"fullTime": {"home": None, "away": None}},
    },
]
FD_MATCHES_YESTERDAY = [
    {
        "utcTime": f"{YESTERDAY.isoformat()}T17:30:00Z",
        "homeTeam": {"longName": "Liverpool FC"},
        "awayTeam": {"longName": "Arsenal FC"},
        "competition": {"code": "PL", "name": "Premier League"},
        "score": {"fullTime": {"home": 3, "away": 2}},
    },
]
FD_MATCHES_WINDOW = [
    {
        "utcTime": (NOW + timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "homeTeam": {"longName": "Real Madrid CF"},
        "awayTeam": {"longName": "FC Barcelona"},
        "competition": {"code": "PD", "name": "La Liga"},
        "score": {"fullTime": {"home": None, "away": None}},
    },
]
TSDB_1015_COUNT = {"n": 0}
LLM_MODE = {"good": True}


def _parse(s: str):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def fake_get(url, headers=None, params=None, timeout=None, **kwargs):
    if "football-data.org" in url and url.endswith("/matches"):
        # فیلتر بر اساس پنجره‌ی UTC (dateFrom/dateTo) — درست شبیه API واقعی
        df = str(params.get("dateFrom", ""))[:10]
        dt_ = str(params.get("dateTo", ""))[:10]
        window_lo = datetime.fromisoformat(df + "T00:00:00+00:00")
        window_hi = datetime.fromisoformat(dt_ + "T23:59:59+00:00")
        all_matches = FD_MATCHES_TODAY + FD_MATCHES_YESTERDAY + FD_MATCHES_WINDOW
        matches = [m for m in all_matches if window_lo <= _parse(m["utcTime"]) <= window_hi]
        return FakeResponse(200, {"matches": matches})
    if "football-data.org" in url and "/standings" in url:
        if "/competitions/CL/" in url:  # پلن رایگان: CL جدول ندارد
            return FakeResponse(403, text='{"message":"Forbidden"}')
        return FakeResponse(
            200,
            {
                "standings": [
                    {
                        "table": [
                            {
                                "position": 1,
                                "team": {"longName": "Arsenal FC"},
                                "playedGames": 12,
                                "won": 9,
                                "draw": 2,
                                "lost": 1,
                                "goalsFor": 25,
                                "goalsAgainst": 7,
                                "goalDifference": 18,
                                "points": 29,
                            }
                        ]
                    }
                ]
            },
        )
    if "football-data.org" in url and "/scorers" in url:
        comp_code = url.split("/competitions/")[1].split("/")[0]
        return FakeResponse(
            200,
            {
                "scorers": [
                    {
                        "player": {"name": "Erling Haaland"},
                        "team": {"longName": "Manchester City FC"},
                        "numberOfGoals": 15 if comp_code == "PL" else 12,
                    }
                ]
            },
        )
    if "thesportsdb.com" in url:
        if "eventspastleague" in url:
            TSDB_1015_COUNT["n"] += 1
            if TSDB_1015_COUNT["n"] <= 2:
                # کلید تست عمومی 123: پاسخ JSON نیست، متن error code: 1015
                return FakeResponse(200, text="error code: 1015", headers={"Content-Type": "text/plain"})
            return FakeResponse(
                200,
                {
                    "events": [
                        {
                            "strTime": f"{YESTERDAY.isoformat()}T17:30:00",
                            "strHomeTeam": "Persepolis",
                            "strAwayTeam": "Esteghlal",
                            "intHomeScore": 3,
                            "intAwayScore": 0,
                            "goals": {
                                "home": [
                                    {"time": "20'", "type": "1-GOAL", "player": "Ali Player"},
                                    {"time": "55'", "type": "2-GOAL", "player": "Ali Player"},
                                    {"time": "80'", "type": "2-GOAL", "player": "Ali Player"},
                                    {"time": "85'", "type": "OWN-GOAL", "player": "Own Scorer"},
                                ],
                                "away": [],
                            },
                        }
                    ]
                },
            )
        if "eventsnextleague" in url:
            return FakeResponse(
                200,
                {
                    "events": [
                        {
                            "strTime": f"{TODAY.isoformat()}T17:30:00",
                            "strHomeTeam": "Persepolis",
                            "strAwayTeam": "Esteghlal",
                            "strLeague": "4742",
                        }
                    ]
                },
            )
        if "lookuptable" in url:
            return FakeResponse(
                200,
                {
                    "table": [
                        {
                            "rank": "1",
                            "teamName": "Persepolis",
                            "intPlayed": "12",
                            "intWon": "9",
                            "intDraw": "2",
                            "intLost": "1",
                            "intGoalDifference": "18",
                            "intPoints": "29",
                        }
                    ]
                },
            )
    return FakeResponse(404, text="not found")


def fake_post(url, json=None, headers=None, data=None, files=None, timeout=None, **kwargs):
    if "api.telegram.org" in url:
        return FakeResponse(200, {"ok": True})
    if "generativelanguage.googleapis.com" in url:
        if LLM_MODE["good"]:
            return FakeResponse(
                200,
                {"candidates": [{"content": {"parts": [{"text": "هالند ۱۵ گل زده و در صدر است."}]}}]},
            )
        return FakeResponse(
            200,
            {"candidates": [{"content": {"parts": [{"text": "هالند ۹۹ گل زده و در صدر است."}]}}]},
        )
    return FakeResponse(404, text="not found")


requests.get = fake_get
requests.post = fake_post


def run_job(job: str):
    sys.argv = ["run.py", "--job", job]
    import run as run_mod

    return run_mod.main()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="football_bot_it_"))
    shutil.copytree(ROOT / "assets", tmp / "assets")
    shutil.copy(ROOT / "config.yaml", tmp / "config.yaml")
    os.chdir(tmp)

    os.environ["FOOTBALL_DATA_TOKEN"] = "fake-fd"
    os.environ["THESPORTSDB_KEY"] = "fake-tsdb"
    os.environ["GEMINI_API_KEY"] = "fake-gemini"
    os.environ["TELEGRAM_BOT_TOKEN"] = "fake-tg"
    os.environ["TELEGRAM_CHANNEL_ID"] = "-1001234567890"

    print("[it] --job daily")
    run_job("daily")
    st = json.loads((tmp / "state" / "posted.json").read_text())
    expect("کلید daily ثبت شد", any(k.startswith("daily:") for k in st), str(st))
    caption = (tmp / "media" / TODAY.isoformat() / "daily.txt").read_text()
    expect("کپشن شامل ساعت تهران + تیم‌های فارسی", "۲۱:۰۰" in caption and "پرسپولیس" in caption and "Arsenal FC" in caption, caption)
    card = tmp / "media" / TODAY.isoformat() / "daily.png"
    expect("کارت PNG ساخته شد", card.exists() and card.stat().st_size > 10_000)

    print("[it] --job daily مجدد (دکمه‌ی ضدتکرار)")
    before = dict(st)
    run_job("daily")
    st = json.loads((tmp / "state" / "posted.json").read_text())
    expect("پست دوباره ثبت نشد", st == before, str(st))

    print("[it] --job recap")
    run_job("recap")
    st = json.loads((tmp / "state" / "posted.json").read_text())
    expect("کلید recap ثبت شد", any(k.startswith("recap:") for k in st))

    print("[it] --job reminder (بازه‌ی ۱۲±۳۰ دقیقه)")
    run_job("reminder")
    st = json.loads((tmp / "state" / "posted.json").read_text())
    rkeys = [k for k in st if k.startswith("reminder:")]
    expect("یادآور برای بازی پنجره‌ی زمانی ثبت شد", len(rkeys) == 1, str(rkeys))

    print("[it] --job stat (۴۰۳ CL رد شد، بقیه ادامه دادند)")
    run_job("stat")
    st = json.loads((tmp / "state" / "posted.json").read_text())
    expect("کلید stat ثبت شد", any(k.startswith("stat:") for k in st), str(st))

    print("[it] راه‌های client: ۴۰۳ پلن رایگان")
    from sources.football_data import FootballDataClient, FreePlanError

    client = FootballDataClient("fake")
    try:
        client.get_standings("CL")
        expect("FreePlanError انداخته شد", False, "exception not raised")
    except FreePlanError as exc:
        expect("پیام ۴۰۳ واضح است", "پلن رایگان" in str(exc), str(exc))

    print("[it] ۱۰۱۵ thesportsdb: retry کوتاه و ادامه بدون کرش")
    TSDB_1015_COUNT["n"] = 0
    from sources.thesportsdb import TheSportsDBClient

    client = TheSportsDBClient("test")
    events = client.past_events(4742)
    expect("پس از retry داده برگشت", len(events) == 1 and events[0]["strHomeTeam"] == "Persepolis", str(events)[:80])

    print("[it] hat_tricks از آرایه‌ی goals (OWN رد می‌شود)")
    from facts.build import _count_hat_tricks

    entries = _count_hat_tricks(events)
    players = {e["player"] for e in entries}
    expect("گل به خودی نشمار شد", "Ali Player" in players and "Own Scorer" not in players, str(entries))

    print("[it] مسیر مدل زبانی با عدد مجاز")
    LLM_MODE["good"] = True
    from sources.demo_data import demo_package
    from config import load_config
    from sources.gemini import GeminiClient
    from writer import make_caption

    cfg = load_config("config.yaml")
    cap = make_caption(demo_package("scorers"), cfg, gemini=GeminiClient("fake"))
    expect("خروجی مدل حفظ شد (عدد مجاز)", "۱۵" in cap and "۹۹" not in cap, cap)

    print("[it] نگهبان عدد: عدد جعلی → fallback قالب + stderr")
    LLM_MODE["good"] = False
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        cap2 = make_caption(demo_package("scorers"), cfg, gemini=GeminiClient("fake"))
    expect("دلیل رد در stderr چاپ شد", "99" in stderr.getvalue() or "۹۹" in stderr.getvalue(), stderr.getvalue())
    expect("قالب آماده جایگزین شد", "۹۹" not in cap2, cap2)

    print("[it] تمیز‌سازی temporary directory")
    os.chdir(ROOT)
    shutil.rmtree(tmp, ignore_errors=True)

    print()
    if FAILURES:
        print(f"[it] شکست: {len(FAILURES)} مورد: {', '.join(FAILURES)}")
        return 1
    print("[it] همه‌ی تست‌های یکپارچه PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
