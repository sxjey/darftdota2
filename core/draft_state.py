"""
Управление состоянием драфта
Хранит текущие пики, баны, фазу драфта
"""
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class DraftPhase(Enum):
    """Фазы драфта"""
    NOT_STARTED = "not_started"
    BAN_PHASE_1 = "ban_phase_1"
    PICK_PHASE_1 = "pick_phase_1"
    BAN_PHASE_2 = "ban_phase_2"
    PICK_PHASE_2 = "pick_phase_2"
    COMPLETE = "complete"


@dataclass
class HeroPick:
    """Информация о пике"""
    hero_id: int
    hero_name: str
    is_ally: bool  # True - наша команда, False - враги
    order: int     # Порядковый номер пика (1-10)


@dataclass  
class DraftState:
    """
    Текущее состояние драфта
    """
    phase: DraftPhase = DraftPhase.NOT_STARTED
    
    # Пики
    ally_picks: List[HeroPick] = field(default_factory=list)
    enemy_picks: List[HeroPick] = field(default_factory=list)
    
    # Баны
    ally_bans: List[int] = field(default_factory=list)  # hero_ids
    enemy_bans: List[int] = field(default_factory=list)
    
    # Метаданные
    game_mode: str = ""  # all_pick, captains_mode, etc.
    is_radiant: bool = True  # Мы играем за Radiant (слева) или Dire (справа)

    # Ручное указание роли для союзников (hero_id -> позиция)
    # Если задано — assign_positions зафиксирует героя на этой позиции
    ally_position_overrides: Dict[int, str] = field(default_factory=dict)

    # Undo история: список снимков состояния
    _undo_stack: List[dict] = field(default_factory=list)
    _undo_max: int = 30

    def _snapshot(self) -> dict:
        return {
            "ally_picks": [(p.hero_id, p.hero_name) for p in self.ally_picks],
            "enemy_picks": [(p.hero_id, p.hero_name) for p in self.enemy_picks],
            "ally_bans": list(self.ally_bans),
            "enemy_bans": list(self.enemy_bans),
            "overrides": dict(self.ally_position_overrides),
        }

    def _restore(self, snap: dict):
        self.ally_picks = [
            HeroPick(hero_id=hid, hero_name=name, is_ally=True, order=i + 1)
            for i, (hid, name) in enumerate(snap["ally_picks"])
        ]
        self.enemy_picks = [
            HeroPick(hero_id=hid, hero_name=name, is_ally=False, order=i + 1)
            for i, (hid, name) in enumerate(snap["enemy_picks"])
        ]
        self.ally_bans = list(snap.get("ally_bans", []))
        self.enemy_bans = list(snap.get("enemy_bans", []))
        self.ally_position_overrides = dict(snap.get("overrides", {}))

    def push_undo(self):
        self._undo_stack.append(self._snapshot())
        if len(self._undo_stack) > self._undo_max:
            self._undo_stack.pop(0)

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        snap = self._undo_stack.pop()
        self._restore(snap)
        return True
    
    def add_ally_pick(self, hero_id: int, hero_name: str) -> HeroPick:
        """Добавить пик союзника"""
        pick = HeroPick(
            hero_id=hero_id,
            hero_name=hero_name,
            is_ally=True,
            order=len(self.ally_picks) + len(self.enemy_picks) + 1
        )
        self.ally_picks.append(pick)
        return pick
    
    def add_enemy_pick(self, hero_id: int, hero_name: str) -> HeroPick:
        """Добавить пик врага"""
        pick = HeroPick(
            hero_id=hero_id,
            hero_name=hero_name,
            is_ally=False,
            order=len(self.ally_picks) + len(self.enemy_picks) + 1
        )
        self.enemy_picks.append(pick)
        return pick
    
    def add_ally_ban(self, hero_id: int):
        if hero_id not in self.ally_bans:
            self.ally_bans.append(hero_id)
    
    def add_enemy_ban(self, hero_id: int):
        if hero_id not in self.enemy_bans:
            self.enemy_bans.append(hero_id)

    def remove_ally_ban(self, hero_id: int):
        self.ally_bans = [b for b in self.ally_bans if b != hero_id]

    def remove_enemy_ban(self, hero_id: int):
        self.enemy_bans = [b for b in self.enemy_bans if b != hero_id]
    
    def set_position_override(self, hero_id: int, position: Optional[str]):
        """Задать вручную позицию для героя союзника (или сбросить если None)"""
        if position is None:
            self.ally_position_overrides.pop(hero_id, None)
        else:
            self.ally_position_overrides[hero_id] = position

    def remove_ally_pick(self, hero_id: int):
        """Удалить пик союзника по ID"""
        self.ally_picks = [p for p in self.ally_picks if p.hero_id != hero_id]
        self.ally_position_overrides.pop(hero_id, None)
        self._reorder()
    
    def remove_enemy_pick(self, hero_id: int):
        """Удалить пик врага по ID"""
        self.enemy_picks = [p for p in self.enemy_picks if p.hero_id != hero_id]
        self._reorder()
    
    def _reorder(self):
        """Пересчитать порядковые номера пиков"""
        order = 1
        for p in self.ally_picks:
            p.order = order
            order += 1
        for p in self.enemy_picks:
            p.order = order
            order += 1
    
    def get_all_picked_heroes(self) -> Set[int]:
        """Все выбранные герои (ID)"""
        picked = set()
        for pick in self.ally_picks + self.enemy_picks:
            picked.add(pick.hero_id)
        return picked
    
    def get_all_banned_heroes(self) -> Set[int]:
        """Все забаненные герои (ID)"""
        return set(self.ally_bans + self.enemy_bans)
    
    def get_available_heroes(self, all_hero_ids: List[int]) -> List[int]:
        """Получить доступных для выбора героев"""
        picked = self.get_all_picked_heroes()
        banned = self.get_all_banned_heroes()
        return [h for h in all_hero_ids if h not in picked and h not in banned]
    
    def get_ally_roles(self) -> Dict[str, int]:
        """Получить распределение ролей в нашей команде"""
        from data.heroes_static import get_hero_by_id
        roles = {}
        for pick in self.ally_picks:
            hero = get_hero_by_id(pick.hero_id)
            for role in hero.get("roles", []):
                roles[role] = roles.get(role, 0) + 1
        return roles
    
    def is_complete(self) -> bool:
        """Драфт завершён (10 пиков)"""
        return len(self.ally_picks) + len(self.enemy_picks) >= 10
    
    def get_current_turn(self) -> Optional[str]:
        """
        Чья сейчас очередь
        Returns: 'ally' или 'enemy' или None если драфт завершён
        """
        if self.is_complete():
            return None
        
        total_picks = len(self.ally_picks) + len(self.enemy_picks)
        
        # В All Pick: Radiant 1,3,5,7,9; Dire 2,4,6,8,10
        # Если мы Radiant - нечётные наши, чётные враги
        if self.is_radiant:
            return 'ally' if total_picks % 2 == 0 else 'enemy'
        else:
            return 'enemy' if total_picks % 2 == 0 else 'ally'
    
    def reset(self):
        self.phase = DraftPhase.NOT_STARTED
        self.ally_picks = []
        self.enemy_picks = []
        self.ally_bans = []
        self.enemy_bans = []
        self.game_mode = ""
        self.ally_position_overrides = {}
        self._undo_stack = []
    
    def to_dict(self) -> dict:
        return {
            "phase": self.phase.value,
            "ally_picks": [
                {"hero_id": p.hero_id, "name": p.hero_name, "order": p.order}
                for p in self.ally_picks
            ],
            "enemy_picks": [
                {"hero_id": p.hero_id, "name": p.hero_name, "order": p.order}
                for p in self.enemy_picks
            ],
            "ally_bans": self.ally_bans,
            "enemy_bans": self.enemy_bans,
            "is_radiant": self.is_radiant,
            "ally_position_overrides": self.ally_position_overrides,
        }
    
    def __str__(self) -> str:
        """Строковое представление"""
        lines = [f"=== Драфт ({self.phase.value}) ==="]
        lines.append(f"Мы играем за: {'Radiant' if self.is_radiant else 'Dire'}")
        lines.append(f"Очередь: {self.get_current_turn() or 'завершено'}")
        lines.append("")
        lines.append("Наша команда:")
        for p in self.ally_picks:
            lines.append(f"  {p.order}. {p.hero_name}")
        lines.append("")
        lines.append("Враги:")
        for p in self.enemy_picks:
            lines.append(f"  {p.order}. {p.hero_name}")
        return "\n".join(lines)


# Глобальное состояние (singleton)
_draft_state = DraftState()


def get_draft_state() -> DraftState:
    """Получить текущее состояние драфта"""
    return _draft_state


def reset_draft():
    """Сбросить драфт"""
    _draft_state.reset()
