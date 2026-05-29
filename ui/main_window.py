"""
Draft Assistant — современный UI с авто-распределением позиций
и инлайн-поиском героев (без модальных окон).
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path
from typing import List, Optional, Callable

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.draft_state import get_draft_state, reset_draft
from core.auto_updater import auto_update_if_needed
from scoring.recommender import HeroRecommender, HeroScore, BRACKETS
from scoring.position_assigner import assign_positions, get_priority_position, POSITIONS
from data.heroes_static import search_hero, get_all_heroes, get_hero_by_id


# ============== ЦВЕТОВАЯ СХЕМА ==============
C = {
    "bg":          "#15171f",
    "panel":       "#1d1f2a",
    "card":        "#272a37",
    "card_hover":  "#323645",
    "card_active": "#3a3f52",
    "border":      "#363a4a",
    "border_hot":  "#4cafef",
    "accent":      "#4cafef",
    "accent_dim":  "#2c6c92",
    "ally":        "#5fd97a",
    "enemy":       "#ff6b6b",
    "text":        "#ecedf2",
    "text_dim":    "#8a90a6",
    "text_muted":  "#5d6378",
    "good":        "#5fd97a",
    "mid":         "#ffb74d",
    "bad":         "#ff6b6b",
    "highlight":   "#ffd54f",
}

POSITION_INFO = {
    "Carry":   {"icon": "🗡", "label": "Carry",   "sub": "поз. 1 · safelane"},
    "Mid":     {"icon": "⚡", "label": "Mid",     "sub": "поз. 2 · midlane"},
    "Offlane": {"icon": "🛡", "label": "Offlane", "sub": "поз. 3 · hardlane"},
    "Support": {"icon": "💙", "label": "Support", "sub": "поз. 5 · hard sup"},
    "Roaming": {"icon": "👟", "label": "Roaming", "sub": "поз. 4 · soft sup"},
}


# ============== УТИЛИТЫ ==============
def make_hover(widget, color_normal, color_hover):
    """Добавить hover-эффект для виджета"""
    def on_enter(e):
        widget.configure(bg=color_hover)
        for c in widget.winfo_children():
            try:
                c.configure(bg=color_hover)
            except tk.TclError:
                pass
    def on_leave(e):
        widget.configure(bg=color_normal)
        for c in widget.winfo_children():
            try:
                c.configure(bg=color_normal)
            except tk.TclError:
                pass
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def score_color(score: float) -> str:
    if score >= 65:
        return C["good"]
    if score >= 50:
        return C["mid"]
    return C["bad"]


# ============== ИНЛАЙН ПОИСК ГЕРОЯ ==============
class InlineHeroPicker(tk.Frame):
    """
    Inline-поиск героя без модальных окон.
    Раскрывается прямо в слоте: Entry + выпадающий список.
    """
    def __init__(self, parent, on_select: Callable, excluded: set,
                 placeholder="Введите имя героя..."):
        super().__init__(parent, bg=C["card"])
        self.on_select = on_select
        self.excluded = excluded
        self._dropdown_window = None
        self._current_results = []

        self.entry = tk.Entry(
            self, font=("Segoe UI", 10),
            bg=C["card"], fg=C["text"],
            insertbackground=C["accent"],
            relief="flat", borderwidth=0,
            highlightthickness=2,
            highlightbackground=C["border"],
            highlightcolor=C["accent"],
        )
        self.entry.pack(fill="both", expand=True, ipady=6, padx=2, pady=2)
        self.entry.insert(0, placeholder)
        self._is_placeholder = True

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<KeyRelease>", self._on_type)
        self.entry.bind("<Down>", self._move_down)
        self.entry.bind("<Up>", self._move_up)
        self.entry.bind("<Return>", self._confirm_top)
        self.entry.bind("<Escape>", lambda e: self._close_dropdown())

    def focus_input(self):
        self.entry.focus_set()

    def _on_focus_in(self, _):
        if self._is_placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=C["text"])
            self._is_placeholder = False
        self._update_dropdown()

    def _on_focus_out(self, _):
        # Задержка чтобы успел сработать клик в дропдауне
        self.after(150, self._close_if_no_focus)

    def _close_if_no_focus(self):
        if self._dropdown_window:
            try:
                if self.focus_get() and str(self.focus_get()).startswith(str(self._dropdown_window)):
                    return
            except Exception:
                pass
        self._close_dropdown()

    def _on_type(self, event):
        if event.keysym in ("Down", "Up", "Return", "Escape"):
            return
        self._update_dropdown()

    def _get_results(self) -> list:
        query = self.entry.get().strip().lower()
        all_h = get_all_heroes()
        if not query or self._is_placeholder:
            results = sorted(
                [{"id": hid, **h} for hid, h in all_h.items() if hid not in self.excluded],
                key=lambda x: x["localized_name"]
            )
        else:
            results = [h for h in search_hero(query) if h["id"] not in self.excluded]
        return results[:50]

    def _update_dropdown(self):
        results = self._get_results()
        self._current_results = results
        if not results:
            self._close_dropdown()
            return
        self._show_dropdown(results)

    def _show_dropdown(self, results):
        if self._dropdown_window is None or not self._dropdown_window.winfo_exists():
            self._build_dropdown()

        # Позиционируем под Entry
        self.entry.update_idletasks()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
        w = self.entry.winfo_width()
        h = min(280, len(results) * 32 + 4)
        self._dropdown_window.geometry(f"{w}x{h}+{x}+{y}")
        self._dropdown_window.deiconify()
        self._dropdown_window.lift()

        # Обновляем список
        self.listbox.delete(0, tk.END)
        for h in results:
            roles = ", ".join(h.get("roles", [])[:2]) or "—"
            self.listbox.insert(tk.END, f"  {h['localized_name']:<26} {roles}")
        if results:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.activate(0)

    def _build_dropdown(self):
        self._dropdown_window = tk.Toplevel(self)
        self._dropdown_window.overrideredirect(True)
        self._dropdown_window.attributes("-topmost", True)
        self._dropdown_window.configure(bg=C["border"])

        self.listbox = tk.Listbox(
            self._dropdown_window,
            font=("Segoe UI", 10),
            bg=C["card"], fg=C["text"],
            selectbackground=C["accent"],
            selectforeground="white",
            relief="flat", borderwidth=0,
            highlightthickness=0,
            activestyle="none",
        )
        self.listbox.pack(fill="both", expand=True, padx=1, pady=1)
        self.listbox.bind("<Button-1>", self._on_listbox_click)
        self.listbox.bind("<Double-1>", self._confirm_top)
        self.listbox.bind("<Return>", self._confirm_top)

    def _on_listbox_click(self, event):
        idx = self.listbox.nearest(event.y)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self._confirm_index(idx)

    def _close_dropdown(self):
        if self._dropdown_window:
            try:
                self._dropdown_window.withdraw()
            except tk.TclError:
                pass

    def _move_down(self, _):
        if not self._dropdown_window:
            return "break"
        cur = self.listbox.curselection()
        idx = (cur[0] + 1) if cur else 0
        idx = min(idx, self.listbox.size() - 1)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.see(idx)
        return "break"

    def _move_up(self, _):
        if not self._dropdown_window:
            return "break"
        cur = self.listbox.curselection()
        idx = max(0, (cur[0] - 1) if cur else 0)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.see(idx)
        return "break"

    def _confirm_top(self, _=None):
        cur = self.listbox.curselection() if self._dropdown_window else None
        idx = cur[0] if cur else 0
        self._confirm_index(idx)
        return "break"

    def _confirm_index(self, idx: int):
        if 0 <= idx < len(self._current_results):
            hero = self._current_results[idx]
            self._close_dropdown()
            self.on_select(hero)

    def destroy(self):
        if self._dropdown_window:
            try:
                self._dropdown_window.destroy()
            except tk.TclError:
                pass
        super().destroy()


# ============== ПАНЕЛЬ КОМАНДЫ (простая) ==============
class TeamPanel(tk.Frame):
    """
    Простой список из пиков + одна кнопка "добавить".
    Рядом с каждым героем мелким шрифтом показывается какую позицию
    он скорее всего занимает (для обучения).
    """

    def __init__(self, parent, title: str, is_ally: bool, on_change: Callable):
        super().__init__(parent, bg=C["panel"])
        self.is_ally = is_ally
        self.on_change = on_change
        self._picker_widget = None  # активный поиск (если открыт)

        accent = C["ally"] if is_ally else C["enemy"]
        self.accent = accent

        # Шапка панели
        header = tk.Frame(self, bg=C["panel"])
        header.pack(fill="x", padx=12, pady=(10, 4))

        tk.Label(header, text=title, bg=C["panel"],
                 fg=accent, font=("Segoe UI", 12, "bold")
                 ).pack(side="left")

        self.count_label = tk.Label(header, text="0/5", bg=C["panel"],
                                    fg=C["text_dim"], font=("Segoe UI", 9))
        self.count_label.pack(side="right")

        # Контейнер слотов
        self.slots_frame = tk.Frame(self, bg=C["panel"])
        self.slots_frame.pack(fill="both", expand=True, padx=10, pady=4)

        # Кнопка/поиск добавления
        self.add_container = tk.Frame(self, bg=C["panel"])
        self.add_container.pack(fill="x", padx=10, pady=(4, 10))

        self.refresh()

    def refresh(self):
        for w in self.slots_frame.winfo_children():
            w.destroy()
        for w in self.add_container.winfo_children():
            w.destroy()

        state = get_draft_state()
        picks = state.ally_picks if self.is_ally else state.enemy_picks

        # Авто-распределение для подписи позиций
        assignment = assign_positions(picks)
        # обратная карта: hero_id -> position_label
        hero_to_pos = {}
        for pos, h in assignment.items():
            if h:
                hero_to_pos[h["hero_id"]] = pos

        # Рендер пиков
        for pick in picks:
            pos = hero_to_pos.get(pick.hero_id, "")
            self._render_pick(pick, pos)

        # Кнопка добавления (или активный поиск)
        if len(picks) < 5:
            self._render_add_button()

        self.count_label.config(text=f"{len(picks)}/5")

    def _render_pick(self, pick, position: str):
        card = tk.Frame(self.slots_frame, bg=C["card"],
                        highlightbackground=self.accent,
                        highlightthickness=1)
        card.pack(fill="x", pady=3)

        # Цветная полоска слева
        stripe = tk.Frame(card, bg=self.accent, width=4)
        stripe.pack(side="left", fill="y")

        content = tk.Frame(card, bg=C["card"])
        content.pack(side="left", fill="both", expand=True, padx=10, pady=6)

        # Имя героя
        tk.Label(content, text=pick.hero_name, bg=C["card"],
                 fg=C["text"], font=("Segoe UI", 11, "bold"),
                 anchor="w").pack(fill="x")

        # Подпись позиции (мелким шрифтом, для обучения)
        if position:
            info = POSITION_INFO.get(position, {})
            label = f"{info.get('icon', '')} {info.get('label', position)} · {info.get('sub', '')}"
            tk.Label(content, text=label, bg=C["card"],
                     fg=C["text_dim"], font=("Segoe UI", 8),
                     anchor="w").pack(fill="x")

        # Кнопка удаления
        btn = tk.Label(card, text="✕", bg=C["card"], fg=C["bad"],
                       font=("Segoe UI", 12, "bold"), cursor="hand2", padx=12)
        btn.pack(side="right", fill="y")
        btn.bind("<Button-1>", lambda e: self._remove(pick.hero_id))
        btn.bind("<Enter>", lambda e: btn.config(bg=C["card_hover"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=C["card"]))

    def _render_add_button(self):
        btn = tk.Frame(self.add_container, bg=C["card"],
                       highlightbackground=self.accent,
                       highlightthickness=1, cursor="hand2")
        btn.pack(fill="x")

        label = tk.Label(btn, text="＋  Добавить героя", bg=C["card"],
                         fg=C["text"], font=("Segoe UI", 10, "bold"),
                         padx=10, pady=10, cursor="hand2")
        label.pack(fill="x")

        def activate(event=None):
            self._activate_search()

        for w in (btn, label):
            w.bind("<Button-1>", activate)
            w.bind("<Enter>", lambda e, w=w: w.config(bg=C["card_hover"]))
            w.bind("<Leave>", lambda e, w=w: w.config(bg=C["card"]))

    def _activate_search(self):
        for w in self.add_container.winfo_children():
            w.destroy()

        state = get_draft_state()
        excluded = state.get_all_picked_heroes()

        picker = InlineHeroPicker(self.add_container,
                                  on_select=self._on_hero_selected,
                                  excluded=excluded)
        picker.pack(fill="x")
        picker.focus_input()

    def _on_hero_selected(self, hero: dict):
        state = get_draft_state()
        if self.is_ally:
            state.add_ally_pick(hero["id"], hero["localized_name"])
        else:
            state.add_enemy_pick(hero["id"], hero["localized_name"])
        self.on_change()

    def _remove(self, hero_id: int):
        state = get_draft_state()
        if self.is_ally:
            state.remove_ally_pick(hero_id)
        else:
            state.remove_enemy_pick(hero_id)
        self.on_change()


# ============== АНАЛИЗ МАТЧАПА (5v5) ==============
class MatchupAnalysis(tk.Frame):
    """
    Панель анализа когда обе команды заполнены.
    Показывает кто выигрывает драфт и насколько.
    """

    def __init__(self, parent, recommender: HeroRecommender):
        super().__init__(parent, bg=C["panel"])
        self.recommender = recommender

        # Шапка
        header = tk.Frame(self, bg=C["panel"])
        header.pack(fill="x", padx=14, pady=(10, 4))

        tk.Label(header, text="📊 Анализ драфта",
                 bg=C["panel"], fg=C["accent"],
                 font=("Segoe UI", 12, "bold")).pack(side="left")

        self.verdict_label = tk.Label(header, text="",
                                      bg=C["panel"], fg=C["text"],
                                      font=("Segoe UI", 11, "bold"))
        self.verdict_label.pack(side="right")

        # Полоса преимущества
        self.advantage_canvas = tk.Canvas(self, height=28, bg=C["panel"],
                                          highlightthickness=0)
        self.advantage_canvas.pack(fill="x", padx=14, pady=(4, 10))

        # Контент: две колонки команд + факторы
        body = tk.Frame(self, bg=C["panel"])
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        body.grid_columnconfigure(0, weight=1, uniform="m")
        body.grid_columnconfigure(1, weight=1, uniform="m")

        self.ally_frame = tk.Frame(body, bg=C["card"])
        self.ally_frame.grid(row=0, column=0, sticky="nsew", padx=4)

        self.enemy_frame = tk.Frame(body, bg=C["card"])
        self.enemy_frame.grid(row=0, column=1, sticky="nsew", padx=4)

        # Ключевые факторы
        self.factors_frame = tk.Frame(self, bg=C["panel"])
        self.factors_frame.pack(fill="x", padx=14, pady=(0, 10))

    def refresh(self):
        state = get_draft_state()
        analysis = self.recommender.analyze_matchup(state)

        # === Полоса преимущества ===
        self.advantage_canvas.delete("all")
        w = self.advantage_canvas.winfo_width() or 1100
        h = 28
        # Фон
        self.advantage_canvas.create_rectangle(0, 0, w, h, fill=C["card"], outline="")

        # Левая часть = ally, правая = enemy. Преимущество смещает середину.
        pct = analysis["advantage_pct"]  # -100..100
        # 0% pct = середина 50/50
        ally_width = w * (50 + pct / 2) / 100
        ally_width = max(0, min(w, ally_width))

        self.advantage_canvas.create_rectangle(
            0, 0, ally_width, h, fill=C["ally"], outline="")
        self.advantage_canvas.create_rectangle(
            ally_width, 0, w, h, fill=C["enemy"], outline="")

        # Текст по центру
        self.advantage_canvas.create_text(
            w / 2, h / 2,
            text=f"{analysis['ally_total']:.0f}  ←  vs  →  {analysis['enemy_total']:.0f}",
            fill="white", font=("Segoe UI", 10, "bold"))

        # === Вердикт ===
        winner = analysis["winner"]
        color = (C["good"] if winner == "ally"
                 else C["bad"] if winner == "enemy"
                 else C["mid"])
        self.verdict_label.config(text=analysis["verdict"], fg=color)

        # === Колонки команд ===
        self._render_team(self.ally_frame, "✅ Твоя команда",
                          C["ally"], analysis["ally_scores"])
        self._render_team(self.enemy_frame, "⚔ Враги",
                          C["enemy"], analysis["enemy_scores"])

        # === Факторы ===
        for w_ in self.factors_frame.winfo_children():
            w_.destroy()
        if analysis["key_factors"]:
            for f in analysis["key_factors"]:
                tk.Label(self.factors_frame, text=f"• {f}",
                         bg=C["panel"], fg=C["text_dim"],
                         font=("Segoe UI", 9), anchor="w"
                         ).pack(fill="x", pady=1)

    def _render_team(self, parent, title, accent, scores):
        for w in parent.winfo_children():
            w.destroy()

        head = tk.Frame(parent, bg=accent)
        head.pack(fill="x")
        tk.Label(head, text=title, bg=accent, fg="white",
                 font=("Segoe UI", 10, "bold"), pady=4).pack()

        # Сортируем по скору для наглядности
        sorted_scores = sorted(scores, key=lambda s: s.total_score, reverse=True)
        for s in sorted_scores:
            row = tk.Frame(parent, bg=C["card"])
            row.pack(fill="x", padx=8, pady=4)

            tk.Label(row, text=s.hero_name, bg=C["card"],
                     fg=C["text"], font=("Segoe UI", 10, "bold"),
                     anchor="w").pack(side="left", fill="x", expand=True)

            tk.Label(row, text=f"{s.total_score:.0f}", bg=C["card"],
                     fg=score_color(s.total_score),
                     font=("Segoe UI", 11, "bold")
                     ).pack(side="right")

            if s.explanation and s.explanation != "сбалансированный пик":
                tk.Label(parent, text=f"   {s.explanation}",
                         bg=C["card"], fg=C["text_muted"],
                         font=("Segoe UI", 8), anchor="w",
                         wraplength=400, justify="left"
                         ).pack(fill="x", padx=8)


# ============== РЕКОМЕНДАЦИИ ПО РОЛЯМ ==============
class RoleRecommendations(tk.Frame):
    def __init__(self, parent, recommender: HeroRecommender,
                 on_pick_ally: Callable):
        super().__init__(parent, bg=C["panel"])
        self.recommender = recommender
        self.on_pick_ally = on_pick_ally

        header = tk.Frame(self, bg=C["panel"])
        header.pack(fill="x", padx=14, pady=(10, 4))

        tk.Label(header, text="🏆 Рекомендации по позициям",
                 bg=C["panel"], fg=C["accent"],
                 font=("Segoe UI", 12, "bold")).pack(side="left")

        self.priority_label = tk.Label(
            header, text="", bg=C["panel"],
            fg=C["highlight"], font=("Segoe UI", 9, "italic"))
        self.priority_label.pack(side="right")

        self.content = tk.Frame(self, bg=C["panel"])
        self.content.pack(fill="both", expand=True, padx=10, pady=4)

        self.refresh()

    def refresh(self):
        for w in self.content.winfo_children():
            w.destroy()

        state = get_draft_state()
        by_role = self.recommender.get_recommendations_by_role(state, top_per_role=3)
        priority = get_priority_position(state.ally_picks)

        if priority:
            self.priority_label.config(
                text=f"⚠ В команде не хватает: {POSITION_INFO[priority]['label']}")
        else:
            self.priority_label.config(text="✓ Все позиции заняты")

        for col, role in enumerate(POSITIONS):
            self.content.grid_columnconfigure(col, weight=1, uniform="r")
            is_priority = (role == priority)

            col_frame = tk.Frame(self.content, bg=C["card"],
                                 highlightbackground=C["highlight"] if is_priority else C["border"],
                                 highlightthickness=2 if is_priority else 1)
            col_frame.grid(row=0, column=col, sticky="nsew", padx=4, pady=4)

            info = POSITION_INFO[role]
            head_bg = C["highlight"] if is_priority else C["card_hover"]
            head_fg = "#1a1a1a" if is_priority else C["text"]

            head = tk.Frame(col_frame, bg=head_bg)
            head.pack(fill="x")
            tk.Label(head, text=f"{info['icon']} {info['label']}",
                     bg=head_bg, fg=head_fg,
                     font=("Segoe UI", 10, "bold"), pady=6).pack()

            heroes = by_role.get(role, [])
            if not heroes:
                tk.Label(col_frame, text="нет кандидатов",
                         bg=C["card"], fg=C["text_dim"],
                         font=("Segoe UI", 9, "italic"), pady=12).pack()
                continue

            for i, h in enumerate(heroes):
                self._make_card(col_frame, h, rank=i + 1)

    def _make_card(self, parent, hero: HeroScore, rank: int):
        card = tk.Frame(parent, bg=C["card_hover"], cursor="hand2")
        card.pack(fill="x", padx=6, pady=4)

        top = tk.Frame(card, bg=C["card_hover"])
        top.pack(fill="x", padx=8, pady=(6, 0))

        badges = {1: "🥇", 2: "🥈", 3: "🥉"}
        tk.Label(top, text=badges.get(rank, "•"), bg=C["card_hover"],
                 fg=C["text"], font=("Segoe UI", 10)).pack(side="left")

        tk.Label(top, text=f" {hero.hero_name}", bg=C["card_hover"],
                 fg=C["text"], font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(side="left", fill="x", expand=True)

        tk.Label(top, text=f"{hero.total_score:.0f}",
                 bg=C["card_hover"], fg=score_color(hero.total_score),
                 font=("Segoe UI", 11, "bold")).pack(side="right")

        exp = tk.Label(card, text=hero.explanation,
                       bg=C["card_hover"], fg=C["text_dim"],
                       font=("Segoe UI", 8), anchor="w",
                       wraplength=180, justify="left")
        exp.pack(fill="x", padx=8, pady=(0, 6))

        # Hover-эффект и клик
        def on_enter(e):
            card.configure(bg=C["card_active"])
            for w in [top, exp] + list(top.winfo_children()):
                try:
                    w.configure(bg=C["card_active"])
                except tk.TclError:
                    pass

        def on_leave(e):
            card.configure(bg=C["card_hover"])
            for w in [top, exp] + list(top.winfo_children()):
                try:
                    w.configure(bg=C["card_hover"])
                except tk.TclError:
                    pass

        def on_click(e):
            self.on_pick_ally(hero.hero_id, hero.hero_name)

        for w in [card, top, exp] + list(top.winfo_children()):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)


# ============== ГЛАВНОЕ ОКНО ==============
class DraftAssistantUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dota 2 Draft Assistant")
        self.root.geometry("1200x780")
        self.root.minsize(1000, 700)
        self.root.configure(bg=C["bg"])
        self.root.attributes("-topmost", True)

        # Иконка приложения (если есть)
        icon_path = Path(__file__).parent.parent / "assets" / "app_icon.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.recommender = HeroRecommender()
        self._updater = None  # фоновый апдейтер
        self._build()
        self.refresh_all()
        # Запускаем авто-обновление через секунду после старта окна
        self.root.after(500, self._start_auto_update)

    def _build(self):
        # ===== Верхняя панель =====
        top = tk.Frame(self.root, bg=C["bg"])
        top.pack(fill="x", padx=14, pady=10)

        tk.Label(top, text="🎮  DOTA 2 DRAFT ASSISTANT",
                 bg=C["bg"], fg=C["accent"],
                 font=("Segoe UI", 14, "bold")).pack(side="left")

        # Статус обновления данных
        self.status_label = tk.Label(
            top, text="", bg=C["bg"], fg=C["text_dim"],
            font=("Segoe UI", 9, "italic"))
        self.status_label.pack(side="left", padx=12)

        # ===== Селектор ранга =====
        rank_frame = tk.Frame(top, bg=C["bg"])
        rank_frame.pack(side="left", padx=20)

        tk.Label(rank_frame, text="Ранг:", bg=C["bg"],
                 fg=C["text_dim"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))

        # Стилизуем Combobox
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Rank.TCombobox",
                        fieldbackground=C["card"], background=C["card"],
                        foreground=C["text"], arrowcolor=C["accent"],
                        borderwidth=0, relief="flat")
        style.map("Rank.TCombobox",
                  fieldbackground=[("readonly", C["card"])],
                  selectbackground=[("readonly", C["card"])],
                  selectforeground=[("readonly", C["text"])])

        bracket_labels = [f"{label}  ({mmr})" for _, label, mmr in BRACKETS]
        self._bracket_keys = [key for key, _, _ in BRACKETS]

        self.bracket_var = tk.StringVar(value=bracket_labels[0])  # "Все паблики"
        self.bracket_cb = ttk.Combobox(
            rank_frame, textvariable=self.bracket_var,
            values=bracket_labels, state="readonly",
            style="Rank.TCombobox", width=28,
            font=("Segoe UI", 9),
        )
        self.bracket_cb.pack(side="left")
        self.bracket_cb.bind("<<ComboboxSelected>>", self._on_bracket_change)

        # Кнопка нового драфта
        new_btn = tk.Label(top, text="🗑  Новый драфт",
                           bg=C["card"], fg=C["text"],
                           font=("Segoe UI", 9), cursor="hand2",
                           padx=14, pady=6)
        new_btn.pack(side="right")
        new_btn.bind("<Button-1>", lambda e: self._new_draft())
        new_btn.bind("<Enter>", lambda e: new_btn.config(bg=C["card_hover"]))
        new_btn.bind("<Leave>", lambda e: new_btn.config(bg=C["card"]))

        # Toggle topmost
        self.topmost = tk.BooleanVar(value=True)
        tk.Checkbutton(top, text="Поверх окон",
                       variable=self.topmost,
                       command=lambda: self.root.attributes("-topmost", self.topmost.get()),
                       bg=C["bg"], fg=C["text_dim"],
                       activebackground=C["bg"],
                       selectcolor=C["card"],
                       font=("Segoe UI", 9), bd=0
                       ).pack(side="right", padx=10)

        # ===== Команды (две колонки) =====
        teams = tk.Frame(self.root, bg=C["bg"])
        teams.pack(fill="both", expand=False, padx=12, pady=4)
        teams.grid_columnconfigure(0, weight=1, uniform="t")
        teams.grid_columnconfigure(1, weight=1, uniform="t")

        self.ally = TeamPanel(teams, "✅  ТВОЯ КОМАНДА", True, self.refresh_all)
        self.ally.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.enemy = TeamPanel(teams, "⚔  ВРАГИ", False, self.refresh_all)
        self.enemy.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # Разделитель
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x", padx=14, pady=8)

        # ===== Контейнер для рекомендаций / анализа =====
        self.bottom_container = tk.Frame(self.root, bg=C["bg"])
        self.bottom_container.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        self.recs = RoleRecommendations(self.bottom_container, self.recommender,
                                        self._pick_to_ally)
        self.analysis = MatchupAnalysis(self.bottom_container, self.recommender)
        # По умолчанию показываем рекомендации
        self.recs.pack(fill="both", expand=True)

        # ===== Подсказка =====
        tk.Label(self.root,
                 text="💡  Клик по «＋ поиск героя» → начни печатать → Enter "
                      "·  Клик по карточке героя добавит его в твою команду  "
                      "·  ✕ удаляет пик",
                 bg=C["bg"], fg=C["text_muted"],
                 font=("Segoe UI", 9, "italic")).pack(pady=(0, 10))

    def _start_auto_update(self):
        """Запустить проверку обновлений данных при старте"""
        def on_status(msg):
            # из фонового потока — переключаемся в UI thread
            self.root.after(0, lambda: self._set_status(msg, finished=False))

        def on_done(ok, msg):
            self.root.after(0, lambda: self._on_update_done(ok, msg))

        self._set_status("Проверка обновлений…", finished=False)
        self._updater = auto_update_if_needed(on_status=on_status, on_done=on_done)
        if self._updater is None:
            # Обновление не требуется
            self._set_status("Данные актуальны ✓", finished=True)
            self.root.after(3000, lambda: self._set_status("", finished=True))

    def _set_status(self, text: str, finished: bool):
        color = C["good"] if finished else C["mid"]
        try:
            self.status_label.config(text=text, fg=color)
        except tk.TclError:
            pass

    def _on_update_done(self, ok: bool, msg: str):
        if ok:
            self._set_status(f"✓ {msg}", finished=True)
            # Перезагрузить данные в рекомендаторе
            self.recommender._load_data()
            self.refresh_all()
            self.root.after(4000, lambda: self._set_status("", finished=True))
        else:
            self._set_status(f"✗ {msg}", finished=True)

    def _on_bracket_change(self, event=None):
        """Сменили ранг в дропдауне"""
        idx = self.bracket_cb.current()
        if 0 <= idx < len(self._bracket_keys):
            new_bracket = self._bracket_keys[idx]
            self.recommender.set_bracket(new_bracket)
            self.refresh_all()

    def _pick_to_ally(self, hero_id: int, hero_name: str):
        state = get_draft_state()
        if len(state.ally_picks) >= 5:
            messagebox.showinfo("Команда заполнена", "В твоей команде уже 5 героев.")
            return
        if hero_id in state.get_all_picked_heroes():
            return
        state.add_ally_pick(hero_id, hero_name)
        self.refresh_all()

    def _new_draft(self):
        if messagebox.askyesno("Новый драфт", "Очистить обе команды?"):
            reset_draft()
            self.refresh_all()

    def refresh_all(self):
        self.ally.refresh()
        self.enemy.refresh()

        state = get_draft_state()
        full = (len(state.ally_picks) == 5 and len(state.enemy_picks) == 5)

        if full:
            # Переключаемся на анализ
            self.recs.pack_forget()
            if not self.analysis.winfo_ismapped():
                self.analysis.pack(fill="both", expand=True)
            # Дадим время Canvas-у получить размеры, затем рефрешим
            self.root.after(50, self.analysis.refresh)
        else:
            # Рекомендации
            self.analysis.pack_forget()
            if not self.recs.winfo_ismapped():
                self.recs.pack(fill="both", expand=True)
            self.recs.refresh()

    def run(self):
        self.root.mainloop()


def main():
    DraftAssistantUI().run()


if __name__ == "__main__":
    main()
