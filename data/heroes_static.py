"""
Статические данные о героях Dota 2
Источник: OpenDota API / dotaconstants
"""

# Полный список героев (ID, имя, локализованное имя, роли)
# Можно обновить через API: https://api.opendota.com/api/heroes

HEROES = {
    1: {"name": "antimage", "localized_name": "Anti-Mage", "roles": ["Carry"]},
    2: {"name": "axe", "localized_name": "Axe", "roles": ["Offlane"]},
    3: {"name": "bane", "localized_name": "Bane", "roles": ["Support", "Roaming"]},
    4: {"name": "bloodseeker", "localized_name": "Bloodseeker", "roles": ["Carry", "Offlane"]},
    5: {"name": "crystal_maiden", "localized_name": "Crystal Maiden", "roles": ["Support"]},
    6: {"name": "drow_ranger", "localized_name": "Drow Ranger", "roles": ["Carry"]},
    7: {"name": "earthshaker", "localized_name": "Earthshaker", "roles": ["Support", "Roaming"]},
    8: {"name": "juggernaut", "localized_name": "Juggernaut", "roles": ["Carry"]},
    9: {"name": "mirana", "localized_name": "Mirana", "roles": ["Support", "Roaming"]},
    10: {"name": "morphling", "localized_name": "Morphling", "roles": ["Carry"]},
    11: {"name": "nevermore", "localized_name": "Shadow Fiend", "roles": ["Mid", "Carry"]},
    12: {"name": "phantom_lancer", "localized_name": "Phantom Lancer", "roles": ["Carry"]},
    13: {"name": "puck", "localized_name": "Puck", "roles": ["Mid", "Support"]},
    14: {"name": "pudge", "localized_name": "Pudge", "roles": ["Roaming", "Offlane"]},
    15: {"name": "razor", "localized_name": "Razor", "roles": ["Carry", "Offlane"]},
    16: {"name": "sand_king", "localized_name": "Sand King", "roles": ["Offlane", "Roaming"]},
    17: {"name": "storm_spirit", "localized_name": "Storm Spirit", "roles": ["Mid"]},
    18: {"name": "sven", "localized_name": "Sven", "roles": ["Carry"]},
    19: {"name": "tiny", "localized_name": "Tiny", "roles": ["Mid", "Offlane", "Roaming"]},
    20: {"name": "vengefulspirit", "localized_name": "Vengeful Spirit", "roles": ["Support", "Roaming"]},
    21: {"name": "windrunner", "localized_name": "Windranger", "roles": ["Support", "Mid", "Offlane"]},
    22: {"name": "zuus", "localized_name": "Zeus", "roles": ["Mid"]},
    23: {"name": "kunkka", "localized_name": "Kunkka", "roles": ["Mid", "Offlane"]},
    25: {"name": "lina", "localized_name": "Lina", "roles": ["Mid", "Support"]},
    26: {"name": "lion", "localized_name": "Lion", "roles": ["Support"]},
    27: {"name": "shadow_shaman", "localized_name": "Shadow Shaman", "roles": ["Support"]},
    28: {"name": "slardar", "localized_name": "Slardar", "roles": ["Roaming", "Offlane"]},
    29: {"name": "tidehunter", "localized_name": "Tidehunter", "roles": ["Offlane"]},
    30: {"name": "witch_doctor", "localized_name": "Witch Doctor", "roles": ["Support"]},
    31: {"name": "lich", "localized_name": "Lich", "roles": ["Support"]},
    32: {"name": "riki", "localized_name": "Riki", "roles": ["Roaming", "Carry"]},
    33: {"name": "enigma", "localized_name": "Enigma", "roles": ["Offlane"]},
    34: {"name": "tinker", "localized_name": "Tinker", "roles": ["Mid"]},
    35: {"name": "sniper", "localized_name": "Sniper", "roles": ["Mid", "Carry"]},
    36: {"name": "necrolyte", "localized_name": "Necrophos", "roles": ["Mid", "Offlane"]},
    37: {"name": "warlock", "localized_name": "Warlock", "roles": ["Support"]},
    38: {"name": "beastmaster", "localized_name": "Beastmaster", "roles": ["Offlane"]},
    39: {"name": "queenofpain", "localized_name": "Queen of Pain", "roles": ["Mid"]},
    40: {"name": "venomancer", "localized_name": "Venomancer", "roles": ["Support", "Offlane"]},
    41: {"name": "faceless_void", "localized_name": "Faceless Void", "roles": ["Carry"]},
    42: {"name": "skeleton_king", "localized_name": "Wraith King", "roles": ["Carry"]},
    43: {"name": "death_prophet", "localized_name": "Death Prophet", "roles": ["Mid", "Offlane"]},
    44: {"name": "phantom_assassin", "localized_name": "Phantom Assassin", "roles": ["Carry"]},
    45: {"name": "pugna", "localized_name": "Pugna", "roles": ["Mid", "Support"]},
    46: {"name": "templar_assassin", "localized_name": "Templar Assassin", "roles": ["Mid"]},
    47: {"name": "viper", "localized_name": "Viper", "roles": ["Mid", "Offlane"]},
    48: {"name": "luna", "localized_name": "Luna", "roles": ["Carry"]},
    49: {"name": "dragon_knight", "localized_name": "Dragon Knight", "roles": ["Mid", "Offlane"]},
    50: {"name": "dazzle", "localized_name": "Dazzle", "roles": ["Support"]},
    51: {"name": "rattletrap", "localized_name": "Clockwerk", "roles": ["Roaming", "Offlane"]},
    52: {"name": "leshrac", "localized_name": "Leshrac", "roles": ["Mid", "Offlane", "Support"]},
    53: {"name": "furion", "localized_name": "Nature's Prophet", "roles": ["Offlane", "Roaming"]},
    54: {"name": "life_stealer", "localized_name": "Lifestealer", "roles": ["Carry"]},
    55: {"name": "dark_seer", "localized_name": "Dark Seer", "roles": ["Offlane"]},
    56: {"name": "clinkz", "localized_name": "Clinkz", "roles": ["Carry", "Roaming"]},
    57: {"name": "omniknight", "localized_name": "Omniknight", "roles": ["Support"]},
    58: {"name": "enchantress", "localized_name": "Enchantress", "roles": ["Support", "Offlane"]},
    59: {"name": "huskar", "localized_name": "Huskar", "roles": ["Mid", "Carry"]},
    60: {"name": "night_stalker", "localized_name": "Night Stalker", "roles": ["Offlane"]},
    61: {"name": "broodmother", "localized_name": "Broodmother", "roles": ["Mid", "Offlane"]},
    62: {"name": "bounty_hunter", "localized_name": "Bounty Hunter", "roles": ["Roaming"]},
    63: {"name": "weaver", "localized_name": "Weaver", "roles": ["Carry"]},
    64: {"name": "jakiro", "localized_name": "Jakiro", "roles": ["Support"]},
    65: {"name": "batrider", "localized_name": "Batrider", "roles": ["Offlane", "Roaming"]},
    66: {"name": "chen", "localized_name": "Chen", "roles": ["Support"]},
    67: {"name": "spectre", "localized_name": "Spectre", "roles": ["Carry"]},
    68: {"name": "ancient_apparition", "localized_name": "Ancient Apparition", "roles": ["Support"]},
    69: {"name": "doom_bringer", "localized_name": "Doom", "roles": ["Offlane"]},
    70: {"name": "ursa", "localized_name": "Ursa", "roles": ["Carry"]},
    71: {"name": "spirit_breaker", "localized_name": "Spirit Breaker", "roles": ["Roaming"]},
    72: {"name": "gyrocopter", "localized_name": "Gyrocopter", "roles": ["Carry"]},
    73: {"name": "alchemist", "localized_name": "Alchemist", "roles": ["Carry"]},
    74: {"name": "invoker", "localized_name": "Invoker", "roles": ["Mid"]},
    75: {"name": "silencer", "localized_name": "Silencer", "roles": ["Support", "Mid"]},
    76: {"name": "obsidian_destroyer", "localized_name": "Outworld Destroyer", "roles": ["Mid"]},
    77: {"name": "lycan", "localized_name": "Lycan", "roles": ["Carry", "Offlane"]},
    78: {"name": "brewmaster", "localized_name": "Brewmaster", "roles": ["Offlane"]},
    79: {"name": "shadow_demon", "localized_name": "Shadow Demon", "roles": ["Support"]},
    80: {"name": "lone_druid", "localized_name": "Lone Druid", "roles": ["Carry"]},
    81: {"name": "chaos_knight", "localized_name": "Chaos Knight", "roles": ["Carry"]},
    82: {"name": "meepo", "localized_name": "Meepo", "roles": ["Mid", "Carry"]},
    83: {"name": "treant", "localized_name": "Treant Protector", "roles": ["Support"]},
    84: {"name": "ogre_magi", "localized_name": "Ogre Magi", "roles": ["Support", "Roaming"]},
    85: {"name": "undying", "localized_name": "Undying", "roles": ["Support", "Offlane"]},
    86: {"name": "rubick", "localized_name": "Rubick", "roles": ["Support"]},
    87: {"name": "disruptor", "localized_name": "Disruptor", "roles": ["Support"]},
    88: {"name": "nyx_assassin", "localized_name": "Nyx Assassin", "roles": ["Roaming", "Support"]},
    89: {"name": "naga_siren", "localized_name": "Naga Siren", "roles": ["Carry"]},
    90: {"name": "keeper_of_the_light", "localized_name": "Keeper of the Light", "roles": ["Support"]},
    91: {"name": "wisp", "localized_name": "Io", "roles": ["Support"]},
    92: {"name": "visage", "localized_name": "Visage", "roles": ["Roaming", "Support"]},
    93: {"name": "slark", "localized_name": "Slark", "roles": ["Carry"]},
    94: {"name": "medusa", "localized_name": "Medusa", "roles": ["Carry"]},
    95: {"name": "troll_warlord", "localized_name": "Troll Warlord", "roles": ["Carry"]},
    96: {"name": "centaur", "localized_name": "Centaur Warrunner", "roles": ["Offlane"]},
    97: {"name": "magnataur", "localized_name": "Magnus", "roles": ["Offlane", "Roaming"]},
    98: {"name": "shredder", "localized_name": "Timbersaw", "roles": ["Offlane"]},
    99: {"name": "bristleback", "localized_name": "Bristleback", "roles": ["Offlane"]},
    100: {"name": "tusk", "localized_name": "Tusk", "roles": ["Roaming"]},
    101: {"name": "skywrath_mage", "localized_name": "Skywrath Mage", "roles": ["Support", "Roaming"]},
    102: {"name": "abaddon", "localized_name": "Abaddon", "roles": ["Support", "Offlane"]},
    103: {"name": "elder_titan", "localized_name": "Elder Titan", "roles": ["Support", "Roaming"]},
    104: {"name": "legion_commander", "localized_name": "Legion Commander", "roles": ["Offlane"]},
    105: {"name": "techies", "localized_name": "Techies", "roles": ["Support", "Roaming"]},
    106: {"name": "ember_spirit", "localized_name": "Ember Spirit", "roles": ["Mid"]},
    107: {"name": "earth_spirit", "localized_name": "Earth Spirit", "roles": ["Roaming", "Support"]},
    108: {"name": "abyssal_underlord", "localized_name": "Underlord", "roles": ["Offlane"]},
    109: {"name": "terrorblade", "localized_name": "Terrorblade", "roles": ["Carry"]},
    110: {"name": "phoenix", "localized_name": "Phoenix", "roles": ["Support", "Offlane"]},
    111: {"name": "oracle", "localized_name": "Oracle", "roles": ["Support"]},
    112: {"name": "winter_wyvern", "localized_name": "Winter Wyvern", "roles": ["Support"]},
    113: {"name": "arc_warden", "localized_name": "Arc Warden", "roles": ["Mid", "Carry"]},
    114: {"name": "monkey_king", "localized_name": "Monkey King", "roles": ["Carry", "Mid", "Roaming"]},
    119: {"name": "dark_willow", "localized_name": "Dark Willow", "roles": ["Support", "Roaming"]},
    120: {"name": "pangolier", "localized_name": "Pangolier", "roles": ["Offlane", "Mid"]},
    121: {"name": "grimstroke", "localized_name": "Grimstroke", "roles": ["Support"]},
    129: {"name": "mars", "localized_name": "Mars", "roles": ["Offlane"]},
    135: {"name": "dawnbreaker", "localized_name": "Dawnbreaker", "roles": ["Offlane", "Support"]},
    136: {"name": "marci", "localized_name": "Marci", "roles": ["Roaming", "Support"]},
    137: {"name": "primal_beast", "localized_name": "Primal Beast", "roles": ["Offlane", "Mid"]},
    138: {"name": "muerta", "localized_name": "Muerta", "roles": ["Mid", "Carry"]},
}


