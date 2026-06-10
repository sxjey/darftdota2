"""
Python API exposed to JS frontend via pywebview.
"""
import json
import base64
from io import BytesIO
from pathlib import Path
from typing import Optional
from dataclasses import asdict

from PIL import Image

from core.draft_state import get_draft_state, reset_draft, DraftPhase
from scoring.recommender import HeroRecommender, BRACKETS
from scoring.position_assigner import assign_positions, get_priority_position, POSITIONS
from scoring.game_plan import generate_game_plan
from data.heroes_static import get_all_heroes, get_hero_by_id, search_hero
from data.counter_items import get_counter_items, get_hero_attrs
from data.hero_notes import HERO_NOTES

ASSETS_DIR = Path(__file__).parent.parent / "assets"
HERO_ICONS_DIR = ASSETS_DIR / "hero_icons"

ROLE_COLORS = {
    "Carry": "#f97316", "Mid": "#a855f7", "Offlane": "#3b82f6",
    "Support": "#22c55e", "Roaming": "#ef4444",
}

POSITION_INFO = {
    "Carry":   {"icon": "🗡", "label": "Pos1", "sub": "safelane", "color": "#f97316"},
    "Mid":     {"icon": "⚡", "label": "Pos2", "sub": "mid", "color": "#a855f7"},
    "Offlane": {"icon": "🛡", "label": "Pos3", "sub": "hardlane", "color": "#3b82f6"},
    "Support": {"icon": "💙", "label": "Pos5", "sub": "hard sup", "color": "#22c55e"},
    "Roaming": {"icon": "👟", "label": "Pos4", "sub": "soft sup", "color": "#ef4444"},
}

_icon_cache = {}


def _img_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


def _get_hero_img(hero_id: int, size: int = 36) -> str:
    key = (hero_id, size)
    if key in _icon_cache:
        return _icon_cache[key]
    icon_path = HERO_ICONS_DIR / f"{hero_id}.png"
    if icon_path.exists():
        img = Image.open(icon_path).convert("RGBA").resize((size, size), Image.LANCZOS)
    else:
        hero = get_hero_by_id(hero_id)
        name = hero.get("localized_name", "?") if hero else "?"
        roles = hero.get("roles", []) if hero else []
        bg = ROLE_COLORS.get(roles[0], "#ff2d78") if roles else "#ff2d78"
        img = _fallback_img(name, size, bg)
    from PIL import ImageDraw
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    r = min(6, size // 4)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    b64 = _img_to_base64(output)
    _icon_cache[key] = b64
    return b64


def _fallback_img(name: str, size: int, bg: str) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    r, g, b = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
    radius = min(6, size // 4)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=(r, g, b, 255))
    initial = name[0].upper() if name else "?"
    try:
        font = ImageFont.truetype("segoeui.ttf", size // 3)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", size // 3)
        except Exception:
            font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), initial, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - bbox[1]), initial,
              fill=(255, 255, 255, 230), font=font)
    return img


