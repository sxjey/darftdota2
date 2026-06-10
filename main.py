"""
Dota 2 Draft Assistant
Главный файл запуска

Использование:
    python main.py              - Запустить GUI
    python main.py --update     - Обновить данные из API
    python main.py --test       - Тест компонентов
    python main.py --manual     - Ручной ввод через консоль
"""
import sys
import argparse
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent))


def check_dependencies():
    missing = []
    for import_name, pip_name in [
        ("webview", "pywebview"),
        ("cv2", "opencv-python"),
        ("requests", "requests"),
        ("numpy", "numpy"),
        ("PIL", "Pillow"),
    ]:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)
    if missing:
        print("Missing deps: " + ", ".join(missing))
        print("pip install " + " ".join(missing))
        return False
    return True


def update_data():
    """Обновить данные из API"""
    print("="*60)
    print("ОБНОВЛЕНИЕ ДАННЫХ")
    print("="*60)
    
    from data.opendota_client import update_all_data
    update_all_data()
    
    print("\n✅ Данные обновлены!")


def test_components():
    """Тест всех компонентов"""
    print("="*60)
    print("ТЕСТИРОВАНИЕ КОМПОНЕНТОВ")
    print("="*60)
    
    # 1. Тест heroes_static
    print("\n1. Тест данных о героях...")
    from data.heroes_static import get_all_heroes, search_hero
    heroes = get_all_heroes()
    print(f"   ✅ Загружено {len(heroes)} героев")
    
    results = search_hero("anti")
    print(f"   ✅ Поиск работает: нашёл {len(results)} героев по 'anti'")
    
    # 2. Тест draft_state
    print("\n2. Тест состояния драфта...")
    from core.draft_state import DraftState, DraftPhase
    state = DraftState()
    state.add_ally_pick(1, "Anti-Mage")
    state.add_enemy_pick(14, "Pudge")
    print(f"   ✅ Состояние работает: {len(state.ally_picks)} союзник, {len(state.enemy_picks)} враг")
    
    # 3. Тест recommender
    print("\n3. Тест рекомендатора...")
    from scoring.recommender import HeroRecommender
    recommender = HeroRecommender()
    recommendations = recommender.get_recommendations(state, top_n=3)
    print(f"   ✅ Рекомендации работают: получено {len(recommendations)} предложений")
    if recommendations:
        print(f"   Топ рекомендация: {recommendations[0].hero_name} (скор: {recommendations[0].total_score:.1f})")
    
    # 4. Тест захвата экрана
    print("\n4. Тест захвата экрана...")
    try:
        from core.detector import DraftDetector
        detector = DraftDetector()
        screenshot = detector.capture_screen()
        print(f"   ✅ Скриншот сделан: размер {screenshot.shape}")
    except Exception as e:
        print(f"   ⚠️ Скриншот: {e}")
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60)


def manual_draft():
    """Ручной ввод драфта через консоль"""
    print("="*60)
    print("РУЧНОЙ ВВОД ДРАФТА")
    print("="*60)
    
    from core.detector import ManualDraftDetector
    from scoring.recommender import HeroRecommender
    
    # Ввод драфта
    ManualDraftDetector.manual_input_dialog()
    
    # Получаем состояние
    from core.draft_state import get_draft_state
    state = get_draft_state()
    
    # Рекомендации
    print("\n" + "="*60)
    print("ГЕНЕРАЦИЯ РЕКОМЕНДАЦИЙ...")
    print("="*60)
    
    recommender = HeroRecommender()
    recommendations = recommender.get_recommendations(state, top_n=5)
    
    print("\n🏆 ТОП-5 РЕКОМЕНДАЦИЙ:")
    print("-"*60)
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec.hero_name}")
        print(f"   Скор: {rec.total_score:.1f} | Роли: {', '.join(rec.roles)}")
        print(f"   Почему: {rec.explanation}")
    
    print("\n" + "="*60)


def run_gui():
    import webview
    from ui.api import Api
    import threading

    api = Api()
    html_path = Path(__file__).parent / "ui" / "web" / "index.html"
    url = str(html_path)

    window = webview.create_window(
        "Dota 2 Draft Assistant",
        url=url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(900, 600),
        resizable=True,
        background_color='#1a1a2e',
    )

    def bind_focus_fix():
        try:
            import clr
            clr.AddReference("System.Windows.Forms")
            from System.Windows.Forms import Application
            form = Application.OpenForms[0]
            was_active = [True]
            def on_activate(s, e):
                if not was_active[0]:
                    was_active[0] = True
                    window.load_url(url)
            def on_deactivate(s, e):
                was_active[0] = False
            form.Activated += on_activate
            form.Deactivate += on_deactivate
        except Exception:
            pass

    def on_shown():
        threading.Thread(target=bind_focus_fix, daemon=True).start()

    window.events.shown += on_shown
    webview.start(http_server=True)


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Dota 2 Draft Assistant')
    parser.add_argument('--update', action='store_true', 
                       help='Обновить данные из OpenDota API')
    parser.add_argument('--test', action='store_true',
                       help='Запустить тесты компонентов')
    parser.add_argument('--manual', action='store_true',
                       help='Ручной ввод через консоль')
    parser.add_argument('--download-icons', action='store_true',
                       help='Загрузить иконки героев')
    
    args = parser.parse_args()
    
    # Проверка зависимостей
    if not check_dependencies():
        sys.exit(1)
    
    # Обработка аргументов
    if args.update:
        update_data()
    elif args.test:
        test_components()
    elif args.manual:
        manual_draft()
    elif args.download_icons:
        print("Downloading hero icons...")
        from core.hero_recognizer import download_hero_icons
        download_hero_icons()
    else:
        # По умолчанию - GUI
        run_gui()


if __name__ == "__main__":
    main()