# Попытка загрузить актуальный список из кэша (после python main.py --update)
# Если файла нет — используем статический HEROES выше
def _load_dynamic_heroes() -> dict:
    try:
        import json
        from pathlib import Path
        cache_file = Path(__file__).parent.parent / "cache" / "heroes_dynamic.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ключи в JSON строковые, конвертируем в int
                return {int(k): v for k, v in data.items()}
    except Exception as e:
        print(f"Не удалось загрузить dynamic heroes: {e}")
    return {}


# Допустимые позиции (не путать с ролями из OpenDota API)
_POSITION_ROLES = {"Carry", "Mid", "Offlane", "Support", "Roaming"}


def _merge_heroes(static: dict, dynamic: dict) -> dict:
    """
    Объединить статический и динамический словари героев.
    Имена берём из dynamic (актуальные), позиции — из static (если есть).
    Для новых героев из API (нет в static) пытаемся угадать позиции
    по ролям OpenDota.
    """
    merged = dict(static)
    for hid, hdata in dynamic.items():
        api_roles = hdata.get("roles", [])
        if hid in static:
            # Герой есть в static — берём его позиции
            merged[hid] = {
                **static[hid],
                "localized_name": hdata.get("localized_name", static[hid].get("localized_name")),
                "name": hdata.get("name", static[hid].get("name")),
            }
        else:
            # Новый герой — маппим роли API на позиции
            positions = _api_roles_to_positions(api_roles)
            merged[hid] = {
                "name": hdata.get("name", ""),
                "localized_name": hdata.get("localized_name", ""),
                "roles": positions or ["Carry"],  # дефолт если ничего не подошло
            }
    return merged


