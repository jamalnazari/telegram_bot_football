"""رنگ‌ها از کانفیگ خوانده می‌شوند (accent، accent2، متن، muted، پس‌زمینه)."""

from __future__ import annotations


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def blend(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


class Theme:
    def __init__(self, cfg: dict):
        cfg = cfg or {}
        self.bg_top = hex_to_rgb(cfg.get("bg_top", "#0B1B2B"))
        self.bg_bottom = hex_to_rgb(cfg.get("bg_bottom", "#111C26"))
        self.accent = hex_to_rgb(cfg.get("accent", "#00E08A"))
        self.accent2 = hex_to_rgb(cfg.get("accent2", "#FFC247"))
        self.text = hex_to_rgb(cfg.get("text", "#FFFFFF"))
        self.muted = hex_to_rgb(cfg.get("muted", "#93A4B5"))
