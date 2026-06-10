"""
Распознавание героев по скриншотам
Использует template matching для определения героев
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import HERO_ICONS_DIR, TEMPLATE_MATCH_THRESHOLD


class HeroRecognizer:
    """
    Распознавание героев по иконкам
    Загружает шаблоны и сравнивает с областями скриншота
    """
    
    def __init__(self):
        self.templates: Dict[int, np.ndarray] = {}
        self.hero_names: Dict[int, str] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Загрузить шаблоны иконок героев"""
        if not HERO_ICONS_DIR.exists():
            print(f"Предупреждение: папка с иконками не найдена: {HERO_ICONS_DIR}")
            return
        
        # Загружаем иконки из папки assets/hero_icons/
        # Имена файлов: {hero_id}.png
        for icon_file in HERO_ICONS_DIR.glob("*.png"):
            try:
                hero_id = int(icon_file.stem)
                template = cv2.imread(str(icon_file), cv2.IMREAD_COLOR)
                if template is not None:
                    self.templates[hero_id] = template
            except ValueError:
                continue
        
        # Загружаем имена героев
        from data.heroes_static import get_all_heroes
        heroes = get_all_heroes()
        for hero_id, hero in heroes.items():
            self.hero_names[hero_id] = hero["localized_name"]
        
        print(f"Загружено {len(self.templates)} шаблонов героев")
    
    def match_hero(self, image: np.ndarray, threshold: float = None) -> Optional[Tuple[int, float]]:
        """
        Найти героя на изображении
        
        Args:
            image: ROI из скриншота (BGR формат)
            threshold: Порог схожести (0-1)
        
        Returns:
            (hero_id, confidence) или None
        """
        if threshold is None:
            threshold = TEMPLATE_MATCH_THRESHOLD
        
        if not self.templates:
            return None
        
        best_match = None
        best_score = 0
        
        for hero_id, template in self.templates.items():
            # Масштабируем шаблон под размер ROI если нужно
            if image.shape[:2] != template.shape[:2]:
                template_resized = cv2.resize(template, (image.shape[1], image.shape[0]))
            else:
                template_resized = template
            
            # Template matching
            result = cv2.matchTemplate(image, template_resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            if max_val > best_score:
                best_score = max_val
                best_match = hero_id
        
        if best_score >= threshold:
            return (best_match, best_score)
        
        return None
    
    def match_hero_in_region(self, screenshot: np.ndarray, 
                             region: Tuple[int, int, int, int],
                             threshold: float = None) -> Optional[Tuple[int, float]]:
        """
        Найти героя в определённой области скриншота
        
        Args:
            screenshot: Полный скриншот
            region: (x, y, width, height)
            threshold: Порог схожести
        
        Returns:
            (hero_id, confidence) или None
        """
        x, y, w, h = region
        roi = screenshot[y:y+h, x:x+w]
        
        if roi.size == 0:
            return None
        
        return self.match_hero(roi, threshold)
    
    def detect_all_picks(self, screenshot: np.ndarray, 
                         regions: Dict[str, List[Tuple]]) -> Dict[str, List[Tuple[int, float]]]:
        """
        Распознать все пики на скриншоте
        
        Args:
            screenshot: Полный скриншот
            regions: Словарь регионов из settings.SCREENSHOT_REGIONS
        
        Returns:
            {'ally_picks': [(hero_id, confidence), ...], 'enemy_picks': [...]}
        """
        results = {
            "ally_picks": [],
            "enemy_picks": [],
            "ally_bans": [],
            "enemy_bans": [],
        }
        
        # Распознаём пики союзников
        for region in regions.get("ally_picks", []):
            match = self.match_hero_in_region(screenshot, region)
            if match:
                results["ally_picks"].append(match)
        
        # Распознаём пики врагов
        for region in regions.get("enemy_picks", []):
            match = self.match_hero_in_region(screenshot, region)
            if match:
                results["enemy_picks"].append(match)
        
        # Баны (если нужно)
        for region in regions.get("ally_bans", []):
            match = self.match_hero_in_region(screenshot, region)
            if match:
                results["ally_bans"].append(match)
        
        for region in regions.get("enemy_bans", []):
            match = self.match_hero_in_region(screenshot, region)
            if match:
                results["enemy_bans"].append(match)
        
        return results
    
    def get_hero_name(self, hero_id: int) -> str:
        """Получить имя героя по ID"""
        return self.hero_names.get(hero_id, f"Unknown ({hero_id})")


class ManualHeroInput:
    """
    Ручной ввод героев (фоллбэк если OCR не работает)
    """
    
    @staticmethod
    def find_hero_by_name(query: str) -> Optional[Dict]:
        """Найти героя по имени"""
        from data.heroes_static import search_hero
        results = search_hero(query)
        return results[0] if results else None
    
    @staticmethod
    def list_all_heroes() -> List[Dict]:
        """Получить список всех героев"""
        from data.heroes_static import get_all_heroes
        heroes = get_all_heroes()
        return [{"id": k, **v} for k, v in heroes.items()]


# Утилита для загрузки иконок
def download_hero_icons(output_dir: Path = None):
    """
    Загрузить иконки героев из Steam CDN
    Запусти один раз для подготовки шаблонов
    """
    if output_dir is None:
        output_dir = HERO_ICONS_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    from data.heroes_static import get_all_heroes
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    heroes = get_all_heroes()
    base_url = "https://cdn.dota2.com/apps/dota2/images/heroes/"

    print(f"Загрузка иконок в {output_dir}...")

    for hero_id, hero in heroes.items():
        hero_name = hero["name"]
        url = f"{base_url}{hero_name}_sb.png"
        output_path = output_dir / f"{hero_id}.png"

        if output_path.exists():
            continue

        try:
            response = requests.get(url, timeout=10, verify=False)
            if response.status_code == 200 and len(response.content) > 500:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"  OK {hero['localized_name']}")
            else:
                print(f"  SKIP {hero['localized_name']} (HTTP {response.status_code})")
        except Exception as e:
            print(f"  ERR {hero['localized_name']}: {type(e).__name__}")
    
    print(f"\nИконки сохранены в: {output_dir}")


if __name__ == "__main__":
    # Тест распознавания
    print("Загрузка шаблонов...")
    recognizer = HeroRecognizer()
    
    # Загрузка иконок если нужно
    if len(recognizer.templates) == 0:
        print("\nИконки не найдены. Запуск загрузки...")
        download_hero_icons()
        recognizer._load_templates()
    
    print(f"\nЗагружено шаблонов: {len(recognizer.templates)}")
