"""
Генератор игрового плана: что собирать, кого фокусить, от кого защищаться.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from data.heroes_static import get_hero_by_id, get_all_heroes
from data.counter_items import get_counter_items, get_hero_attrs, ITEMS
from data.hero_notes import HERO_NOTES
from scoring.recommender import HeroRecommender
from scoring.position_assigner import assign_positions, POSITIONS
from core.draft_state import DraftState


@dataclass
class CounterInfo:
    hero_id: int
    hero_name: str
    winrate_vs: float
    games_played: int
    direction: str  # "you_counter" | "they_counter" | "neutral"


@dataclass
class GamePlan:
    my_hero_id: int
    my_hero_name: str
    my_roles: List[str]
    my_note: str
    my_winrate: float

    i_counter: List[CounterInfo]
    counter_me: List[CounterInfo]
    synergy_with: List[dict]
    focus_targets: List[dict]
    protect_from: List[dict]

    enemy_phys_pct: int
    enemy_magic_pct: int
    enemy_timing: str
    ally_phys_pct: int
    ally_magic_pct: int
    ally_timing: str

    items: List[dict]

    lane_advice: str
    teamfight_advice: str


def _load_matchups() -> Dict[int, Dict[int, Tuple[float, int]]]:
    p = Path(__file__).parent.parent / "cache" / "matchups.json"
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        raw = json.load(f)
    result = {}
    for hid_str, entries in raw.items():
        hid = int(hid_str)
        d = {}
        for e in entries:
            eid = e.get("hero_id", 0)
            gp = e.get("games_played", 0)
            w = e.get("wins", 0)
            if gp > 0:
                d[eid] = (w / gp * 100, gp)
        result[hid] = d
    return result


_matchups_cache = None


def _get_matchups() -> Dict[int, Dict[int, Tuple[float, int]]]:
    global _matchups_cache
    if _matchups_cache is None:
        _matchups_cache = _load_matchups()
    return _matchups_cache


def _analyze_comp(heroes_ids: List[int]) -> Dict:
    ROLE_TAGS = {
        "Carry": {"dmg_type": "physical", "timing": "late"},
        "Mid": {"dmg_type": "mixed", "timing": "mid"},
        "Offlane": {"dmg_type": "mixed", "timing": "mid"},
        "Support": {"dmg_type": "magical", "timing": "early"},
        "Roaming": {"dmg_type": "magical", "timing": "early"},
    }
    phys = 0
    mag = 0
    early = 0
    mid_t = 0
    late = 0
    for hid in heroes_ids:
        hero = get_hero_by_id(hid)
        if not hero:
            continue
        roles = hero.get("roles", [])
        attrs = get_hero_attrs(hid)
        attr = attrs.get("primary_attr", "all")
        for r in roles:
            tags = ROLE_TAGS.get(r, {})
            dt = tags.get("dmg_type", "mixed")
            tm = tags.get("timing", "mid")
            if dt == "physical":
                phys += 1
            elif dt == "magical":
                mag += 1
            else:
                phys += 0.5
                mag += 0.5
            if tm == "early":
                early += 1
            elif tm == "late":
                late += 1
            else:
                mid_t += 1
        if attr == "agi":
            phys += 0.5
        elif attr == "int":
            mag += 0.5
    total = max(phys + mag, 1)
    return {
        "physical_pct": round(phys / total * 100),
        "magical_pct": round(mag / total * 100),
        "timing": "early" if early > late else "late" if late > early else "balanced",
    }


def generate_game_plan(
    my_hero_id: int,
    draft_state: DraftState,
    recommender: HeroRecommender,
) -> GamePlan:
    hero = get_hero_by_id(my_hero_id)
    my_name = hero.get("localized_name", "?") if hero else "?"
    my_roles = hero.get("roles", []) if hero else []
    my_note = HERO_NOTES.get(my_hero_id, "")
    my_winrate = recommender._get_winrate(my_hero_id)

    matchups = _get_matchups()
    my_matchups = matchups.get(my_hero_id, {})

    enemy_ids = [p.hero_id for p in draft_state.enemy_picks]
    ally_ids = [p.hero_id for p in draft_state.ally_picks
                if p.hero_id != my_hero_id]

    i_counter = []
    counter_me = []
    for eid in enemy_ids:
        wr, gp = my_matchups.get(eid, (50.0, 0))
        ehero = get_hero_by_id(eid)
        ename = ehero.get("localized_name", "?") if ehero else "?"
        if wr > 52:
            i_counter.append(CounterInfo(eid, ename, wr, gp, "you_counter"))
        elif wr < 48:
            counter_me.append(CounterInfo(eid, ename, wr, gp, "they_counter"))
        else:
            pass

    i_counter.sort(key=lambda x: -x.winrate_vs)
    counter_me.sort(key=lambda x: x.winrate_vs)

    synergy_pairs = recommender._get_synergy_pairs()
    synergy_with = []
    for aid in ally_ids:
        ahero = get_hero_by_id(aid)
        aname = ahero.get("localized_name", "?") if ahero else "?"
        pair = tuple(sorted([my_hero_id, aid]))
        bonus = synergy_pairs.get(pair, 0)
        role_overlap = len(set(my_roles) & set(ahero.get("roles", []))) if ahero else 0
        synergy_with.append({
            "hero_id": aid,
            "name": aname,
            "synergy_bonus": bonus,
            "role_overlap": role_overlap,
        })

    focus_targets = []
    for eid in enemy_ids:
        ehero = get_hero_by_id(eid)
        if not ehero:
            continue
        ename = ehero.get("localized_name", "?")
        e_roles = ehero.get("roles", [])
        priority = 0
        reason_parts = []
        if "Carry" in e_roles:
            priority += 3
            reason_parts.append("кэрри — приоритет #1")
        if "Mid" in e_roles:
            priority += 2
            reason_parts.append("мидер — DPS")
        e_attrs = get_hero_attrs(eid)
        if e_attrs.get("primary_attr") == "agi":
            priority += 1
            reason_parts.append("хрупкий")
        wr_vs_me = my_matchups.get(eid, (50.0, 0))[0]
        if wr_vs_me > 52:
            priority += 1
            reason_parts.append(f"ты его контришь ({wr_vs_me:.0f}%)")
        elif wr_vs_me < 48:
            priority -= 2
            reason_parts.append(f"сложно убить ({wr_vs_me:.0f}%)")
        focus_targets.append({
            "hero_id": eid,
            "name": ename,
            "priority": priority,
            "reasons": reason_parts,
        })
    focus_targets.sort(key=lambda x: -x["priority"])

    protect_from = []
    for eid in enemy_ids:
        ehero = get_hero_by_id(eid)
        if not ehero:
            continue
        ename = ehero.get("localized_name", "?")
        e_roles = ehero.get("roles", [])
        danger = 0
        reason_parts = []
        wr_vs_me = my_matchups.get(eid, (50.0, 0))[0]
        if wr_vs_me < 48:
            danger += 3
            reason_parts.append(f"контрит тебя ({wr_vs_me:.0f}%)")
        e_attrs = get_hero_attrs(eid)
        if "Disabler" in e_attrs.get("roles", []):
            danger += 2
            reason_parts.append("дизейблер")
        if "Nuker" in e_attrs.get("roles", []):
            danger += 1
            reason_parts.append("нюкер")
        if "Carry" in e_roles:
            danger += 1
            reason_parts.append("кэрри в лейте")
        if "Initiator" in e_attrs.get("roles", []):
            danger += 1
            reason_parts.append("инициатор")
        if danger > 0:
            protect_from.append({
                "hero_id": eid,
                "name": ename,
                "danger": danger,
                "reasons": reason_parts,
            })
    protect_from.sort(key=lambda x: -x["danger"])

    enemy_comp = _analyze_comp(enemy_ids)
    ally_comp_ids = [p.hero_id for p in draft_state.ally_picks]
    ally_comp = _analyze_comp(ally_comp_ids)

    items = get_counter_items(my_hero_id, enemy_ids)

    lane_map = {
        "Carry": "Безопасная линия (Bot для Radiant)",
        "Mid": "Мидлейн — 1 на 1",
        "Offlane": "Сложная линия (Top для Radiant)",
        "Support": "Саппорт при кэрри / роум",
        "Roaming": "Роум между линиями",
    }
    my_lane = lane_map.get(my_roles[0] if my_roles else "", "Определись по роли")
    lane_advice = f"Лайн: {my_lane}.\n"
    if counter_me:
        worst = counter_me[0]
        lane_advice += f"⚠ Осторожно: {worst.hero_name} ({worst.winrate_vs:.0f}%) — держись от него подальше.\n"
    if i_counter:
        best = i_counter[0]
        lane_advice += f"✅ Агрессуй на {best.hero_name} ({best.winrate_vs:.0f}%) — ты его контришь."

    teamfight_advice = ""
    if focus_targets:
        t1 = focus_targets[0]
        teamfight_advice += f"🎯 Фокуси: {t1['name']} ({', '.join(t1['reasons'][:2])})\n"
    if protect_from:
        p1 = protect_from[0]
        teamfight_advice += f"🛡 Сторонись: {p1['name']} ({', '.join(p1['reasons'][:2])})\n"
    if enemy_comp["physical_pct"] > 60:
        teamfight_advice += "Враги — физ. урон. Собирай броню/Blade Mail/Halberd.\n"
    elif enemy_comp["magical_pct"] > 60:
        teamfight_advice += "Враги — маг. урон. BKB/Pipe/Glimmer обязательны.\n"
    else:
        teamfight_advice += "У врагов смешанный урон — нужны и BKB, и броня.\n"
    if enemy_comp["timing"] == "early":
        teamfight_advice += "Враги сильны рано — не дай им раскатать, дотерпи до лейта."
    elif enemy_comp["timing"] == "late":
        teamfight_advice += "Враги раскачиваются в лейте — дави рано, не дай фармить."
    else:
        teamfight_advice += "Враги ровные по таймингу — выигрывай позиционированием."

    return GamePlan(
        my_hero_id=my_hero_id,
        my_hero_name=my_name,
        my_roles=my_roles,
        my_note=my_note,
        my_winrate=my_winrate,
        i_counter=i_counter,
        counter_me=counter_me,
        synergy_with=synergy_with,
        focus_targets=focus_targets,
        protect_from=protect_from,
        enemy_phys_pct=enemy_comp["physical_pct"],
        enemy_magic_pct=enemy_comp["magical_pct"],
        enemy_timing=enemy_comp["timing"],
        ally_phys_pct=ally_comp["physical_pct"],
        ally_magic_pct=ally_comp["magical_pct"],
        ally_timing=ally_comp["timing"],
        items=items,
        lane_advice=lane_advice,
        teamfight_advice=teamfight_advice,
    )