class Api:
    def __init__(self):
        self.recommender = HeroRecommender()

    def get_all_heroes(self):
        heroes = get_all_heroes()
        result = []
        for hid, h in heroes.items():
            attrs = get_hero_attrs(hid)
            result.append({
                "id": hid,
                "name": h.get("name", ""),
                "localized_name": h.get("localized_name", ""),
                "roles": h.get("roles", []),
                "primary_attr": attrs.get("primary_attr", "all"),
                "attack_type": attrs.get("attack_type", "Melee"),
            })
        return result

    def get_hero_icons(self, size=36):
        heroes = get_all_heroes()
        result = {}
        for hid in heroes.keys():
            result[str(hid)] = _get_hero_img(hid, size)
        return result

    def get_draft_state(self):
        state = get_draft_state()
        overrides = state.ally_position_overrides
        asgn = assign_positions(state.ally_picks, overrides=overrides)
        ally = []
        for p in state.ally_picks:
            pos = next((pos for pos, h in asgn.items()
                        if h and h["hero_id"] == p.hero_id), None)
            ally.append({
                "hero_id": p.hero_id,
                "hero_name": p.hero_name,
                "position": pos,
                "is_overridden": p.hero_id in overrides,
            })
        enemy = [{"hero_id": p.hero_id, "hero_name": p.hero_name}
                 for p in state.enemy_picks]
        return {
            "ally_picks": ally,
            "enemy_picks": enemy,
            "ally_bans": list(state.ally_bans),
            "enemy_bans": list(state.enemy_bans),
            "all_picked": list(state.get_all_picked_heroes()),
            "all_banned": list(state.get_all_banned_heroes()),
        }

    def add_ally_pick(self, hero_id):
        state = get_draft_state()
        if len(state.ally_picks) >= 5:
            return False
        if hero_id in state.get_all_picked_heroes():
            return False
        hero = get_hero_by_id(hero_id)
        name = hero.get("localized_name", "?") if hero else "?"
        state.push_undo()
        state.add_ally_pick(hero_id, name)
        return True

    def add_enemy_pick(self, hero_id):
        state = get_draft_state()
        if len(state.enemy_picks) >= 5:
            return False
        if hero_id in state.get_all_picked_heroes():
            return False
        hero = get_hero_by_id(hero_id)
        name = hero.get("localized_name", "?") if hero else "?"
        state.push_undo()
        state.add_enemy_pick(hero_id, name)
        return True

    def remove_ally_pick(self, hero_id):
        state = get_draft_state()
        state.push_undo()
        state.remove_ally_pick(hero_id)

    def remove_enemy_pick(self, hero_id):
        state = get_draft_state()
        state.push_undo()
        state.remove_enemy_pick(hero_id)

    def add_ban(self, hero_id):
        state = get_draft_state()
        state.push_undo()
        state.add_ally_ban(hero_id)

    def remove_ban(self, hero_id):
        state = get_draft_state()
        state.push_undo()
        if hero_id in state.ally_bans:
            state.remove_ally_ban(hero_id)
        else:
            state.remove_enemy_ban(hero_id)

    def set_position_override(self, hero_id, position):
        get_draft_state().set_position_override(hero_id, position if position else None)

    def undo(self):
        return get_draft_state().undo()

    def new_draft(self):
        reset_draft()

    def set_bracket(self, bracket):
        self.recommender.set_bracket(bracket)

    def get_brackets(self):
        return [{"key": k, "label": l, "mmr": m} for k, l, m in BRACKETS]

    def get_analysis(self):
        state = get_draft_state()
        raw = self.recommender.analyze_matchup(state)
        raw["ally_scores"] = [asdict(s) for s in raw.get("ally_scores", [])]
        raw["enemy_scores"] = [asdict(s) for s in raw.get("enemy_scores", [])]
        return raw

    def get_counter_matrix(self):
        state = get_draft_state()
        ally_ids = [p.hero_id for p in state.ally_picks]
        enemy_ids = [p.hero_id for p in state.enemy_picks]
        matchups = self.recommender.matchups
        matrix = {}
        for aid in ally_ids:
            row = {}
            my_matchups = matchups.get(aid, [])
            mdict = {}
            for m in my_matchups:
                eid = m.get("hero_id", 0)
                gp = m.get("games_played", 0)
                if gp > 0:
                    mdict[eid] = round(m.get("wins", 0) / gp * 100, 1)
            for eid in enemy_ids:
                row[str(eid)] = mdict.get(eid, None)
            matrix[str(aid)] = row
        return {
            "allies": [{"hero_id": p.hero_id, "name": p.hero_name}
                       for p in state.ally_picks],
            "enemies": [{"hero_id": p.hero_id, "name": p.hero_name}
                        for p in state.enemy_picks],
            "matrix": matrix,
        }

    def get_recommendations(self):
        state = get_draft_state()
        by_role = self.recommender.get_recommendations_by_role(state, top_per_role=3)
        result = {}
        for role, heroes in by_role.items():
            result[role] = [asdict(h) for h in heroes]
        return result

    def get_ban_suggestions(self):
        state = get_draft_state()
        if not state.ally_picks:
            return []
        picked = state.get_all_picked_heroes()
        banned = state.get_all_banned_heroes()
        all_heroes = get_all_heroes()
        suggestions = []
        matchups = self.recommender.matchups
        for hid, hero in all_heroes.items():
            if hid in picked or hid in banned:
                continue
            counter_score = 0
            reasons = []
            mdata = matchups.get(hid, [])
            mdict = {}
            for m in mdata:
                eid = m.get("hero_id", 0)
                gp = m.get("games_played", 0)
                if gp > 0:
                    mdict[eid] = round(m.get("wins", 0) / gp * 100, 1)
            for pick in state.ally_picks:
                wr = mdict.get(pick.hero_id)
                if wr and wr > 52:
                    counter_score += (wr - 50) * 2
                    reasons.append(f"{wr:.0f}% vs {pick.hero_name}")
            if counter_score > 8 and reasons:
                suggestions.append({
                    "hero_id": hid,
                    "name": hero.get("localized_name", ""),
                    "counter_score": round(counter_score, 1),
                    "reasons": reasons[:3],
                })
        suggestions.sort(key=lambda x: -x["counter_score"])
        return suggestions[:5]

    def get_game_plan(self, hero_id):
        state = get_draft_state()
        plan = generate_game_plan(hero_id, state, self.recommender)
        return asdict(plan)

    def get_position_info(self):
        return POSITION_INFO

    def search_heroes(self, query):
        results = search_hero(query)[:10]
        return [{"id": r["id"], "localized_name": r["localized_name"]}
                for r in results]

    def get_hero_note(self, hero_id):
        return HERO_NOTES.get(hero_id, "")
