"""حسابرسی چیدمان کارت‌ها (بدون نیاز به دید): بررسی کران، همپوشانی و پیکسل‌های متنی."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import ImageDraw

from cards.card import CONTENT_BOTTOM, CONTENT_TOP, MARGIN, W, H, render_card
from config import load_config
from sources.demo_data import ALL_KINDS, demo_package
from text.drawing import enable_recording, get_recorded


def box(rec: dict) -> tuple[float, float, float, float]:
    x, y = rec["xy"]
    width = rec["width"]
    size = rec["size"]
    anchor = rec["anchor"]
    if anchor[0] == "l":
        x0, x1 = x, x + width
    elif anchor[0] == "r":
        x0, x1 = x - width, x
    else:
        x0, x1 = x - width / 2, x + width / 2
    #ارتفاع ink تقریبی: Vazirmatn حدود ۰٫۷۵×size است
    if anchor[1] == "a":
        y0, y1 = y, y + size * 0.75
    elif anchor[1] == "s":
        y0, y1 = y - size * 0.7, y + size * 0.05
    else:
        y0, y1 = y - size * 0.38, y + size * 0.38
    return x0, y0, x1, y1


def overlap(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return ix * iy


def main() -> int:
    cfg = load_config("config.yaml")
    errors: list[str] = []
    for kind in ALL_KINDS:
        facts = demo_package(kind)
        enable_recording()
        img = render_card(facts, "تست", cfg)
        draw = ImageDraw.Draw(img)
        recorded = get_recorded()
        boxes = [(rec, box(rec)) for rec in recorded]
        # ۱) درون کادر
        for rec, b in boxes:
            if b[0] < -2 or b[1] < -2 or b[2] > W + 2 or b[3] > H + 2:
                errors.append(f"{kind}: متن بیرون کادر: {rec['text'][:30]!r} box={tuple(round(v) for v in b)}")
        # ۲) متن contenu درون منطقه‌ی محتوا باشد (نه سر و پایش)
        content = [(r, b) for r, b in boxes if b[1] > 390 and b[3] < 1210]
        # ۳) همپوشانی بین محتوای کنار هم
        for i in range(len(content)):
            for j in range(i + 1, len(content)):
                a, b = content[i][1], content[j][1]
                ov = overlap(a, b)
                if ov <= 0:
                    continue
                area = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
                if area > 0 and ov / area > 0.25:
                    errors.append(
                        f"{kind}: همپوشانی: {content[i][0]['text'][:24]!r} و {content[j][0]['text'][:24]!r}"
                    )
        # ۴) پیکسل‌های متنی در منطقه‌ی محتوا (متن حقيقي کشيده شده)
        pixels = img.crop((MARGIN, CONTENT_TOP, W - MARGIN, CONTENT_BOTTOM))
        colors = pixels.getcolors(maxcolors=1_000_000) or []
        bright = sum(n for n, c in colors if sum(c) > 400)
        total = pixels.width * pixels.height
        ratio = bright / total
        if ratio < 0.0015:
            errors.append(f"{kind}: רק {ratio:.3%} پیکسل روشن در منطقه‌ی محتوا — متن شاید کشيده نشده")
        print(f"{kind}: {len(content)} عنصر محتوا, پیکسل روشن {ratio:.2%}")

    if errors:
        print("\nخطای چیدمان:")
        for e in errors:
            print(" -", e)
        return 1
    print("\nچیدمان OK برای همه‌ی شش کارت")
    return 0


if __name__ == "__main__":
    sys.exit(main())
