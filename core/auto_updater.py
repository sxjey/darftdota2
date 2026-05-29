"""
Авто-обновление данных при старте приложения.
Проверяет свежесть кэша; если старше N часов — фоном обновляет.
"""
import threading
import time
from pathlib import Path
from typing import Callable, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import CACHE_DIR, WINRATES_FILE, MATCHUP_DATA_FILE, CACHE_TTL_HOURS


def _is_file_stale(path: Path, max_age_hours: int) -> bool:
    """True если файла нет или он старше max_age_hours"""
    if not path.exists():
        return True
    age = time.time() - path.stat().st_mtime
    return age > max_age_hours * 3600


def needs_update(max_age_hours: int = None) -> bool:
    """Нужно ли обновлять данные"""
    if max_age_hours is None:
        max_age_hours = CACHE_TTL_HOURS
    
    bracket_file = CACHE_DIR / "winrates_by_rank.json"
    
    # Если хотя бы одного критичного файла нет/устарел — обновляем
    return (
        _is_file_stale(bracket_file, max_age_hours)
        or _is_file_stale(WINRATES_FILE, max_age_hours)
        or _is_file_stale(MATCHUP_DATA_FILE, max_age_hours * 3)  # matchups можно реже
    )


class BackgroundUpdater:
    """
    Фоновое обновление данных.
    Использует callback для статуса (строка) и завершения.
    """
    
    def __init__(self,
                 on_status: Optional[Callable[[str], None]] = None,
                 on_done: Optional[Callable[[bool, str], None]] = None):
        self.on_status = on_status or (lambda s: None)
        self.on_done = on_done or (lambda ok, msg: None)
        self.thread: Optional[threading.Thread] = None
        self._cancelled = False
    
    def is_running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()
    
    def start(self, full: bool = False):
        """
        Запустить обновление в фоне.
        
        Args:
            full: True — обновлять всё включая matchups (долго, ~3 мин).
                  False — только список героев + винрейты по рангам (~5 сек).
        """
        if self.is_running():
            return
        self._cancelled = False
        self.thread = threading.Thread(target=self._run, args=(full,), daemon=True)
        self.thread.start()
    
    def cancel(self):
        self._cancelled = True
    
    def _run(self, full: bool):
        try:
            from data.opendota_client import OpenDotaClient
            import json
            
            client = OpenDotaClient()
            
            # 1. Список героев
            self.on_status("Загрузка списка героев…")
            heroes_list = client.get_heroes()
            heroes_dict = {}
            for h in heroes_list:
                heroes_dict[h["id"]] = {
                    "name": h.get("name", "").replace("npc_dota_hero_", ""),
                    "localized_name": h.get("localized_name", ""),
                    "roles": h.get("roles", []),
                }
            with open(CACHE_DIR / "heroes_dynamic.json", 'w', encoding='utf-8') as f:
                json.dump(heroes_dict, f, ensure_ascii=False, indent=2)
            
            if self._cancelled:
                self.on_done(False, "Отменено")
                return
            
            # 2. Винрейты общие
            self.on_status("Загрузка винрейтов…")
            winrates = client.get_hero_winrates()
            with open(WINRATES_FILE, 'w', encoding='utf-8') as f:
                json.dump(winrates, f, indent=2)
            
            # 3. Винрейты по рангам
            self.on_status("Загрузка статистики по рангам…")
            bracket_stats = client.get_hero_stats_by_rank()
            with open(CACHE_DIR / "winrates_by_rank.json", 'w', encoding='utf-8') as f:
                json.dump(bracket_stats, f, indent=2)
            
            if self._cancelled:
                self.on_done(False, "Отменено")
                return
            
            # 4. Matchups (только если full)
            if full or _is_file_stale(MATCHUP_DATA_FILE, CACHE_TTL_HOURS * 3):
                self.on_status("Загрузка контрпиков (это займёт пару минут)…")
                client.get_all_matchups()
            
            self.on_status("Готово")
            self.on_done(True, "Данные обновлены")
            
        except Exception as e:
            self.on_done(False, f"Ошибка: {e}")


def auto_update_if_needed(on_status: Callable[[str], None],
                          on_done: Callable[[bool, str], None]) -> Optional[BackgroundUpdater]:
    """
    Запускает обновление если нужно. Возвращает updater или None.
    """
    if not needs_update():
        on_status("Данные актуальны")
        return None
    
    # Нужен ли полный апдейт (с matchups) — решаем по их возрасту
    full = _is_file_stale(MATCHUP_DATA_FILE, CACHE_TTL_HOURS * 7)
    
    updater = BackgroundUpdater(on_status=on_status, on_done=on_done)
    updater.start(full=full)
    return updater
