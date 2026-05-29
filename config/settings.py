"""
Настройки Draft Assistant
"""
import os
from pathlib import Path

# Пути
BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "cache"
ASSETS_DIR = BASE_DIR / "assets"
HERO_ICONS_DIR = ASSETS_DIR / "hero_icons"

# Создаём папки если нет
CACHE_DIR.mkdir(parents=True, exist_ok=True)
HERO_ICONS_DIR.mkdir(parents=True, exist_ok=True)

# API endpoints
OPENDOTA_API = "https://api.opendota.com/api"
STRATZ_API = "https://api.stratz.com/graphql"

# Пути к данным
HERO_DATA_FILE = CACHE_DIR / "heroes.json"
MATCHUP_DATA_FILE = CACHE_DIR / "matchups.json"
WINRATES_FILE = CACHE_DIR / "winrates.json"

# Настройки OCR и детекции
# Координаты для разрешения 1920x1080 (Full HD)
# Эти ROI (Region of Interest) нужно настроить под твой интерфейс Dota 2
SCREENSHOT_REGIONS = {
    # Левая колонка - пики союзников (Radiant)
    "ally_picks": [
        (100, 200, 150, 80),   # slot 1
        (100, 290, 150, 80),   # slot 2
        (100, 380, 150, 80),   # slot 3
        (100, 470, 150, 80),   # slot 4
        (100, 560, 150, 80),   # slot 5
    ],
    # Правая колонка - пики врагов (Dire)
    "enemy_picks": [
        (1670, 200, 150, 80),  # slot 1
        (1670, 290, 150, 80),  # slot 2
        (1670, 380, 150, 80),  # slot 3
        (1670, 470, 150, 80),  # slot 4
        (1670, 560, 150, 80),  # slot 5
    ],
    # Баны (если нужно)
    "ally_bans": [
        (250, 150, 60, 60),
        (320, 150, 60, 60),
        (390, 150, 60, 60),
    ],
    "enemy_bans": [
        (1520, 150, 60, 60),
        (1450, 150, 60, 60),
        (1380, 150, 60, 60),
    ],
}

# Порог схожести для template matching (0-1)
TEMPLATE_MATCH_THRESHOLD = 0.75

# Настройки API
CACHE_TTL_HOURS = 24  # Сколько хранить кэш
REQUEST_DELAY = 1.0   # Задержка между запросами к API (сек)

# Веса для скоринг-модели
SCORING_WEIGHTS = {
    "base_winrate": 1.0,      # Базовый винрейт героя
    "counter_bonus": 0.8,     # Бонус за контрпик врага
    "synergy_bonus": 0.6,     # Бонус за синергию с союзником
    "role_penalty": 0.5,      # Пенальти за дублирование роли
    "meta_multiplier": 1.0,     # Множитель меты (обновляется под патч)
}

# Роли героев
ROLES = ["Carry", "Support", "Offlane", "Mid", "Roaming"]

# Tesseract путь (Windows)
# Установи Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
