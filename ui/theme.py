"""
Тема: розовый акцент, iOS-стиль, скруглённые карточки
"""
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).parent.parent / "assets"
HERO_ICONS_DIR = ASSETS_DIR / "hero_icons"

C = {
    "bg":             "#0d0d12",
    "bg_secondary":   "#111118",
    "panel":          "#16161e",
    "card":           "#1c1c28",
    "card_hover":     "#26263a",
    "card_active":    "#30304a",
    "border":         "#28283e",
    "border_light":   "#363650",
    "accent":         "#ff2d78",
    "accent_hover":   "#ff5599",
    "accent_dim":     "#b8205a",
    "ally":           "#ff2d78",
    "ally_bg":        "#1a0d16",
    "enemy":          "#3b82f6",
    "enemy_bg":       "#0d1424",
    "text":           "#f0f0f5",
    "text_secondary": "#9898b0",
    "text_muted":     "#585870",
    "good":           "#22c55e",
    "mid":            "#f59e0b",
    "bad":            "#ef4444",
    "highlight":      "#fbbf24",
    "ban":            "#a855f7",
    "ban_bg":         "#180d28",
    "role_carry":     "#f97316",
    "role_mid":       "#a855f7",
    "role_offlane":   "#3b82f6",
    "role_support":   "#22c55e",
    "role_roaming":   "#ef4444",
}

ROLE_COLORS = {
    "Carry":   C["role_carry"],
    "Mid":     C["role_mid"],
    "Offlane": C["role_offlane"],
    "Support": C["role_support"],
    "Roaming": C["role_roaming"],
}

POSITION_INFO = {
    "Carry":   {"icon": "🗡", "label": "Pos1",  "sub": "safelane",   "color": C["role_carry"]},
    "Mid":     {"icon": "⚡", "label": "Pos2",  "sub": "mid",        "color": C["role_mid"]},
    "Offlane": {"icon": "🛡", "label": "Pos3",  "sub": "hardlane",   "color": C["role_offlane"]},
    "Support": {"icon": "💙", "label": "Pos5",  "sub": "hard sup",   "color": C["role_support"]},
    "Roaming": {"icon": "👟", "label": "Pos4",  "sub": "soft sup",   "color": C["role_roaming"]},
}

FONT = "Segoe UI Variable"
FONT_FALLBACK = "Segoe UI"
FONT_MONO = "Cascadia Code"

RADIUS = 6

_image_cache = {}


def _rounded_mask(size, radius=RADIUS):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def _apply_rounded(img, radius=RADIUS):
    mask = _rounded_mask(img.size[0], radius)
    output = Image.new("RGBA", img.size, (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output


def _create_fallback_image(hero_name, size, bg_color):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r, g, b = int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=RADIUS, fill=(r, g, b, 255))
    initials = hero_name[0].upper() if hero_name else "?"
    try:
        font = ImageFont.truetype("segoeui.ttf", size // 3)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", size // 3)
        except Exception:
            font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - bbox[1]), initials,
              fill=(255, 255, 255, 230), font=font)
    return img


def get_hero_image(hero_id, hero_name, size=48, roles=None):
    key = (hero_id, size)
    if key in _image_cache:
        return _image_cache[key]

    icon_path = HERO_ICONS_DIR / f"{hero_id}.png"
    if icon_path.exists():
        img = Image.open(icon_path).convert("RGBA")
        img = img.resize((size, size), Image.LANCZOS)
    else:
        roles = roles or []
        bg = ROLE_COLORS.get(roles[0], C["accent"]) if roles else C["accent"]
        img = _create_fallback_image(hero_name, size, bg)

    img = _apply_rounded(img, min(RADIUS, size // 4))
    photo = ImageTk.PhotoImage(img)
    _image_cache[key] = photo
    return photo


def score_color(score):
    if score >= 65:
        return C["good"]
    if score >= 50:
        return C["mid"]
    return C["bad"]
