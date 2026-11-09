"""کارتِ برندشده ۱۰۸۰×۱۳۵۰ با Pillow. هیچ تصویر خارجی دانلود نمی‌شود.

تل فنی ترکیب آلفا: کشیدن با رنگ RGBA روی تصویر RGBA جایگزین می‌شود، ترکیب نیست.
راه حل: لایه‌ی تزئینی جداگانه با alpha_composite نشانده می‌شود.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from cards import layouts
from cards.theme import Theme, blend
from text.dates import now_tehran, parse_persian_date, persian_datetime_str, persian_date_str
from text.drawing import draw_text
from text.numerals import fa_num

W, H = 1080, 1350
MARGIN = 72
TOP_BAR_H = 18
CONTENT_TOP = 410
CONTENT_BOTTOM = 1190

TITLES = {
    "fixtures": "برنامه‌ی امروز",
    "recap": "مرور نتایج دیروز",
    "scorers": "گلزنان برتر",
    "standings": "صدرنشینان جدول",
    "hat_tricks": "هتریک‌های اخیر",
    "reminder": "یادآور بازی",
}


class Fonts:
    """فونت Vazirmatn (Regular/Medium/Bold/Black) از assets/fonts."""

    _FILES = {
        "regular": "Vazirmatn-Regular.ttf",
        "medium": "Vazirmatn-Medium.ttf",
        "bold": "Vazirmatn-Bold.ttf",
        "black": "Vazirmatn-Black.ttf",
    }

    def __init__(self, base_dir: str | Path = "assets/fonts"):
        self.dir = Path(base_dir)
        self._cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    def get(self, weight: str, size: int) -> ImageFont.FreeTypeFont:
        key = (weight, size)
        if key not in self._cache:
            path = self.dir / self._FILES[weight]
            if not path.exists():
                raise FileNotFoundError(
                    f"فونت {path.name} یافت نشد. والفت Vazirmatn را در assets/fonts قرار دهید."
                )
            self._cache[key] = ImageFont.truetype(str(path), size)
        return self._cache[key]


def _gradient_vertical(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        grad.putpixel((0, y), blend(top, bottom, t))
    return grad.resize((w, h))


def _top_bar(theme: Theme) -> Image.Image:
    """نوار باریک رنگی بالای کارت (اندازه‌ی کامل کارت، فقط ۱۸ پیکسل بالایی painted)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for x in range(W):
        t = x / max(W - 1, 1)
        draw.line([x, 0, x, TOP_BAR_H], fill=blend(theme.accent, theme.accent2, t) + (255,))
    return layer


def _decorate(img: Image.Image, theme: Theme) -> Image.Image:
    """پس‌زمینه + لایه‌ی تزئینی محو (دایره و خط زمین) با alpha_composite."""
    decor = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(decor)
    # دایره‌ی بزرگ محو در پایین‌سره
    draw.ellipse([W - 430, H - 560, W + 160, H + 120], fill=theme.accent + (16,))
    # دایره‌ی کوچک در بالا-چپ
    draw.ellipse([-180, -140, 240, 260], fill=theme.accent2 + (10,))
    # خط زمین
    draw.line([0, int(H * 0.78), W, int(H * 0.78)], fill=theme.accent + (14,), width=2)
    # دایره‌ی میانی محو
    draw.ellipse([W // 2 - 320, H // 2 - 320, W // 2 + 320, H // 2 + 320], outline=theme.muted + (8,), width=2)
    return Image.alpha_composite(img.convert("RGBA"), decor).convert("RGB")


def _subtitle(facts: dict) -> str:
    date_str = facts.get("date")
    if date_str:
        try:
            weekday = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"][
                parse_persian_date(date_str).weekday()
            ]
            return f"{date_str} — {weekday}"
        except (ValueError, IndexError):
            pass
    from text.dates import now_tehran

    return persian_datetime_str(now_tehran())

class Card:
    def __init__(self, cfg: dict, facts: dict, caption: str = ""):
        self.cfg = cfg
        self.facts = facts
        self.caption = caption
        self.theme = Theme(cfg.get("theme", {}))
        self.fonts = Fonts()

    def render(self) -> Image.Image:
        img = _gradient_vertical((W, H), self.theme.bg_top, self.theme.bg_bottom)
        img = _decorate(img, self.theme)
        # نوار باریک رنگی بالای کارت
        img = Image.alpha_composite(img.convert("RGBA"), _top_bar(self.theme)).convert("RGB")
        draw = ImageDraw.Draw(img)
        self._header(draw)
        self._footer(draw)
        layouts.render(
            draw,
            self.fonts,
            self.theme,
            self.facts,
            MARGIN,
            CONTENT_TOP,
            W - 2 * MARGIN,
            CONTENT_BOTTOM - CONTENT_TOP,
        )
        return img

    def _header(self, draw: ImageDraw.ImageDraw) -> None:
        theme = self.theme
        fonts = self.fonts
        brand = fa_num(self.cfg["channel"].get("brand", ""))
        draw_text(draw, (W - MARGIN, 130), brand, fonts.get("regular", 34), theme.muted, anchor="rs")
        title = TITLES.get(self.facts.get("type", ""), "")
        draw_text(draw, (MARGIN, 216), title, fonts.get("black", 84), theme.text, anchor="ls")
        draw_text(draw, (MARGIN, 332), _subtitle(self.facts), fonts.get("medium", 42), theme.muted, anchor="ls")
        draw.rectangle([MARGIN, 380, MARGIN + 240, 386], fill=theme.accent)

    def _footer(self, draw: ImageDraw.ImageDraw) -> None:
        theme = self.theme
        fonts = self.fonts
        faint = blend(theme.bg_bottom, theme.muted, 0.35)
        draw.line([MARGIN, 1216, W - MARGIN, 1216], fill=faint, width=2)
        username = fa_num(self.cfg["channel"].get("username", ""))
        draw_text(draw, (W - MARGIN, 1254), f"@{username}", fonts.get("medium", 36), theme.muted, anchor="rs")
        today = persian_date_str(now_tehran())
        draw_text(draw, (MARGIN, 1252), today, fonts.get("regular", 34), theme.muted, anchor="ls")


def render_card(facts: dict, caption: str, cfg: dict) -> Image.Image:
    """رقم کارت PIL Image برای یک بسته‌ی واقعیت."""
    return Card(cfg, facts, caption).render()


def save_card(img: Image.Image, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p, "PNG")
    return p
