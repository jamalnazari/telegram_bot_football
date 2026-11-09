"""قالب‌های آماده فارسی: کپشن قطعی از روی بسته. همیشه کار می‌کند."""

from __future__ import annotations

MAX_CAPTION = 1000  # زیر حداکثر ۱۰۲۴ کاراکتر تلگرام


def _lines_budget(lines: list[str], budget: int = MAX_CAPTION) -> str:
    """خط‌ها را تا سقف budget کاراکتر برش می‌دهد (تگ‌ها و متن پایانی حفظ می‌شوند)."""
    out: list[str] = []
    used = 0
    for line in lines:
        if used + len(line) + 1 > budget:
            break
        out.append(line)
        used += len(line) + 1
    return "\n".join(out)


def render(facts: dict) -> str:
    kind = facts.get("type")
    if kind == "fixtures":
        return _fixtures(facts)
    if kind == "recap":
        return _recap(facts)
    if kind == "scorers":
        return _list_caption(facts, "🥇 گلزنان برتر", "گل", lambda e: f"{e.get('player', '')} — {e.get('team', '')} ({e.get('goals', 0)} گل)")
    if kind == "standings":
        return _list_caption(facts, "🏆 صدرنشینان جدول", "امتیاز", lambda e: f"{e.get('team', '')} — {e.get('points', 0)} امتیاز")
    if kind == "hat_tricks":
        return _hat_tricks(facts)
    if kind == "reminder":
        return _reminder(facts)
    raise ValueError(f"قالب برای نوع {kind} وجود ندارد")


def _fixtures(facts: dict) -> str:
    lines = ["📅 برنامه‌ی امروز", ""]
    for g in facts.get("groups", []):
        lines.append(g.get("competition", ""))
        for m in g.get("matches", []):
            lines.append(f"• {m.get('home', '')} — {m.get('away', '')}  ({m.get('time', '')})")
        lines.append("")
    lines += ["⏰ همه‌ی ساعت‌ها به وقت تهران است.", "", "#فوتبال #لیگ #برنامه_بازی"]
    return _lines_budget(lines)


def _recap(facts: dict) -> str:
    lines = ["⚽ مرور نتایج دیروز", ""]
    for m in facts.get("matches", []):
        lines.append(
            f"• {m.get('home', '')} — {m.get('away', '')}  ({m.get('score', '')})  "
            f"گل‌های بازی: {m.get('total', 0)}"
        )
    lines += ["", "🔥 بازی‌های پرگل‌تر اول آمدند.", "", "#فوتبال #نتایج #لیگ"]
    return _lines_budget(lines)


def _list_caption(facts: dict, title: str, unit: str, entry_line) -> str:
    lines = [title, ""]
    for e in facts.get("entries", []):
        lines.append(f"{e.get('rank', '')}. {entry_line(e)}")
    lines += ["", "#گلزنان #جدول_لیگ #فوتبال"]
    return _lines_budget(lines)


def _hat_tricks(facts: dict) -> str:
    entries = facts.get("entries") or []
    if not entries:
        # fallback: جدول صدرنشینان
        return _list_caption(facts, "🏆 صدرنشینان جدول", "امتیاز", lambda e: f"{e.get('team', '')} — {e.get('points', 0)} امتیاز")
    lines = ["✳️ هتریک‌های اخیر", ""]
    for e in entries:
        lines.append(f"{e.get('rank', '')}. {e.get('player', '')} ({e.get('team', '')}) — {e.get('goals', 0)} گل در بازی مقابل {e.get('match', '')}")
    lines += ["", "#هتریک #گل #فوتبال"]
    return _lines_budget(lines)


def _reminder(facts: dict) -> str:
    return (
        f"⏰ یادآور: {facts.get('hours_before', 12)} ساعت تا شروع بازی\n\n"
        f"{facts.get('home', '')} — {facts.get('away', '')}\n"
        f"ساعت {facts.get('time', '')} به وقت تهران\n"
        f"{facts.get('competition', '')}\n\n"
        "#یادآور_بازی #فوتبال"
    )
