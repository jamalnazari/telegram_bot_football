#!/usr/bin/env python3
"""خط لوله‌ی اصلی: python run.py --job <daily|recap|stat|reminder|auto|demo|test|all>.

لایه‌بندی: sources → facts → writer → cards → telegram.
هر لایه فقط با لایه‌ی بعدی حرف می‌زند.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import jdatetime

from cards import render_card, save_card
from config import load_config, load_env
from facts import FactsUnavailable, build
from sources.demo_data import ALL_KINDS, demo_package
from sources.football_data import FootballDataClient
from sources.gemini import GeminiClient
from sources.thesportsdb import TheSportsDBClient
from telegram.api import TelegramClient
from telegram.state import StateStore
from text.dates import tehran_date_of
from writer import make_caption

STAT_ORDER = ["scorers", "standings", "hat_tricks"]
SAMPLES_DIR = Path("samples")


# ---------------------------------------------------------------- clients
def build_clients(cfg: dict):
    fd = (
        FootballDataClient(os.environ.get("FOOTBALL_DATA_TOKEN", ""))
        if os.environ.get("FOOTBALL_DATA_TOKEN")
        else None
    )
    tsdb = (
        TheSportsDBClient(os.environ.get("THESPORTSDB_KEY", ""))
        if os.environ.get("THESPORTSDB_KEY")
        else None
    )
    gemini = None
    if cfg["model"].get("enabled", True):
        gemini = GeminiClient(
            os.environ.get("GEMINI_API_KEY", ""),
            model=cfg["model"].get("name", "gemini-2.5-flash"),
            max_output_tokens=int(cfg["model"].get("max_output_tokens", 400)),
        )
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    tg_chat = os.environ.get("TELEGRAM_CHANNEL_ID", "")
    if tg_token and not tg_chat:
        print(
            "[run] هشدار: توکن ربات وجود دارد ولی TELEGRAM_CHANNEL_ID تنظیم نشده — "
            "فرستادن ممکن است با خطای تلگرام شکست بخورد.",
            file=sys.stderr,
        )
    tg = TelegramClient(tg_token, tg_chat)
    return fd, tsdb, gemini, tg


# ---------------------------------------------------------------- pipeline
def publish_post(cfg, gemini, tg, state, facts, kind, key, media_dir) -> None:
    caption = make_caption(facts, cfg, gemini)
    img = render_card(facts, caption, cfg)
    png = save_card(img, media_dir / f"{kind}.png")
    (media_dir / f"{kind}.txt").write_text(caption, encoding="utf-8")
    source_link = cfg["channel"].get("source_link", "")
    tg.send_photo(png, caption, source_link)
    state.remember(key)
    state.save()
    print(f"[post] {kind} -> {png} ({key})")


def _job_daily(cfg, fd, tsdb, gemini, tg, state, now_utc) -> None:
    iso = tehran_date_of(now_utc).isoformat()
    key = f"daily:{iso}"
    if state.seen(key):
        print(f"[daily] قبلاً پست شده ({key}) — دكمه‌ی ضدتکرار")
        return
    try:
        facts = build("fixtures", cfg, fd, tsdb, now_utc)
    except FactsUnavailable as exc:
        print(f"[daily] {exc}")
        return
    publish_post(cfg, gemini, tg, state, facts, "daily", key, Path("media") / iso)


def _job_recap(cfg, fd, tsdb, gemini, tg, state, now_utc) -> None:
    iso = tehran_date_of(now_utc).isoformat()
    key = f"recap:{iso}"
    if state.seen(key):
        print(f"[recap] قبلاً پست شده ({key}) — دكمه‌ی ضدتکرار")
        return
    try:
        facts = build("recap", cfg, fd, tsdb, now_utc)
    except FactsUnavailable as exc:
        print(f"[recap] {exc}")
        return
    publish_post(cfg, gemini, tg, state, facts, "recap", key, Path("media") / iso)


def _job_stat(cfg, fd, tsdb, gemini, tg, state, now_utc) -> None:
    iso = tehran_date_of(now_utc).isoformat()
    key = f"stat:{iso}"
    if state.seen(key):
        print(f"[stat] قبلاً پست شده ({key}) — دكمه‌ی ضدتکرار")
        return
    rotation = jdatetime.date.fromgregorian(date=tehran_date_of(now_utc)).toordinal() % len(STAT_ORDER)
    kind = STAT_ORDER[rotation]
    print(f"[stat] چرخش کارت آماری: {kind}")
    try:
        facts = build(kind, cfg, fd, tsdb, now_utc)
    except FactsUnavailable as exc:
        print(f"[stat] {exc}")
        return
    publish_post(cfg, gemini, tg, state, facts, f"stat_{kind}", key, Path("media") / iso)


def _job_reminder(cfg, fd, tsdb, gemini, tg, state, now_utc) -> None:
    try:
        pkg = build("reminder", cfg, fd, tsdb, now_utc)
    except FactsUnavailable as exc:
        print(f"[reminder] {exc}")
        return
    if pkg["count"] == 0:
        print("[reminder] هیچ بازی‌ای در پنجره‌ی ۱۲±۳۰ دقیقه‌ی زمانی نیست")
        return
    iso = tehran_date_of(now_utc).isoformat()
    media_dir = Path("media") / iso
    for i, m in enumerate(pkg["matches"], 1):
        single = {
            "type": "reminder",
            "date": m.get("date", ""),
            "home": m["home"],
            "away": m["away"],
            "time": m["time"],
            "utc": m["utc"],
            "competition": m["competition"],
            "code": m.get("code", ""),
            "hours_before": pkg["hours_before"],
        }
        key = f"reminder:{m['utc']}:{m['home']}"
        if state.seen(key):
            print(f"[reminder] قبلاً پست شده ({key})")
            continue
        publish_post(cfg, gemini, tg, state, single, f"reminder_{i}_{m['home']}", key, media_dir)


def _job_auto(cfg, fd, tsdb, gemini, tg, state, now_utc) -> None:
    """ورودیت پیش‌فرض کرون: پنجره‌ی ۲ ساعته برای هر پست."""
    hour = now_utc.astimezone(ZoneInfo(cfg.get("timezone", "Asia/Tehran"))).hour
    print(f"[auto] ساعت تهران: {hour}")
    windows = [
        ("daily", int(cfg["posts"]["daily_digest_hour"])),
        ("recap", int(cfg["posts"]["recap_hour"])),
        ("stat", int(cfg["posts"]["stat_card_hour"])),
    ]
    for job, target in windows:
        if target <= hour < target + 2:
            print(f"[auto] اجرای {job} (پنجره‌ی ساعت {target})")
            _run_job(job, cfg, fd, tsdb, gemini, tg, state, now_utc)
    # یادآور هر ساعت اجرا می‌شود
    _run_job("reminder", cfg, fd, tsdb, gemini, tg, state, now_utc)


def _run_job(job, cfg, fd, tsdb, gemini, tg, state, now_utc) -> None:
    if job == "daily":
        _job_daily(cfg, fd, tsdb, gemini, tg, state, now_utc)
    elif job == "recap":
        _job_recap(cfg, fd, tsdb, gemini, tg, state, now_utc)
    elif job == "stat":
        _job_stat(cfg, fd, tsdb, gemini, tg, state, now_utc)
    elif job == "reminder":
        _job_reminder(cfg, fd, tsdb, gemini, tg, state, now_utc)
    else:
        raise ValueError(f"job نامعتبر: {job}")


# ---------------------------------------------------------------- demo
def _make_preview(cfg) -> None:
    """پیش‌نمایش شبیه چت تلگرام: تصاویر base64 درون‌خطی (بدون منبع خارجی)."""
    parts = [
        "<!DOCTYPE html><html lang=\"fa\" dir=\"rtl\"><head><meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        "<title>پیش‌نمایش کانال — تلگرام</title><style>",
        "body{margin:0;background:#0e1621;font-family:'Vazirmatn',sans-serif;color:#fff;display:flex;justify-content:center}",
        ".chat{width:100%;max-width:520px;padding:16px 8px;}",
        ".day{text-align:center;color:#7ea7c5;font-size:13px;margin:14px 0}",
        ".bubble{background:#182533;border-radius:14px;padding:10px;margin:8px 0;max-width:92%;margin-inline-end:auto}",
        ".row{display:flex;gap:10px;align-items:flex-start}",
        ".avatar{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#00e08a,#ffc247);",
        "display:flex;align-items:center;justify-content:center;font-size:22px;flex:none}",
        ".inner{min-width:0}",
        ".brand{color:#7ea7c5;font-size:13px;margin:2px 6px 8px}",
        ".bubble img{width:100%;border-radius:10px;display:block}",
        ".caption{font-size:14.5px;line-height:1.65;margin-top:8px;white-space:pre-wrap;word-break:break-word}",
        "</style></head><body><div class=\"chat\">",
    ]
    titles = {
        "fixtures": "برنامه‌ی امروز",
        "recap": "مرور نتایج دیروز",
        "scorers": "گلزنان برتر",
        "standings": "صدرنشینان جدول",
        "hat_tricks": "هتریک‌های اخیر",
        "reminder": "یادآور بازی",
    }
    for kind in ALL_KINDS:
        png = SAMPLES_DIR / f"demo_{kind}.png"
        cap_file = SAMPLES_DIR / f"demo_{kind}.txt"
        if not png.exists() or not cap_file.exists():
            continue
        b64 = base64.b64encode(png.read_bytes()).decode("ascii")
        caption = cap_file.read_text(encoding="utf-8")
        parts.append(
            f'<div class="day">{titles.get(kind, kind)}</div>'
            f'<div class="bubble"><div class="row"><div class="avatar">⚽</div>'
            f'<div class="inner"><div class="brand">@{cfg["channel"].get("username", "")}</div>'
            f'<img src="data:image/png;base64,{b64}" alt="{titles.get(kind, kind)}">'
            f'<div class="caption">{caption}</div></div></div></div>'
        )
    parts.append("</div></body></html>")
    (SAMPLES_DIR / "preview.html").write_text("".join(parts), encoding="utf-8")
    print(f"[demo] پیش‌نمایش: {SAMPLES_DIR / 'preview.html'}")


def run_demo(cfg) -> None:
    """داده‌ی نمونه: بدون هیچ کلیدی، شش کارت + شش کپشن در samples/."""
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    print("=== بسته‌های واقعیت (demo، فقط JSON) ===")
    for kind in ALL_KINDS:
        pkg = demo_package(kind)
        print(json.dumps(pkg, ensure_ascii=False))
    print("=== رندر کارت‌ها و کپشن‌ها ===")
    for kind in ALL_KINDS:
        facts = demo_package(kind)
        caption = make_caption(facts, cfg, gemini=None)
        img = render_card(facts, caption, cfg)
        save_card(img, SAMPLES_DIR / f"demo_{kind}.png")
        (SAMPLES_DIR / f"demo_{kind}.txt").write_text(caption, encoding="utf-8")
        print(f"[demo] {kind}: {SAMPLES_DIR / f'demo_{kind}.png'} + caption {len(caption)} کاراکتر")
    _make_preview(cfg)
    print("[demo] انجام شد.")


# ---------------------------------------------------------------- tests
def run_tests(cfg) -> int:
    """تست‌های یکپارچه: نگهبان اعداد، bidi، ارقام فارسی، بازه‌ی روز تهران، چیدمان."""
    from writer.guard import check
    from text.drawing import _display, _shape, detect_direction
    from text.dates import tehran_day_bounds
    from text.numerals import fa_num, normalize_digits
    from datetime import timezone as dt_timezone

    failures: list[str] = []

    def expect(name: str, cond: bool, detail: str = "") -> None:
        print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f" — {detail}" if detail and not cond else ""))
        if not cond:
            failures.append(name)

    print("[test] نگهبان اعداد")
    facts = demo_package("scorers")
    ok, reason = check("هالند ۱۵ گل زد و ۱۳ پاس گلف داد", facts)
    expect("عدد معتبر قبول می‌شود", ok, reason)
    ok, reason = check("هالند ۱۵ گل زد و ۶۰ پاس گلف داد", facts)
    expect("عدد جعلی رد می‌شود", not ok and "60" in reason, reason)
    ok, reason = check("دیروز بازی جذاب بود", facts)
    expect("متن بدون عدد مجاز است", ok, reason)
    ok, reason = check("هالند scored 15 goals", facts)
    expect("ارقام لاتین مجاز شمرده می‌شود", ok, reason)

    print("[test] bidi و shaping")
    expect("جهت فارسی rtl است", detect_direction("آرسنال") == "rtl")
    expect("جهت لاتین ltr است", detect_direction("PL") == "ltr")
    v = _display(_shape("سلام Hello", "rtl"), "rtl")
    expect("ترتيب bidi مطابق UAX#9 است", v == "Hello ﻡﻼﺳ", repr(v))
    expect("reshaper لاتین را تغییر نمی‌دهد", _shape("Hello سلام", "rtl").startswith("Hello"))

    print("[test] ارقام فارسی")
    expect("fa_num تبدیل می‌کند", fa_num("PL 2026-11-09 20:30") == "PL ۲۰۲۶-۱۱-۰۹ ۲۰:۳۰")
    expect("normalize_digits تبدیل می‌کند", normalize_digits("۱۵") == "15")

    print("[test] بازه‌ی روز تهران")
    from text.dates import now_tehran

    now = now_tehran()
    lo, hi = tehran_day_bounds(now.date())
    mid = datetime.fromtimestamp((lo.timestamp() + hi.timestamp()) / 2, dt_timezone.utc)
    expect("میان بازه، تاریخ تهران برابر با هدف است", tehran_date_of(mid) == now.date())

    print("[test] چیدمان کارت‌ها (audit)")
    sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
    import audit_layout

    if audit_layout.main() != 0:
        failures.append("چیدمان کارت‌ها")

    print()
    if failures:
        print(f"[test] شکست: {len(failures)} مورد: {', '.join(failures)}")
        return 1
    print("[test] همه‌ی تست‌ها PASS")
    return 0


# ---------------------------------------------------------------- main
def main() -> int:
    parser = argparse.ArgumentParser(description="انتشار خودکار محتوای فوتبالی در کانال تلگرام")
    parser.add_argument("--job", required=True, choices=["daily", "recap", "stat", "reminder", "auto", "demo", "test", "all"])
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    load_env()
    cfg = load_config(args.config)
    now_utc = datetime.now(timezone.utc)

    if args.job == "demo":
        run_demo(cfg)
        return 0
    if args.job == "test":
        return run_tests(cfg)

    fd, tsdb, gemini, tg = build_clients(cfg)
    state = StateStore("state/posted.json")

    if args.job == "auto":
        _job_auto(cfg, fd, tsdb, gemini, tg, state, now_utc)
    elif args.job == "all":
        _run_job("daily", cfg, fd, tsdb, gemini, tg, state, now_utc)
        _run_job("recap", cfg, fd, tsdb, gemini, tg, state, now_utc)
        _run_job("stat", cfg, fd, tsdb, gemini, tg, state, now_utc)
    else:
        _run_job(args.job, cfg, fd, tsdb, gemini, tg, state, now_utc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
