"""
Статическая база предметов Dota 2 и правила контр-айтемов.
"""
from typing import List, Dict, Optional

ITEMS = {
    "armor": {
        "name": "Assault Cuirass",
        "icon": "🛡",
        "cost": 5075,
        "desc": "-5 броня врагам, +30 ярост. атак, +10 броня",
        "tags": ["physical_def", "aura", "push"],
    },
    "bkb": {
        "name": "Black King Bar",
        "icon": "🔮",
        "cost": 4050,
        "desc": "Иммунитет к магии 8-5 сек. Контрит массовый маг. контроль.",
        "tags": ["magic_def", "channel_break"],
    },
    "blade_mail": {
        "name": "Blade Mail",
        "icon": "⚔",
        "cost": 2100,
        "desc": "Возврат урона. Контрит физических дамагеров.",
        "tags": ["physical_def", "reflect"],
    },
    "butterfly": {
        "name": "Butterfly",
        "icon": "🦋",
        "cost": 4975,
        "desc": "+35 урон, +30 ярост. атак, +35% уклонение",
        "tags": ["physical_def", "dodge", "agi_core"],
    },
    "crimson_guard": {
        "name": "Crimson Guard",
        "icon": "🛡",
        "cost": 3700,
        "desc": "Блок урона для команды. Контрит массовый физ. урон.",
        "tags": ["physical_def", "team_def", "block"],
    },
    "cyclone": {
        "name": "Eul's Scepter of Divinity",
        "icon": "🌪",
        "cost": 2725,
        "desc": "Подброс себя/врага. Снятие дебаффов, мана реген.",
        "tags": ["utility", "dispel", "setup"],
    },
    "daedalus": {
        "name": "Daedalus",
        "icon": "🎯",
        "cost": 5150,
        "desc": "+88 урон, 30% крит x2.15. Для физ. дамагеров.",
        "tags": ["physical_off", "crit"],
    },
    "desolator": {
        "name": "Desolator",
        "icon": "🔴",
        "cost": 3500,
        "desc": "-6 броня, +50 урон. Контрит броню и башни.",
        "tags": ["physical_off", "armor_red"],
    },
    "diffusal": {
        "name": "Diffusal Blade",
        "icon": "💜",
        "cost": 3150,
        "desc": "Mana Break +20/40, медленный. Контрит мана-зависимых.",
        "tags": ["mana_burn", "slow", "agi_core"],
    },
    "force_staff": {
        "name": "Force Staff",
        "icon": "💨",
        "cost": 1900,
        "desc": "Толчок союзника/врага. Спасение и позиционирование.",
        "tags": ["utility", "save", "position"],
    },
    "ghost": {
        "name": "Ghost Scepter",
        "icon": "👻",
        "cost": 1500,
        "desc": "Иммунитет к физ. урону 4 сек. Контрит физ. дамагеров.",
        "tags": ["physical_def", "ethereal"],
    },
    "glimmer": {
        "name": "Glimmer Cape",
        "icon": "✨",
        "cost": 2350,
        "desc": "Невидимость + маг. резист союзнику. Спасение саппорта.",
        "tags": ["magic_def", "save", "support"],
    },
    "guardian_greaves": {
        "name": "Guardian Greaves",
        "icon": "🩹",
        "cost": 5050,
        "desc": "Хил команды, мана реген, аура. Лучший саппорт-айтем.",
        "tags": ["team_def", "heal", "support"],
    },
    "halberd": {
        "name": "Heaven's Halberd",
        "icon": "🔱",
        "cost": 3500,
        "desc": "Дизарм врага 5 сек. Контрит физ. дамагеров.",
        "tags": ["physical_def", "disarm"],
    },
    "hurricane_pike": {
        "name": "Hurricane Pike",
        "icon": "🔱",
        "cost": 4525,
        "desc": "Отталкивание + 5 атак. Кайт для рейндж героев.",
        "tags": ["physical_def", "kite", "range_core"],
    },
    "linkens": {
        "name": "Linken's Sphere",
        "icon": "🔵",
        "cost": 4600,
        "desc": "Блок 1 скилл каждые 13 сек. Контрит сингл-таргет ульты.",
        "tags": ["magic_def", "spell_block"],
    },
    "lotus_orb": {
        "name": "Lotus Orb",
        "icon": "🌸",
        "cost": 4000,
        "desc": "Отражение скилла на кастера. Снятие дебаффов.",
        "tags": ["magic_def", "reflect", "dispel"],
    },
    "maelstrom": {
        "name": "Maelstrom",
        "icon": "⚡",
        "cost": 2700,
        "desc": "Цепная молния 25%. Фарм + AoE урон.",
        "tags": ["physical_off", "farming", "agi_core"],
    },
    "manta": {
        "name": "Manta Style",
        "icon": "👤",
        "cost": 4650,
        "desc": "Иллюзии + снятие дебаффов. Пуш + DPS.",
        "tags": ["physical_off", "dispel", "push", "agi_core"],
    },
    "medallion": {
        "name": "Medallion of Courage",
        "icon": "☀",
        "cost": 1175,
        "desc": "-7 броня врагу. Дешёвый контр брони для роумеров.",
        "tags": ["armor_red", "support"],
    },
    "mjollnir": {
        "name": "Mjollnir",
        "icon": "🔨",
        "cost": 6200,
        "desc": "Цепная молния 25% + Static Charge. AoE физ.",
        "tags": ["physical_off", "farming", "agi_core"],
    },
    "monkey_king_bar": {
        "name": "Monkey King Bar",
        "icon": "棍",
        "cost": 4175,
        "desc": "+40 урон, True Strike. Контрит уклонение (Butterfly, Blur).",
        "tags": ["physical_off", "true_strike"],
    },
    "nullifier": {
        "name": "Nullifier",
        "icon": "🚫",
        "cost": 4725,
        "desc": "Снятие баффов врага + замедление. Контрит спасения.",
        "tags": ["dispel", "anti_save"],
    },
    "octarine": {
        "name": "Octarine Core",
        "icon": "💜",
        "cost": 5600,
        "desc": "+25% CDR, спел вампиризм. Для маг. нюкеров.",
        "tags": ["magic_off", "cd_reduction", "int_core"],
    },
    "orb_of_corrosion": {
        "name": "Orb of Corrosion",
        "icon": "🟢",
        "cost": 925,
        "desc": "-3 броня, DoT, замедление. Ранний лейн айтем.",
        "tags": ["armor_red", "early", "melee"],
    },
    "pipe": {
        "name": "Pipe of Insight",
        "icon": "🫧",
        "cost": 3475,
        "desc": "Маг. щит команды 400. Контрит маг. AoE ульты.",
        "tags": ["magic_def", "team_def"],
    },
    "plate_mail": {
        "name": "Shiva's Guard",
        "icon": "❄",
        "cost": 4750,
        "desc": "-40% IAS врагов, -4 броня аура, AoE замедление.",
        "tags": ["physical_def", "armor_red", "int_core"],
    },
    "radiance": {
        "name": "Radiance",
        "icon": "🔥",
        "cost": 5150,
        "desc": "AoE урон 60/сек. Фарм + замедление миссов.",
        "tags": ["physical_off", "farming", "aura"],
    },
    "sange_yasha": {
        "name": "Sange and Yasha",
        "icon": "⚔",
        "cost": 4100,
        "desc": "+30% статус резист, замедление атак, баланс DPS/танка.",
        "tags": ["hybrid", "status_resist"],
    },
    "scythe": {
        "name": "Scythe of Vyse",
        "icon": "🐑",
        "cost": 5650,
        "desc": "Хекс 3.5 сек. Лучший контроль одного врага.",
        "tags": ["hard_cc", "int_core"],
    },
    "silver_edge": {
        "name": "Silver Edge",
        "icon": "🗡",
        "cost": 5300,
        "desc": "Инвиз + дизарм/урон. Контрит пассивки (Bristle, PA).",
        "tags": ["break", "physical_off", "invis"],
    },
    "solar_crest": {
        "name": "Solar Crest",
        "icon": "☀",
        "cost": 2625,
        "desc": "-10 броня врагу, уклонение союзнику. Апгрейд медальона.",
        "tags": ["armor_red", "support", "dodge"],
    },
    "sphere": {
        "name": "Abyssal Blade",
        "icon": "⚡",
        "cost": 6250,
        "desc": "Стан через BKB 2 сек. Контрит BKB-носителей.",
        "tags": ["hard_cc", "bkb_counter", "melee"],
    },
    "spirit_vessel": {
        "name": "Spirit Vessel",
        "icon": "🏺",
        "cost": 2940,
        "desc": "-30% хил/реген врагу. Контрит вампиризм и хилеры.",
        "tags": ["anti_heal", "support"],
    },
    "vanguard": {
        "name": "Vanguard",
        "icon": "🛡",
        "cost": 1825,
        "desc": "Блок урона 70. Ранняя выживаемость милишникам.",
        "tags": ["physical_def", "block", "early"],
    },
    "veil": {
        "name": "Veil of Discord",
        "icon": "🌀",
        "cost": 1525,
        "desc": "+25% маг. урон в области. Дешёвый маг. усилитель.",
        "tags": ["magic_off", "amplify"],
    },
    "witch_blade": {
        "name": "Witch Blade",
        "icon": "🔮",
        "cost": 2450,
        "desc": "+20 урон, замедление, маг. усилитель. Мид-гейм инт.",
        "tags": ["magic_off", "int_core", "slow"],
    },
}