def _api_roles_to_positions(api_roles: list) -> list:
    """
    OpenDota роли: Carry, Support, Nuker, Disabler, Jungler, Durable,
    Escape, Pusher, Initiator.
    Превращаем их в позиции драфта.
    """
    api_set = set(api_roles)
    positions = []
    if "Carry" in api_set:
        positions.append("Carry")
    if "Nuker" in api_set and "Escape" in api_set:
        positions.append("Mid")
    if "Durable" in api_set and ("Initiator" in api_set or "Disabler" in api_set):
        positions.append("Offlane")
    if "Support" in api_set:
        positions.append("Support")
    if "Initiator" in api_set and "Escape" in api_set:
        positions.append("Roaming")
    # Фоллбэки
    if not positions:
        if "Nuker" in api_set:
            positions.append("Mid")
        elif "Durable" in api_set:
            positions.append("Offlane")
    return positions


_dynamic = _load_dynamic_heroes()
if _dynamic:
    HEROES = _merge_heroes(HEROES, _dynamic)


def get_hero_by_id(hero_id: int) -> dict:
    """Получить данные героя по ID"""
    return HEROES.get(hero_id, {"name": "unknown", "localized_name": "Unknown", "roles": []})


def get_hero_by_name(name: str) -> dict:
    """Получить данные героя по названию"""
    for hero_id, hero in HEROES.items():
        if hero["name"] == name or hero["localized_name"].lower() == name.lower():
            return {"id": hero_id, **hero}
    return None


def get_all_heroes() -> dict:
    """Получить всех героев"""
    return HEROES


def search_hero(query: str) -> list:
    """Поиск героя по части имени"""
    query = query.lower()
    results = []
    for hero_id, hero in HEROES.items():
        if query in hero["name"].lower() or query in hero["localized_name"].lower():
            results.append({"id": hero_id, **hero})
    return results
