"""
Клиент для OpenDota API
Документация: https://docs.opendota.com/
"""
import requests
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

# Импортируем настройки
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    OPENDOTA_API, 
    CACHE_DIR, 
    MATCHUP_DATA_FILE, 
    WINRATES_FILE,
    REQUEST_DELAY
)


class OpenDotaClient:
    """
    Клиент для работы с OpenDota API
    С кэшированием для избежания rate limits
    """
    
    def __init__(self):
        self.base_url = OPENDOTA_API
        self.cache_dir = Path(CACHE_DIR)
        self.cache_dir.mkdir(exist_ok=True)
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Задержка между запросами"""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, endpoint: str) -> Path:
        """Путь к файлу кэша для endpoint"""
        cache_name = endpoint.replace("/", "_") + ".json"
        return self.cache_dir / cache_name
    
    def _load_from_cache(self, endpoint: str, max_age_hours: int = 24) -> Optional[dict]:
        """Загрузить данные из кэша если они свежие"""
        cache_path = self._get_cache_path(endpoint)
        if not cache_path.exists():
            return None
        
        # Проверяем возраст файла
        file_age = time.time() - cache_path.stat().st_mtime
        if file_age > max_age_hours * 3600:
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def _save_to_cache(self, endpoint: str, data: dict):
        """Сохранить данные в кэш"""
        cache_path = self._get_cache_path(endpoint)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения кэша: {e}")
    
    def get(self, endpoint: str, use_cache: bool = True, **params) -> dict:
        """
        Выполнить GET запрос с кэшированием
        
        Args:
            endpoint: API endpoint (например '/heroes')
            use_cache: Использовать кэш
            **params: Query параметры
        """
        # Проверяем кэш
        if use_cache:
            cached = self._load_from_cache(endpoint)
            if cached is not None:
                return cached
        
        # Rate limiting
        self._rate_limit()
        
        # Выполняем запрос
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Сохраняем в кэш
            if use_cache:
                self._save_to_cache(endpoint, data)
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса к {url}: {e}")
            # Пытаемся загрузить из кэша даже если он устарел
            cached = self._load_from_cache(endpoint, max_age_hours=999999)
            if cached:
                print("Используются устаревшие данные из кэша")
                return cached
            raise
    
    def get_heroes(self) -> List[Dict]:
        """Получить список всех героев"""
        return self.get("/heroes")
    
    def get_hero_matchups(self, hero_id: int) -> List[Dict]:
        """
        Получить контрпики для героя
        Возвращает список: [{hero_id, wins, games_played}, ...]
        """
        endpoint = f"/heroes/{hero_id}/matchups"
        return self.get(endpoint)
    
    def get_hero_winrates(self) -> Dict[int, float]:
        """
        Получить винрейты всех героев (про-сцена)
        Возвращает: {hero_id: winrate_percent}
        """
        heroes = self.get_heroes()
        winrates = {}
        
        for hero in heroes:
            hero_id = hero.get("id")
            pro_pick = hero.get("pro_pick", 0)
            pro_win = hero.get("pro_win", 0)
            
            if pro_pick > 0:
                winrate = (pro_win / pro_pick) * 100
                winrates[hero_id] = round(winrate, 2)
            else:
                winrates[hero_id] = 50.0  # Дефолт
        
        return winrates
    
    def get_hero_stats_by_rank(self) -> Dict[int, Dict[str, float]]:
        """
        Получить винрейты всех героев по рангам (брэкетам).
        Источник: GET /heroStats
        
        Returns:
            {hero_id: {"herald": 52.1, "guardian": 51.8, ..., "pub": 50.5, "pro": 48.2}}
        """
        stats_raw = self.get("/heroStats")
        
        brackets = ["herald", "guardian", "crusader", "archon",
                    "legend", "ancient", "divine", "immortal", "pub", "pro"]
        
        result = {}
        for hero in stats_raw:
            hero_id = hero.get("id")
            bracket_winrates = {}
            for br in brackets:
                pick = hero.get(f"{br}_pick", 0) or 0
                win = hero.get(f"{br}_win", 0) or 0
                if pick > 0:
                    bracket_winrates[br] = round((win / pick) * 100, 2)
                else:
                    bracket_winrates[br] = 50.0
            result[hero_id] = bracket_winrates
        
        return result
    
    def get_all_matchups(self) -> Dict[int, List[Dict]]:
        """
        Получить контрпики для всех героев
        Осторожно: много запросов! (100+ героев)
        
        Returns:
            {hero_id: [{hero_id, wins, games_played}, ...]}
        """
        print("Загрузка контрпиков для всех героев...")
        print("Это займет 2-3 минуты из-за rate limiting API")
        
        heroes = self.get_heroes()
        all_matchups = {}
        
        for hero in heroes:
            hero_id = hero["id"]
            try:
                matchups = self.get_hero_matchups(hero_id)
                all_matchups[hero_id] = matchups
                print(f"  ✓ {hero.get('localized_name', hero_id)}")
            except Exception as e:
                print(f"  ✗ {hero.get('localized_name', hero_id)}: {e}")
                all_matchups[hero_id] = []
        
        # Сохраняем общий кэш
        with open(MATCHUP_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_matchups, f, ensure_ascii=False, indent=2)
        
        return all_matchups
    
    def load_cached_matchups(self) -> Dict[int, List[Dict]]:
        """Загрузить контрпики из кэша"""
        if MATCHUP_DATA_FILE.exists():
            with open(MATCHUP_DATA_FILE, 'r', encoding='utf-8') as f:
                # Ключи в JSON строковые, конвертируем в int
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        return {}


# Утилита для обновления данных
def update_all_data():
    """Обновить все данные из API"""
    client = OpenDotaClient()
    
    print("=" * 50)
    print("Обновление данных из OpenDota API")
    print("=" * 50)
    
    # Сохраняем актуальный список героев (с новыми типа Kez, Ringmaster)
    print("\n0. Загрузка актуального списка героев...")
    heroes_list = client.get_heroes()
    heroes_dict = {}
    for h in heroes_list:
        heroes_dict[h["id"]] = {
            "name": h.get("name", "").replace("npc_dota_hero_", ""),
            "localized_name": h.get("localized_name", ""),
            "roles": h.get("roles", []),
        }
    
    from config.settings import CACHE_DIR as _CACHE
    heroes_dynamic_file = _CACHE / "heroes_dynamic.json"
    with open(heroes_dynamic_file, 'w', encoding='utf-8') as f:
        json.dump(heroes_dict, f, ensure_ascii=False, indent=2)
    print(f"   Сохранено {len(heroes_dict)} героев (включая новых)")
    
    # Винрейты (общие, pro-сцена)
    print("\n1. Загрузка винрейтов...")
    winrates = client.get_hero_winrates()
    with open(WINRATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(winrates, f, indent=2)
    print(f"   Сохранено {len(winrates)} записей")
    
    # Винрейты по рангам
    print("\n1b. Загрузка винрейтов по рангам (Herald → Immortal)...")
    bracket_stats = client.get_hero_stats_by_rank()
    bracket_file = _CACHE / "winrates_by_rank.json"
    with open(bracket_file, 'w', encoding='utf-8') as f:
        json.dump(bracket_stats, f, indent=2)
    print(f"   Сохранено {len(bracket_stats)} героев x 10 брэкетов")
    
    # Контрпики
    print("\n2. Загрузка контрпиков...")
    matchups = client.get_all_matchups()
    print(f"   Сохранено {len(matchups)} героев")
    
    print("\n✓ Обновление завершено!")
    print(f"Данные сохранены в: {CACHE_DIR}")


if __name__ == "__main__":
    # Тест клиента
    client = OpenDotaClient()
    
    print("Тест OpenDota Client")
    print("-" * 30)
    
    # Получить список героев
    heroes = client.get_heroes()
    print(f"Всего героев: {len(heroes)}")
    print(f"Первый герой: {heroes[0] if heroes else 'N/A'}")
    
    # Получить контрпики для Anti-Mage (ID=1)
    print("\nКонтрпики для Anti-Mage:")
    matchups = client.get_hero_matchups(1)
    for m in matchups[:5]:
        hero_id = m.get('hero_id')
        winrate = (m.get('wins', 0) / m.get('games_played', 1)) * 100
        print(f"  vs Hero {hero_id}: {winrate:.1f}% winrate")