def _load_hero_attrs() -> Dict[int, dict]:
    import json
    from pathlib import Path
    p = Path(__file__).parent.parent / "cache" / "_heroes.json"
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        heroes = json.load(f)
    return {h["id"]: h for h in heroes}


_hero_attrs_cache = None


def get_hero_attrs(hero_id: int) -> dict:
    global _hero_attrs_cache
    if _hero_attrs_cache is None:
        _hero_attrs_cache = _load_hero_attrs()
    return _hero_attrs_cache.get(hero_id, {})


def get_counter_items(my_hero_id: int, enemy_hero_ids: List[int]) -> List[dict]:
    """
    Возвращает список рекомендованных контр-айтемов для героя my_hero_id
    против списка вражеских hero_ids.
    Каждый элемент: {"key", "name", "icon", "cost", "reason", "priority"}
    """
    recs = []
    enemy_attrs = [get_hero_attrs(eid) for eid in enemy_hero_ids]
    my_attr = get_hero_attrs(my_hero_id)

    my_primary = my_attr.get("primary_attr", "all")
    my_attack = my_attr.get("attack_type", "Melee")
    my_roles = set()

    from data.heroes_static import get_hero_by_id
    hero = get_hero_by_id(my_hero_id)
    if hero:
        my_roles = set(hero.get("roles", []))

    enemy_has_bkb = False
    enemy_magic_nukers = 0
    enemy_physical_carry = 0
    enemy_strong_passives = False
    enemy_healers = False
    enemy_evasion = False
    enemy_armor = 0
    enemy_high_hp = 0
    enemy_illusions = False
    enemy_stunners = 0
    enemy_single_target_ult = False

    for ea in enemy_attrs:
        if not ea:
            continue
        attr = ea.get("primary_attr", "all")
        roles = set(ea.get("roles", []))
        localized = ea.get("localized_name", "")

        if attr == "str":
            enemy_high_hp += 1
        if attr == "agi":
            enemy_physical_carry += 1
        if attr == "int":
            enemy_magic_nukers += 1

        if "Nuker" in roles:
            enemy_magic_nukers += 1
        if "Carry" in roles:
            enemy_physical_carry += 1
        if "Durable" in roles:
            enemy_armor += 1
        if "Escape" in roles:
            enemy_evasion = True
        if "Disabler" in roles:
            enemy_stunners += 1
        if "Support" in roles or "Durable" in roles:
            enemy_healers = True

        if localized in ("Anti-Mage", "Phantom Assassin", "Bristleback",
                         "Huskar", "Spectre", "Broodmother"):
            enemy_strong_passives = True
        if localized in ("Anti-Mage", "Phantom Lancer", "Naga Siren",
                         "Terrorblade", "Chaos Knight"):
            enemy_illusions = True
        if localized in ("Lina", "Lion", "Shadow Shaman", "Bane",
                         "Witch Doctor", "Tinker", "Zeus"):
            enemy_single_target_ult = True

    if enemy_magic_nukers >= 2:
        recs.append({"key": "bkb", "name": ITEMS["bkb"]["name"],
                     "icon": ITEMS["bkb"]["icon"], "cost": ITEMS["bkb"]["cost"],
                     "reason": f"У врагов {enemy_magic_nukers} маг. нюкеров — BKB обязателен",
                     "priority": 5})
        recs.append({"key": "pipe", "name": ITEMS["pipe"]["name"],
                     "icon": ITEMS["pipe"]["icon"], "cost": ITEMS["pipe"]["cost"],
                     "reason": "Pipe защитит команду от маг. ультов",
                     "priority": 3})
        if "Support" in my_roles:
            recs.append({"key": "glimmer", "name": ITEMS["glimmer"]["name"],
                         "icon": ITEMS["glimmer"]["icon"], "cost": ITEMS["glimmer"]["cost"],
                         "reason": "Спасай союзников от маг. урона",
                         "priority": 4})

    if enemy_physical_carry >= 2:
        recs.append({"key": "blade_mail", "name": ITEMS["blade_mail"]["name"],
                     "icon": ITEMS["blade_mail"]["icon"], "cost": ITEMS["blade_mail"]["cost"],
                     "reason": "Возврат урона физ. дамагерам",
                     "priority": 4})
        recs.append({"key": "halberd", "name": ITEMS["halberd"]["name"],
                     "icon": ITEMS["halberd"]["icon"], "cost": ITEMS["halberd"]["cost"],
                     "reason": "Дизарм не даёт бить физ. кэрри",
                     "priority": 3})
        if my_primary == "int":
            recs.append({"key": "ghost", "name": ITEMS["ghost"]["name"],
                         "icon": ITEMS["ghost"]["icon"], "cost": ITEMS["ghost"]["cost"],
                         "reason": "Иммунитет к физ. урону пока ультуешь",
                         "priority": 3})

    if enemy_stunners >= 2:
        recs.append({"key": "bkb", "name": ITEMS["bkb"]["name"],
                     "icon": ITEMS["bkb"]["icon"], "cost": ITEMS["bkb"]["cost"],
                     "reason": f"У врагов {enemy_stunners} дизейблера — BKB!",
                     "priority": 5})
        if "Carry" in my_roles or "Mid" in my_roles:
            recs.append({"key": "sange_yasha", "name": ITEMS["sange_yasha"]["name"],
                         "icon": ITEMS["sange_yasha"]["icon"], "cost": ITEMS["sange_yasha"]["cost"],
                         "reason": "30% статус резист — меньше оглушений",
                         "priority": 2})

    if enemy_single_target_ult:
        recs.append({"key": "linkens", "name": ITEMS["linkens"]["name"],
                     "icon": ITEMS["linkens"]["icon"], "cost": ITEMS["linkens"]["cost"],
                     "reason": "Блок сингл-таргет ульты (Lina, Lion и т.д.)",
                     "priority": 3})
        recs.append({"key": "lotus_orb", "name": ITEMS["lotus_orb"]["name"],
                     "icon": ITEMS["lotus_orb"]["icon"], "cost": ITEMS["lotus_orb"]["cost"],
                     "reason": "Отражение сингл-таргет скиллов + диспелл",
                     "priority": 3})

    if enemy_strong_passives:
        recs.append({"key": "silver_edge", "name": ITEMS["silver_edge"]["name"],
                     "icon": ITEMS["silver_edge"]["icon"], "cost": ITEMS["silver_edge"]["cost"],
                     "reason": "Break отключает пассивки (AM, PA, Bristle)",
                     "priority": 4})

    if enemy_evasion or enemy_physical_carry >= 2:
        recs.append({"key": "monkey_king_bar", "name": ITEMS["monkey_king_bar"]["name"],
                     "icon": ITEMS["monkey_king_bar"]["icon"], "cost": ITEMS["monkey_king_bar"]["cost"],
                     "reason": "True Strike контрит уклонение",
                     "priority": 3})

    if enemy_high_hp >= 2 or enemy_armor >= 2:
        recs.append({"key": "desolator", "name": ITEMS["desolator"]["name"],
                     "icon": ITEMS["desolator"]["icon"], "cost": ITEMS["desolator"]["cost"],
                     "reason": "Снижение брони против танков",
                     "priority": 2})
        if "Support" in my_roles or "Roaming" in my_roles:
            recs.append({"key": "medallion", "name": ITEMS["medallion"]["name"],
                         "icon": ITEMS["medallion"]["icon"], "cost": ITEMS["medallion"]["cost"],
                         "reason": "Дешёвое снижение брони для фокуса",
                         "priority": 2})
            recs.append({"key": "solar_crest", "name": ITEMS["solar_crest"]["name"],
                         "icon": ITEMS["solar_crest"]["icon"], "cost": ITEMS["solar_crest"]["cost"],
                         "reason": "Апгрейд медальона, уклонение союзнику",
                         "priority": 2})

    if enemy_healers:
        recs.append({"key": "spirit_vessel", "name": ITEMS["spirit_vessel"]["name"],
                     "icon": ITEMS["spirit_vessel"]["icon"], "cost": ITEMS["spirit_vessel"]["cost"],
                     "reason": "Снижение хила/регена врагов",
                     "priority": 3})

    if enemy_illusions:
        recs.append({"key": "maelstrom", "name": ITEMS["maelstrom"]["name"],
                     "icon": ITEMS["maelstrom"]["icon"], "cost": ITEMS["maelstrom"]["cost"],
                     "reason": "AoE цепная молния против иллюзий",
                     "priority": 2})
        recs.append({"key": "mjollnir", "name": ITEMS["mjollnir"]["name"],
                     "icon": ITEMS["mjollnir"]["icon"], "cost": ITEMS["mjollnir"]["cost"],
                     "reason": "Максимальный AoE против иллюзий",
                     "priority": 2})

    if "Carry" in my_roles and my_primary == "agi":
        recs.append({"key": "manta", "name": ITEMS["manta"]["name"],
                     "icon": ITEMS["manta"]["icon"], "cost": ITEMS["manta"]["cost"],
                     "reason": "DPS + диспелл + пуш. Классика для AGI кэрри.",
                     "priority": 2})
        recs.append({"key": "butterfly", "name": ITEMS["butterfly"]["name"],
                     "icon": ITEMS["butterfly"]["icon"], "cost": ITEMS["butterfly"]["cost"],
                     "reason": "DPS + уклонение. Лейт-гейм стандарт.",
                     "priority": 1})
        recs.append({"key": "daedalus", "name": ITEMS["daedalus"]["name"],
                     "icon": ITEMS["daedalus"]["icon"], "cost": ITEMS["daedalus"]["cost"],
                     "reason": "Максимальный физ. DPS через криты.",
                     "priority": 1})

    if "Mid" in my_roles and my_primary == "int":
        recs.append({"key": "octarine", "name": ITEMS["octarine"]["name"],
                     "icon": ITEMS["octarine"]["icon"], "cost": ITEMS["octarine"]["cost"],
                     "reason": "CDR + спел вамп — стандарт для INT мидера",
                     "priority": 2})
        recs.append({"key": "witch_blade", "name": ITEMS["witch_blade"]["name"],
                     "icon": ITEMS["witch_blade"]["icon"], "cost": ITEMS["witch_blade"]["cost"],
                     "reason": "Мид-гейм усилитель для INT",
                     "priority": 2})

    if "Support" in my_roles or "Roaming" in my_roles:
        recs.append({"key": "force_staff", "name": ITEMS["force_staff"]["name"],
                     "icon": ITEMS["force_staff"]["icon"], "cost": ITEMS["force_staff"]["cost"],
                     "reason": "Спасение союзников — мастхэв для саппорта",
                     "priority": 4})
        recs.append({"key": "cyclone", "name": ITEMS["cyclone"]["name"],
                     "icon": ITEMS["cyclone"]["icon"], "cost": ITEMS["cyclone"]["cost"],
                     "reason": "Сетап + диспелл себя + мана реген",
                     "priority": 2})
        recs.append({"key": "guardian_greaves", "name": ITEMS["guardian_greaves"]["name"],
                     "icon": ITEMS["guardian_greaves"]["icon"], "cost": ITEMS["guardian_greaves"]["cost"],
                     "reason": "Лучший лейт-айтем саппорта",
                     "priority": 1})
        recs.append({"key": "scythe", "name": ITEMS["scythe"]["name"],
                     "icon": ITEMS["scythe"]["icon"], "cost": ITEMS["scythe"]["cost"],
                     "reason": "Хекс — лучший контроль одного врага",
                     "priority": 1})

    if "Carry" in my_roles and my_attack == "Ranged":
        recs.append({"key": "hurricane_pike", "name": ITEMS["hurricane_pike"]["name"],
                     "icon": ITEMS["hurricane_pike"]["icon"], "cost": ITEMS["hurricane_pike"]["cost"],
                     "reason": "Кайт милишников — мастхэв для рейндж кэрри",
                     "priority": 3})

    if "Offlane" in my_roles:
        recs.append({"key": "vanguard", "name": ITEMS["vanguard"]["name"],
                     "icon": ITEMS["vanguard"]["icon"], "cost": ITEMS["vanguard"]["cost"],
                     "reason": "Ранняя выживаемость на линии",
                     "priority": 3})
        if enemy_physical_carry >= 2:
            recs.append({"key": "crimson_guard", "name": ITEMS["crimson_guard"]["name"],
                         "icon": ITEMS["crimson_guard"]["icon"], "cost": ITEMS["crimson_guard"]["cost"],
                         "reason": "Блок урона для команды против физ. кэрри",
                         "priority": 3})
        recs.append({"key": "radiance", "name": ITEMS["radiance"]["name"],
                     "icon": ITEMS["radiance"]["icon"], "cost": ITEMS["radiance"]["cost"],
                     "reason": "AoE урон + фарм для офлейнера",
                     "priority": 1})

    seen = set()
    unique = []
    for r in sorted(recs, key=lambda x: -x["priority"]):
        if r["key"] not in seen:
            seen.add(r["key"])
            unique.append(r)
    return unique
