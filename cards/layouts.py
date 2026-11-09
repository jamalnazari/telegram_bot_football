"""چیدمان‌های کارت: ارتفاع سطرها طوری محاسبه می‌شود که فضا خالی نماند
(بین ۸۶ تا ۱۵۰ پیکسل) و بلوک محتوا عمودی وسط‌چین می‌شود.

نکته‌ی کلیدی: anchorهای Pillow بصری هستند. برای متن‌هایی که باید در سمت
چپ تصویر باشند (متن فارسی، راست‌چین) از "rm"/"rs" استفاده می‌کنیم، برای
ستون ساعت و اعداد بزرگ (متن لاتین/فارسی در سمت چپ) از "lm"/"ls".
"""

from __future__ import annotations

from PIL import ImageDraw

from cards.theme import Theme
from text.drawing import draw_text, fit_font
from text.numerals import fa_num

ROW_MIN = 86
ROW_MAX = 150


def _clamp_row_h(avail_h: int, n_rows: int, lo: int = ROW_MIN) -> int:
    if n_rows <= 0:
        return ROW_MAX
    return max(lo, min(ROW_MAX, avail_h // n_rows))


def _fit(draw: ImageDraw.ImageDraw, text: str, font, max_width: float, min_size: int = 28):
    return fit_font(draw, text, font, max_width, min_size)


def render(draw, fonts, theme: Theme, facts: dict, x: int, y: int, w: int, avail_h: int) -> None:
    kind = facts.get("type")
    if kind == "fixtures":
        _fixtures(draw, fonts, theme, facts, x, y, w, avail_h)
    elif kind == "recap":
        _recap(draw, fonts, theme, facts, x, y, w, avail_h)
    elif kind == "reminder":
        _reminder(draw, fonts, theme, facts, x, y, w, avail_h)
    elif kind in ("scorers", "standings", "hat_tricks"):
        _list(draw, fonts, theme, facts, x, y, w, avail_h)
    else:
        raise ValueError(f"چیدمان برای نوع {kind} وجود ندارد")


def _fixtures(draw, fonts, theme, facts, x, y, w, avail_h) -> None:
    groups = facts.get("groups", [])
    total_rows = sum(len(g.get("matches", [])) for g in groups) + len(groups)
    row_h = _clamp_row_h(avail_h, total_rows)
    block_h = total_rows * row_h
    cy = y + max(0, (avail_h - block_h) // 2)

    for g in groups:
        mid = cy + row_h / 2
        title = fa_num(g.get("competition", ""))
        f = _fit(draw, title, fonts.get("medium", 40), w - 240)
        draw_text(draw, (x + w - 40, mid), title, f, theme.accent2, anchor="rm")
        cy += row_h
        for m in g.get("matches", []):
            mid = cy + row_h / 2
            time = fa_num(m.get("time", ""))
            draw_text(draw, (x, mid), time, fonts.get("medium", 42), theme.text, anchor="lm")
            label = fa_num(f"{m.get('home', '')}  —  {m.get('away', '')}")
            f = _fit(draw, label, fonts.get("bold", 46), w - 240)
            draw_text(draw, (x + w - 40, mid), label, f, theme.text, anchor="rm")
            cy += row_h


def _recap(draw, fonts, theme, facts, x, y, w, avail_h) -> None:
    matches = facts.get("matches", [])
    n = len(matches)
    if n == 0:
        return
    row_h = _clamp_row_h(avail_h, n, lo=112)
    block_h = n * row_h
    cy = y + max(0, (avail_h - block_h) // 2)

    for m in matches:
        mid = cy + row_h / 2
        score = fa_num(m.get("score", ""))
        draw_text(draw, (x + 14, mid), score, fonts.get("black", 62), theme.accent2, anchor="lm")
        label = fa_num(f"{m.get('home', '')} — {m.get('away', '')}")
        f = _fit(draw, label, fonts.get("bold", 46), w - 250)
        draw_text(draw, (x + w - 40, mid - 34), label, f, theme.text, anchor="rm")
        goals = fa_num(f"گل‌های بازی: {m.get('total', 0)}")
        draw_text(draw, (x + w - 40, mid + 40), goals, fonts.get("regular", 36), theme.muted, anchor="rm")
        cy += row_h


def _reminder(draw, fonts, theme, facts, x, y, w, avail_h) -> None:
    hours = fa_num(str(facts.get("hours_before", 12)))
    match = fa_num(f"{facts.get('home', '')} — {facts.get('away', '')}")
    f_match = _fit(draw, match, fonts.get("bold", 64), w - 160)
    time = fa_num(facts.get("time", ""))
    comp = fa_num(facts.get("competition", ""))

    lines = [
        (f"{hours} ساعت", fonts.get("black", 150), theme.accent, 168),
        ("تا شروع بازی", fonts.get("medium", 46), theme.muted, 56),
        (match, f_match, theme.text, 76),
        (f"ساعت {time} به وقت تهران", fonts.get("medium", 44), theme.text, 54),
        (comp, fonts.get("medium", 40), theme.accent2, 48),
    ]
    gap = 34
    block_h = sum(h for _, _, _, h in lines) + gap * (len(lines) - 1)
    cy = y + max(0, (avail_h - block_h) // 2)
    cx = x + w / 2
    for text, font, color, line_h in lines:
        draw_text(draw, (cx, cy + line_h / 2), text, font, color, anchor="mm")
        cy += line_h + gap


def _list(draw, fonts, theme, facts, x, y, w, avail_h) -> None:
    # اگر هتریک خالی بود (count: 0)، به کارت جدول fallback می‌کنیم.
    if facts.get("type") == "hat_tricks" and facts.get("count", 0) == 0:
        entries = facts.get("fallback_standings", [])
        mode = "standings"
    else:
        entries = facts.get("entries", [])
        mode = facts.get("type")

    n = len(entries)
    if n == 0:
        return
    row_h = _clamp_row_h(avail_h, n, lo=112 if mode == "standings" else ROW_MIN)
    block_h = n * row_h
    cy = y + max(0, (avail_h - block_h) // 2)

    for e in entries:
        mid = cy + row_h / 2
        cx = x + w - 46
        rank = fa_num(str(e.get("rank", "")))
        # چیپ شماره
        draw.ellipse([cx - 34, mid - 34, cx + 34, mid + 34], fill=theme.accent)
        draw_text(draw, (cx, mid), rank, fonts.get("bold", 40), theme.bg_top, anchor="mm")

        if mode in ("scorers", "hat_tricks"):
            name = fa_num(e.get("player", ""))
            sub = fa_num(e.get("team", ""))
            number = fa_num(str(e.get("goals", 0)))
        else:
            name = fa_num(e.get("team", ""))
            sub = fa_num(e.get("competition", ""))
            number = fa_num(str(e.get("points", 0)))

        name_x = cx - 116
        f_name = _fit(draw, name, fonts.get("bold", 46), w - 300)
        draw_text(draw, (name_x, mid - 30), name, f_name, theme.text, anchor="rm")
        if mode == "standings":
            stats = fa_num(
                f"{e.get('played', 0)} بازی · {e.get('won', 0)} برد · "
                f"{e.get('drawn', 0)} تساوی · {e.get('lost', 0)} بارتخت"
            )
            draw_text(draw, (name_x, mid + 42), stats, fonts.get("regular", 34), theme.muted, anchor="rm")
        else:
            f_sub = _fit(draw, sub, fonts.get("regular", 36), w - 300)
            draw_text(draw, (name_x, mid + 34), sub, f_sub, theme.muted, anchor="rm")

        draw_text(draw, (x + 18, mid), number, fonts.get("black", 62), theme.accent2, anchor="lm")
        cy += row_h
