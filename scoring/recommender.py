"""
Скоринг-модель для рекомендации героев
Весовая формула: база + контрпики + синергия - роли + мета
"""
import json
import sys
import itertools
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))
from data.heroes_static import get_all_heroes, get_hero_by_id
from data.opendota_client import OpenDotaClient
from config.settings import SCORING_WEIGHTS, WINRATES_FILE, MATCHUP_DATA_FILE
from core.draft_state import DraftState


@dataclass
class HeroScore:
    """Результат скоринга героя"""
    hero_id: int
    hero_name: str
    roles: List[str]
    total_score: float
    base_winrate: float
    counter_bonus: float
    synergy_bonus: float
    role_penalty: float
    meta_score: float
    explanation: str


# Описание брэкетов (рангов) для UI
BRACKETS = [
    ("pub",      "Все паблики",      "0–12000+ MMR (среднее)"),
    ("herald",   "Herald",           "0–770 MMR"),
    ("guardian", "Guardian",         "770–1540 MMR"),
    ("crusader", "Crusader",         "1540–2310 MMR"),
    ("archon",   "Archon",           "2310–3080 MMR"),
    ("legend",   "Legend",           "3080–3850 MMR"),
    ("ancient",  "Ancient",          "3850–4620 MMR"),
    ("divine",   "Divine",           "4620–5420 MMR"),
    ("immortal", "Immortal",         "5420+ MMR"),
    ("pro",      "Pro-сцена",        "профессионалы"),
]


