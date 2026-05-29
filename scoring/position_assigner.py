"""
Авто-назначение позиций героям в команде.
Если в команде все герои carry — всё равно распределяет по 5 позициям,
выбирая наименее болезненное распределение.
"""
import itertools
from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from data.heroes_static import get_hero_by_id

POSITIONS = ["Carry", "Mid", "Offlane", "Support", "Roaming"]

# Матрица "близости" позиций — насколько роль подходит на позицию,
# даже если она не идеальна. Чем выше число — тем лучше fit.
COMPATIBILITY = {
    # position -> {role: score}
    "Carry":   {"Carry": 10, "Mid": 5,  "Offlane": 4, "Support": 1, "Roaming": 1},
    "Mid":     {"Mid": 10,   "Carry": 5, "Offlane": 4, "Support": 3, "Roaming": 3},
    "Offlane": {"Offlane": 10, "Carry": 4, "Mid": 4,  "Support": 4, "Roaming": 5},
    "Support": {"Support": 10, "Roaming": 7, "Mid": 2, "Offlane": 3, "Carry": 1},
    "Roaming": {"Roaming": 10, "Support": 7, "Offlane": 5, "Mid": 4, "Carry": 2},
}


def fit_score(hero_roles: List[str], position: str) -> int:
    """Насколько герой подходит на позицию (0-10)"""
    if not hero_roles:
        return 1
    pos_compat = COMPATIBILITY.get(position, {})
    return max((pos_compat.get(r, 1) for r in hero_roles), default=1)


def assign_positions(picks: List, all_positions: List[str] = None) -> Dict[str, Optional[dict]]:
    """
    Распределяет пикнутых героев по позициям через перебор.
    
    Args:
        picks: список объектов HeroPick (или dict с hero_id)
    
    Returns:
        {position: {hero_id, name, ...} или None если позиция пуста}
    """
    if all_positions is None:
        all_positions = POSITIONS
    
    result = {p: None for p in all_positions}
    if not picks:
        return result
    
    # Готовим данные
    hero_infos = []
    for pick in picks:
        hero_id = pick.hero_id if hasattr(pick, 'hero_id') else pick['hero_id']
        hero_data = get_hero_by_id(hero_id)
        hero_infos.append({
            'hero_id': hero_id,
            'name': pick.hero_name if hasattr(pick, 'hero_name') else hero_data.get('localized_name', '?'),
            'roles': hero_data.get('roles', []),
        })
    
    n = len(hero_infos)
    if n > len(all_positions):
        n = len(all_positions)
        hero_infos = hero_infos[:n]
    
    # Перебираем все способы выбрать N позиций из 5 и расставить героев
    best_score = -1
    best_assignment = None
    
    for positions_subset in itertools.combinations(all_positions, n):
        for perm in itertools.permutations(positions_subset):
            score = sum(fit_score(hero_infos[i]['roles'], perm[i]) for i in range(n))
            if score > best_score:
                best_score = score
                best_assignment = perm
    
    if best_assignment:
        for i, pos in enumerate(best_assignment):
            result[pos] = hero_infos[i]
    
    return result


def get_empty_positions(picks: List) -> List[str]:
    """Какие позиции ещё не заняты"""
    assignment = assign_positions(picks)
    return [pos for pos, hero in assignment.items() if hero is None]


def get_priority_position(picks: List) -> Optional[str]:
    """
    Самая приоритетная позиция для следующего пика.
    Логика: ядро (Carry/Mid/Offlane) важнее саппортов в начале драфта.
    """
    empty = get_empty_positions(picks)
    if not empty:
        return None
    
    priority = ["Carry", "Mid", "Offlane", "Support", "Roaming"]
    for p in priority:
        if p in empty:
            return p
    return empty[0]
