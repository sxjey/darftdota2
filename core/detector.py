"""
Детекция фазы драфта и захват скриншотов
"""
import cv2
import numpy as np
from PIL import ImageGrab
from typing import Optional, Tuple
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import SCREENSHOT_REGIONS
from core.hero_recognizer import HeroRecognizer


class DraftDetector:
    """
    Детектор драфта Dota 2
    Захватывает скриншоты и распознаёт состояние
    """
    
    def __init__(self):
        self.recognizer = HeroRecognizer()
        self.last_screenshot: Optional[np.ndarray] = None
        self.is_dota_running = False
    
    def capture_screen(self, region: Tuple[int, int, int, int] = None) -> np.ndarray:
        """
        Сделать скриншот экрана
        
        Args:
            region: (left, top, right, bottom) или None для полного экрана
        
        Returns:
            Скриншот в формате numpy array (BGR для OpenCV)
        """
        if region:
            screenshot = ImageGrab.grab(bbox=region)
        else:
            screenshot = ImageGrab.grab()
        
        # Конвертируем PIL Image в numpy array (BGR для OpenCV)
        screenshot_np = np.array(screenshot)
        # RGB to BGR
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        self.last_screenshot = screenshot_bgr
        return screenshot_bgr
    
    def is_draft_active(self, screenshot: np.ndarray = None) -> bool:
        """
        Проверить, активен ли сейчас драфт
        
        Простая эвристика: ищем характерные элементы UI драфта
        Можно искать:
        - Цвета фона панелей пиков
        - Текст "Select Hero" / "Ban Hero"
        - Специфичные элементы интерфейса
        
        Returns:
            True если похоже что драфт активен
        """
        if screenshot is None:
            screenshot = self.capture_screen()
        
        # TODO: Реализовать проверку по характерным элементам UI
        # Пока просто проверяем что есть что-то в ROI
        
        # Проверяем ROI для пиков союзников
        for region in SCREENSHOT_REGIONS.get("ally_picks", []):
            x, y, w, h = region
            if y + h <= screenshot.shape[0] and x + w <= screenshot.shape[1]:
                roi = screenshot[y:y+h, x:x+w]
                # Если ROI не пустой и не однородный - возможно там пик
                if roi.std() > 10:  # Есть вариации цвета
                    return True
        
        return False
    
    def detect_draft_state(self, screenshot: np.ndarray = None) -> dict:
        """
        Распознать полное состояние драфта
        
        Returns:
            {
                'is_active': bool,
                'ally_picks': [(hero_id, confidence), ...],
                'enemy_picks': [...],
                'ally_bans': [...],
                'enemy_bans': [...],
            }
        """
        if screenshot is None:
            screenshot = self.capture_screen()
        
        # Распознаём всех героев
        detections = self.recognizer.detect_all_picks(screenshot, SCREENSHOT_REGIONS)
        
        return {
            "is_active": self.is_draft_active(screenshot),
            **detections
        }
    
    def find_dota_window(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Найти окно Dota 2 и получить его координаты
        
        Returns:
            (left, top, right, bottom) или None
        """
        try:
            # Windows: используем win32gui
            import win32gui
            
            def enum_windows_callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if "dota 2" in title.lower():
                        rect = win32gui.GetWindowRect(hwnd)
                        extra.append(rect)
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                return windows[0]  # (left, top, right, bottom)
            
        except ImportError:
            print("win32gui не установлен. Установи: pip install pywin32")
        
        return None
    
    def wait_for_draft(self, timeout: float = 60.0, poll_interval: float = 1.0) -> bool:
        """
        Ждать начала драфта
        
        Args:
            timeout: Максимальное время ожидания (сек)
            poll_interval: Интервал проверки (сек)
        
        Returns:
            True если драфт начался
        """
        print(f"Ожидание драфта (таймаут: {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                screenshot = self.capture_screen()
                if self.is_draft_active(screenshot):
                    print("✓ Драфт обнаружен!")
                    return True
            except Exception as e:
                print(f"Ошибка захвата экрана: {e}")
            
            time.sleep(poll_interval)
        
        print("✗ Драфт не обнаружен")
        return False
    
    def start_monitoring(self, callback, interval: float = 1.0):
        """
        Начать мониторинг драфта в фоне
        
        Args:
            callback: Функция callback(state_dict) вызываемая при изменении
            interval: Интервал проверки (сек)
        """
        print(f"Мониторинг драфта начат (интервал: {interval}s)")
        print("Нажми Ctrl+C для остановки")
        
        previous_state = None
        
        try:
            while True:
                try:
                    screenshot = self.capture_screen()
                    current_state = self.detect_draft_state(screenshot)
                    
                    # Проверяем изменения
                    if current_state != previous_state:
                        callback(current_state)
                        previous_state = current_state
                    
                except Exception as e:
                    print(f"Ошибка: {e}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nМониторинг остановлен")


class ManualDraftDetector:
    """
    Ручной ввод состояния драфта (фоллбэк)
    """
    
    @staticmethod
    def manual_input_dialog():
        """
        Диалог ручного ввода
        Запрашивает у пользователя пики через консоль
        """
        from core.draft_state import get_draft_state, DraftPhase
        from data.heroes_static import search_hero
        
        state = get_draft_state()
        state.reset()
        state.phase = DraftPhase.PICK_PHASE_1
        
        print("\n" + "="*50)
        print("РУЧНОЙ ВВОД ДРАФТА")
        print("="*50)
        
        # Спрашиваем сторону
        side = input("Играем за Radiant? (y/n): ").lower().strip()
        state.is_radiant = side in ('y', 'yes', 'да', 'д')
        
        print(f"\nМы играем за: {'Radiant' if state.is_radiant else 'Dire'}")
        print("Вводи имена героев. Пустая строка = пропуск. 'q' = выход")
        
        while not state.is_complete():
            turn = state.get_current_turn()
            if turn is None:
                break
            
            pick_num = len(state.ally_picks) + len(state.enemy_picks) + 1
            team = "НАША КОМАНДА" if turn == 'ally' else "ВРАГИ"
            
            print(f"\n--- Пик #{pick_num} ({team}) ---")
            query = input("Герой: ").strip()
            
            if query.lower() == 'q':
                break
            
            if not query:
                continue
            
            # Ищем героя
            results = search_hero(query)
            if not results:
                print(f"Герой '{query}' не найден. Попробуй ещё раз.")
                continue
            
            # Если несколько результатов - показываем выбор
            hero = results[0]
            if len(results) > 1:
                print(f"Найдено {len(results)} героев:")
                for i, h in enumerate(results[:5], 1):
                    print(f"  {i}. {h['localized_name']}")
                
                choice = input("Выбери номер (1-5, Enter=1): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(results):
                    hero = results[int(choice) - 1]
            
            # Добавляем пик
            if turn == 'ally':
                state.add_ally_pick(hero['id'], hero['localized_name'])
                print(f"  → Добавлен: {hero['localized_name']}")
            else:
                state.add_enemy_pick(hero['id'], hero['localized_name'])
                print(f"  → Добавлен враг: {hero['localized_name']}")
        
        print("\n" + "="*50)
        print("Драфт завершён!")
        print(state)
        
        return state


if __name__ == "__main__":
    # Тест детектора
    print("Тест DraftDetector")
    print("-" * 30)
    
    detector = DraftDetector()
    
    # Тест захвата экрана
    print("\n1. Захват скриншота...")
    screenshot = detector.capture_screen()
    print(f"   Размер: {screenshot.shape}")
    
    # Сохраняем для проверки
    test_path = Path("test_screenshot.png")
    cv2.imwrite(str(test_path), screenshot)
    print(f"   Сохранено: {test_path.absolute()}")
    
    # Тест ручного ввода
    print("\n2. Тест ручного ввода...")
    ManualDraftDetector.manual_input_dialog()