class HeroRecommender:
    """
    Рекомендатор героев на основе весовой формулы
    """
    
    def __init__(self, bracket: str = "pub"):
        self.winrates: Dict[int, float] = {}
        self.bracket_winrates: Dict[int, Dict[str, float]] = {}
        self.matchups: Dict[int, List[Dict]] = {}
        self.weights = SCORING_WEIGHTS
        self.current_bracket = bracket  # текущий выбранный ранг
        self._load_data()
    
    def set_bracket(self, bracket: str):
        """Сменить ранг для расчёта"""
        self.current_bracket = bracket
    
    def _get_winrate(self, hero_id: int) -> float:
        """Винрейт героя для текущего брэкета"""
        if self.bracket_winrates and hero_id in self.bracket_winrates:
            wr = self.bracket_winrates[hero_id].get(self.current_bracket)
            if wr is not None:
                return wr
        # Фоллбэк на старые данные
        return self.winrates.get(hero_id, 50.0)
    
    def _load_data(self):
        """Загрузить данные о винрейтах и контрпиках"""
        # Винрейты по рангам (новый формат)
        bracket_file = WINRATES_FILE.parent / "winrates_by_rank.json"
        if bracket_file.exists():
            with open(bracket_file, 'r') as f:
                self.bracket_winrates = {
                    int(k): v for k, v in json.load(f).items()
                }
        
        # Старые винрейты (фоллбэк)
        if WINRATES_FILE.exists():
            with open(WINRATES_FILE, 'r') as f:
                self.winrates = {int(k): v for k, v in json.load(f).items()}
        else:
            heroes = get_all_heroes()
            self.winrates = {hid: 50.0 for hid in heroes.keys()}
        
        # Контрпики (общие для всех рангов — OpenDota не разделяет)
        if MATCHUP_DATA_FILE.exists():
            with open(MATCHUP_DATA_FILE, 'r') as f:
                data = json.load(f)
                self.matchups = {int(k): v for k, v in data.items()}
    
    def get_counter_score(self, hero_id: int, enemy_picks: List[int]) -> float:
        """
        Рассчитать бонус за контрпики врагов
        
        Args:
            hero_id: ID героя которого оцениваем
            enemy_picks: ID героев врагов
        
        Returns:
            Суммарный бонус (0-100)
        """
        if hero_id not in self.matchups:
            return 0.0
        
        bonus = 0.0
        matchups = self.matchups[hero_id]
        
        # Создаём словарь: hero_id -> winrate против него
        matchup_dict = {}
        for m in matchups:
            enemy_id = m.get('hero_id')
            wins = m.get('wins', 0)
            games = m.get('games_played', 1)
            if games > 0:
                matchup_dict[enemy_id] = (wins / games) * 100
        
        # Суммируем бонусы за каждого врага
        for enemy_id in enemy_picks:
            if enemy_id in matchup_dict:
                winrate_vs = matchup_dict[enemy_id]
                # Бонус если у нас хороший винрейт против этого героя (>50%)
                if winrate_vs > 50:
                    bonus += (winrate_vs - 50) * 2  # Сильный контрпик
                elif winrate_vs < 45:
                    bonus -= (45 - winrate_vs) * 2  # Антиконтрпик
        
        return bonus
    
    def get_synergy_score(self, hero_id: int, ally_picks: List[int]) -> float:
        """
        Рассчитать бонус за синергию с союзниками
        
        Простая модель: комбо хорошо работающие вместе
        Можно расширить таблицей синергий
        
        Args:
            hero_id: ID героя
            ally_picks: ID союзников
        
        Returns:
            Бонус синергии
        """
        bonus = 0.0
        hero = get_hero_by_id(hero_id)
        hero_roles = set(hero.get("roles", []))
        
        # Проверяем комбо
        synergy_pairs = self._get_synergy_pairs()
        
        for ally_id in ally_picks:
            pair = tuple(sorted([hero_id, ally_id]))
            if pair in synergy_pairs:
                bonus += synergy_pairs[pair]
        
        # Бонус за разнообразие ролей (не дублируем роли)
        for ally_id in ally_picks:
            ally = get_hero_by_id(ally_id)
            ally_roles = set(ally.get("roles", []))
            
            # Если есть общие роли - пенальти
            overlap = hero_roles & ally_roles
            if overlap:
                bonus -= 5 * len(overlap)  # -5 за каждую дублирующую роль
            else:
                bonus += 3  # Бонус за разнообразие
        
        return bonus
    
    def _get_synergy_pairs(self) -> Dict[Tuple[int, int], float]:
        """
        Таблица известных синергий
        Можно расширять по мере изучения
        """
        # Примеры синергий (hero_id_a, hero_id_b) -> бонус
        # ID: Magnus=97, Enigma=33, Tidehunter=29 - хорошие комбо с wombo
        # ID: Crystal Maiden=5 - мана реген для всех
        return {
            # Magnus + мили герои
            (97, 18): 15,   # Magnus + Sven
            (97, 81): 15,   # Magnus + Chaos Knight
            (97, 42): 10,   # Magnus + Wraith King
            
            # Enigma + массовые ульты
            (33, 97): 10,   # Enigma + Magnus
            (33, 29): 10,   # Enigma + Tide
            
            # Dark Willow + входы
            (119, 28): 8,   # DW + Slardar
            (119, 51): 8,   # DW + Clockwerk
            
            # Dazzle + физ урон
            (50, 18): 8,    # Dazzle + Sven
            (50, 81): 8,    # Dazzle + CK
            
            # CM + мана зависимые
            (5, 17): 10,    # CM + Storm Spirit
            (5, 74): 10,    # CM + Invoker
            (5, 106): 8,    # CM + Ember Spirit
        }
    
    def get_role_penalty(self, hero_id: int, ally_roles: Dict[str, int]) -> float:
        """
        Пенальти за перенасыщение роли
        
        Args:
            hero_id: ID героя
            ally_roles: {role: count} - текущее распределение ролей
        
        Returns:
            Пенальти (отрицательное число)
        """
        hero = get_hero_by_id(hero_id)
        hero_roles = hero.get("roles", [])
        
        penalty = 0.0
        
        for role in hero_roles:
            count = ally_roles.get(role, 0)
            if count >= 2:
                penalty -= 10  # Уже 2+ этой роли - сильный пенальти
            elif count == 1:
                penalty -= 3   # Уже 1 - небольшой пенальти
        
        return penalty
    
    def get_meta_score(self, hero_id: int) -> float:
        """
        Метрика меты (текущий патч)
        
        Returns:
            Множитель меты (0-20)
        """
        # Базируем на винрейте в выбранном ранге
        winrate = self._get_winrate(hero_id)
        
        # Если винрейт > 52% - герой в мете
        if winrate > 52:
            return (winrate - 50) * 5  # До +10 за метовость
        elif winrate < 48:
            return (winrate - 50) * 3  # Штраф за неметовость
        
        return 0.0
    
    def score_hero(self, hero_id: int, draft_state: DraftState) -> HeroScore:
        """
        Рассчитать полный скор для героя
        
        Формула:
        total = base * w_base + counter * w_counter + synergy * w_synergy + role * w_role + meta * w_meta
        """
        hero = get_hero_by_id(hero_id)
        
        # 1. Базовый винрейт (по выбранному рангу)
        base_winrate = self._get_winrate(hero_id)
        
        # 2. Контрпики врагов
        enemy_ids = [p.hero_id for p in draft_state.enemy_picks]
        counter_bonus = self.get_counter_score(hero_id, enemy_ids)
        
        # 3. Синергия с союзниками
        ally_ids = [p.hero_id for p in draft_state.ally_picks]
        synergy_bonus = self.get_synergy_score(hero_id, ally_ids)
        
        # 4. Пенальти ролей
        current_roles = draft_state.get_ally_roles()
        role_penalty = self.get_role_penalty(hero_id, current_roles)
        
        # 5. Мета
        meta_score = self.get_meta_score(hero_id)
        
        # Применяем веса
        w = self.weights
        total = (
            base_winrate * w["base_winrate"] +
            counter_bonus * w["counter_bonus"] +
            synergy_bonus * w["synergy_bonus"] +
            role_penalty * w["role_penalty"] +
            meta_score * w["meta_multiplier"]
        )
        
        # Создаём объяснение
        parts = []
        if counter_bonus > 5:
            parts.append(f"сильный контрпик (+{counter_bonus:.0f})")
        elif counter_bonus < -5:
            parts.append(f"контрится ({counter_bonus:.0f})")
        
        if synergy_bonus > 5:
            parts.append(f"хорошая синергия (+{synergy_bonus:.0f})")
        
        if role_penalty < -5:
            parts.append(f"перебор ролей ({role_penalty:.0f})")
        
        if meta_score > 5:
            parts.append(f"в мете (+{meta_score:.0f})")
        
        explanation = ", ".join(parts) if parts else "сбалансированный пик"
        
        return HeroScore(
            hero_id=hero_id,
            hero_name=hero["localized_name"],
            roles=hero.get("roles", []),
            total_score=round(total, 1),
            base_winrate=round(base_winrate, 1),
            counter_bonus=round(counter_bonus, 1),
            synergy_bonus=round(synergy_bonus, 1),
            role_penalty=round(role_penalty, 1),
            meta_score=round(meta_score, 1),
            explanation=explanation
        )
    
    def get_recommendations(self, draft_state: DraftState, 
                          top_n: int = 5) -> List[HeroScore]:
        """
        Получить топ-N рекомендаций для текущего драфта
        
        Args:
            draft_state: Текущее состояние
            top_n: Сколько рекомендаций вернуть
        
        Returns:
            Список HeroScore отсортированный по убыванию
        """
        # Получаем доступных героев
        all_heroes = list(get_all_heroes().keys())
        available = draft_state.get_available_heroes(all_heroes)
        
        # Скорим каждого
        scores = []
        for hero_id in available:
            score = self.score_hero(hero_id, draft_state)
            scores.append(score)
        
        # Сортируем по убыванию скора
        scores.sort(key=lambda x: x.total_score, reverse=True)
        
        return scores[:top_n]
    
    def get_recommendations_by_role(self, draft_state: DraftState,
                                    top_per_role: int = 3) -> Dict[str, List[HeroScore]]:
        """
        Лучшие герои для каждой роли отдельно.
        Возвращает: {role: [HeroScore top1, top2, top3]}
        """
        roles = ["Carry", "Mid", "Offlane", "Support", "Roaming"]
        
        # Скорим всех доступных
        all_heroes = list(get_all_heroes().keys())
        available = draft_state.get_available_heroes(all_heroes)
        
        scored = [self.score_hero(hid, draft_state) for hid in available]
        
        result = {}
        for role in roles:
            # Фильтруем героев подходящих на эту роль
            role_heroes = [s for s in scored if role in s.roles]
            role_heroes.sort(key=lambda x: x.total_score, reverse=True)
            result[role] = role_heroes[:top_per_role]
        
        return result
    
    def update_weights(self, new_weights: Dict[str, float]):
        """Обновить веса скоринга"""
        self.weights.update(new_weights)
    
    def analyze_matchup(self, draft_state: DraftState) -> Dict:
        """
        Анализ обеих команд при полном драфте (5v5).
        Считает скоры каждого героя и общий перевес.
        
        Returns:
            {
                "ally_scores":  [HeroScore, ...] (5 шт),
                "enemy_scores": [HeroScore, ...] (5 шт),
                "ally_total": float,
                "enemy_total": float,
                "diff": float,                  # ally - enemy
                "advantage_pct": float,         # -100..+100, > 0 = наша команда сильнее
                "winner": "ally"|"enemy"|"draw",
                "verdict": str,                 # текстовый вердикт
                "key_factors": List[str],       # ключевые факторы
            }
        """
        # Скорим союзников из их перспективы
        ally_scores = [self.score_hero(p.hero_id, draft_state)
                       for p in draft_state.ally_picks]
        
        # Для врагов меняем перспективу: они становятся "союзниками"
        # тогда их контрпики/синергии считаются правильно
        swapped = DraftState()
        swapped.ally_picks = list(draft_state.enemy_picks)
        swapped.enemy_picks = list(draft_state.ally_picks)
        swapped.ally_bans = list(draft_state.enemy_bans)
        swapped.enemy_bans = list(draft_state.ally_bans)
        
        enemy_scores = [self.score_hero(p.hero_id, swapped)
                        for p in draft_state.enemy_picks]
        
        ally_total = sum(s.total_score for s in ally_scores)
        enemy_total = sum(s.total_score for s in enemy_scores)
        diff = ally_total - enemy_total
        
        # Преимущество в процентах (от среднего скора)
        avg = max((abs(ally_total) + abs(enemy_total)) / 2, 1)
        advantage_pct = max(-100.0, min(100.0, (diff / avg) * 100))
        
        # Вердикт
        if diff > 30:
            winner = "ally"
            verdict = "🏆 Большое преимущество твоей команды"
        elif diff > 10:
            winner = "ally"
            verdict = "✅ Лёгкий перевес у твоей команды"
        elif diff < -30:
            winner = "enemy"
            verdict = "⚠️ Большое преимущество врагов"
        elif diff < -10:
            winner = "enemy"
            verdict = "🟠 Лёгкий перевес у врагов"
        else:
            winner = "draw"
            verdict = "⚖️ Равный матчап — решит скилл"
        
        # Ключевые факторы
        factors = []
        # Сильнейший герой каждой команды
        if ally_scores:
            best_ally = max(ally_scores, key=lambda s: s.total_score)
            factors.append(f"Лучший в твоей команде: {best_ally.hero_name} ({best_ally.total_score:.0f})")
        if enemy_scores:
            best_enemy = max(enemy_scores, key=lambda s: s.total_score)
            factors.append(f"Опасный у врагов: {best_enemy.hero_name} ({best_enemy.total_score:.0f})")
        
        # Слабое звено своей команды
        if ally_scores:
            worst_ally = min(ally_scores, key=lambda s: s.total_score)
            if worst_ally.total_score < 50:
                factors.append(f"Слабое звено у тебя: {worst_ally.hero_name} ({worst_ally.total_score:.0f})")
        
        return {
            "ally_scores": ally_scores,
            "enemy_scores": enemy_scores,
            "ally_total": round(ally_total, 1),
            "enemy_total": round(enemy_total, 1),
            "diff": round(diff, 1),
            "advantage_pct": round(advantage_pct, 1),
            "winner": winner,
            "verdict": verdict,
            "key_factors": factors,
        }
    
    def explain_pick(self, hero_id: int, draft_state: DraftState) -> str:
        """Подробное объяснение рекомендации"""
        score = self.score_hero(hero_id, draft_state)
        
        lines = [
            f"=== Анализ: {score.hero_name} ===",
            f"Роли: {', '.join(score.roles)}",
            f"",
            f"Итоговый скор: {score.total_score:.1f}",
            f"",
            f"Разбор:",
            f"  Базовый винрейт: {score.base_winrate}%",
            f"  Бонус контрпиков: {score.counter_bonus:+.1f}",
            f"  Бонус синергии: {score.synergy_bonus:+.1f}",
            f"  Пенальти ролей: {score.role_penalty:+.1f}",
            f"  Мета: {score.meta_score:+.1f}",
            f"",
            f"Вывод: {score.explanation}",
        ]
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Тест рекомендатора
    print("Тест HeroRecommender")
    print("="*50)
    
    recommender = HeroRecommender()
    
    # Создаём тестовый драфт
    from core.draft_state import DraftState, get_draft_state, DraftPhase
    
    state = get_draft_state()
    state.reset()
    state.phase = DraftPhase.PICK_PHASE_1
    state.is_radiant = True
    
    # Добавляем тестовых врагов
    state.add_enemy_pick(1, "Anti-Mage")      # AM
    state.add_enemy_pick(14, "Pudge")         # Pudge
    
    # И одного союзника
    state.add_ally_pick(5, "Crystal Maiden")  # CM
    
    print(f"\nТекущий драфт:")
    print(f"  Союзники: {[p.hero_name for p in state.ally_picks]}")
    print(f"  Враги: {[p.hero_name for p in state.enemy_picks]}")
    
    # Получаем рекомендации
    print(f"\n{'='*50}")
    print("ТОП-5 РЕКОМЕНДАЦИЙ:")
    print("="*50)
    
    recommendations = recommender.get_recommendations(state, top_n=5)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec.hero_name} (скор: {rec.total_score:.1f})")
        print(f"   Роли: {', '.join(rec.roles)}")
        print(f"   Почему: {rec.explanation}")
    
    # Детальный разбор первого
    if recommendations:
        print(f"\n{'='*50}")
        print(recommender.explain_pick(recommendations[0].hero_id, state))
