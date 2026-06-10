"""
Окно 2 — Игровой план.
Выбираешь за кого играешь → полный разбор: контры, айтемы, кого фокусить.
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from core.draft_state import get_draft_state, DraftState
from scoring.recommender import HeroRecommender
from scoring.game_plan import generate_game_plan, GamePlan, CounterInfo
from data.heroes_static import get_hero_by_id
from ui.theme import C, FONT, POSITION_INFO, ROLE_COLORS, get_hero_image, score_color


class GamePlanWindow(tk.Toplevel):
    def __init__(self, parent, recommender: HeroRecommender, on_back: Callable):
        super().__init__(parent)
        self.recommender = recommender
        self.on_back = on_back
        self._selected_hero_id = None
        self._plan: Optional[GamePlan] = None

        self.title("Dota 2 — Игровой план")
        self.geometry("1050x800")
        self.minsize(900, 650)
        self.configure(bg=C["bg"])
        self.attributes("-topmost", True)

        icon_path = None
        from pathlib import Path
        p = Path(__file__).parent.parent / "assets" / "app_icon.ico"
        if p.exists():
            try: self.iconbitmap(str(p))
            except: pass

        self._build()
        self._show_hero_select()

    def _build(self):
        self.header = tk.Frame(self, bg=C["bg"])
        self.header.pack(fill="x", padx=12, pady=(8, 4))

        self.title_lbl = tk.Label(self.header, text="🎮 ИГРОВОЙ ПЛАН",
                                   bg=C["bg"], fg=C["accent"],
                                   font=(FONT, 14, "bold"))
        self.title_lbl.pack(side="left")

        self.back_btn = tk.Label(self.header, text="← Назад к драфту",
                                  bg=C["card"], fg=C["text"],
                                  font=(FONT, 10), cursor="hand2", padx=10, pady=4)
        self.back_btn.pack(side="right", padx=4)
        self.back_btn.bind("<Button-1>", lambda e: self._go_back())
        self.back_btn.bind("<Enter>", lambda e, l=self.back_btn: l.config(bg=C["card_hover"]))
        self.back_btn.bind("<Leave>", lambda e, l=self.back_btn: l.config(bg=C["card"]))

        self.content = tk.Frame(self, bg=C["bg"])
        self.content.pack(fill="both", expand=True, padx=12, pady=4)

    def _go_back(self):
        self.on_back()
        self.destroy()

    def _show_hero_select(self):
        for w in self.content.winfo_children():
            w.destroy()

        state = get_draft_state()
        if not state.ally_picks:
            tk.Label(self.content, text="Нет союзных пиков — вернись к драфту",
                     bg=C["bg"], fg=C["text_muted"], font=(FONT, 12)).pack(pady=40)
            return

        tk.Label(self.content, text="Выбери за кого ты играешь:",
                 bg=C["bg"], fg=C["text"], font=(FONT, 12, "bold")).pack(pady=(10, 8))

        grid = tk.Frame(self.content, bg=C["bg"])
        grid.pack(pady=8)

        for i, pick in enumerate(state.ally_picks):
            hero = get_hero_by_id(pick.hero_id)
            roles = hero.get("roles", []) if hero else []
            self._hero_choice(grid, pick.hero_id, pick.hero_name, roles, i)

    def _hero_choice(self, parent, hero_id, hero_name, roles, idx):
        card = tk.Frame(parent, bg=C["card"], highlightbackground=C["border"],
                        highlightthickness=2, cursor="hand2")
        card.grid(row=0, column=idx, padx=8, pady=4)

        img = get_hero_image(hero_id, hero_name, 52, roles)
        lbl = tk.Label(card, image=img, bg=C["card"])
        lbl.image = img
        lbl.pack(padx=8, pady=(8, 2))

        tk.Label(card, text=hero_name, bg=C["card"], fg=C["text"],
                 font=(FONT, 11, "bold")).pack()
        if roles:
            role_txt = " · ".join(roles)
            role_col = ROLE_COLORS.get(roles[0], C["accent"])
            tk.Label(card, text=role_txt, bg=C["card"], fg=role_col,
                     font=(FONT, 9)).pack(pady=(0, 6))

        def on_enter(e):
            card.configure(highlightbackground=C["accent"])
            for cw in card.winfo_children():
                try: cw.configure(bg=C["card_hover"])
                except: pass

        def on_leave(e):
            card.configure(highlightbackground=C["border"])
            for cw in card.winfo_children():
                try: cw.configure(bg=C["card"])
                except: pass

        def on_click(e):
            self._selected_hero_id = hero_id
            self._generate_and_show()

        for w in [card, lbl] + list(card.winfo_children()):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

    def _generate_and_show(self):
        state = get_draft_state()
        self._plan = generate_game_plan(self._selected_hero_id, state, self.recommender)
        self._show_plan()

    def _show_plan(self):
        for w in self.content.winfo_children():
            w.destroy()
        plan = self._plan
        if not plan:
            return

        top = tk.Frame(self.content, bg=C["bg"])
        top.pack(fill="x", pady=(0, 6))

        hero = get_hero_by_id(plan.my_hero_id)
        roles = hero.get("roles", []) if hero else []
        img = get_hero_image(plan.my_hero_id, plan.my_hero_name, 40, roles)
        lbl = tk.Label(top, image=img, bg=C["bg"])
        lbl.image = img
        lbl.pack(side="left", padx=(0, 8))

        info_f = tk.Frame(top, bg=C["bg"])
        info_f.pack(side="left", fill="y")
        tk.Label(info_f, text=plan.my_hero_name, bg=C["bg"], fg=C["accent"],
                 font=(FONT, 16, "bold")).pack(anchor="w")
        role_txt = " · ".join(plan.my_roles) if plan.my_roles else ""
        if role_txt:
            tk.Label(info_f, text=role_txt, bg=C["bg"], fg=C["text_secondary"],
                     font=(FONT, 10)).pack(anchor="w")
        if plan.my_note:
            tk.Label(info_f, text=plan.my_note, bg=C["bg"], fg=C["text_muted"],
                     font=(FONT, 9, "italic"), wraplength=500, justify="left"
                     ).pack(anchor="w")

        tk.Label(top, text=f"Винрейт: {plan.my_winrate:.1f}%", bg=C["bg"],
                 fg=score_color(plan.my_winrate), font=(FONT, 11, "bold")).pack(side="right", padx=8)

        change_btn = tk.Label(top, text="Сменить героя", bg=C["card"], fg=C["text_secondary"],
                              font=(FONT, 9), cursor="hand2", padx=8, pady=3)
        change_btn.pack(side="right", padx=4)
        change_btn.bind("<Button-1>", lambda e: self._show_hero_select())
        change_btn.bind("<Enter>", lambda e, l=change_btn: l.config(bg=C["card_hover"]))
        change_btn.bind("<Leave>", lambda e, l=change_btn: l.config(bg=C["card"]))

        body = tk.Frame(self.content, bg=C["bg"])
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1, uniform="c")
        body.grid_columnconfigure(1, weight=1, uniform="c")
        body.grid_rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=C["panel"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        left_scroll = tk.Canvas(left, bg=C["panel"], highlightthickness=0, bd=0)
        left_sb = tk.Scrollbar(left, orient="vertical", command=left_scroll.yview, width=8)
        left_inner = tk.Frame(left_scroll, bg=C["panel"])
        left_inner.bind("<Configure>", lambda e: left_scroll.configure(scrollregion=left_scroll.bbox("all")))
        left_scroll.create_window((0, 0), window=left_inner, anchor="nw")
        left_scroll.configure(yscrollcommand=left_sb.set)
        left_sb.pack(side="right", fill="y")
        left_scroll.pack(side="left", fill="both", expand=True)
        left_scroll.bind("<Configure>", lambda e: left_scroll.itemconfig("all", width=e.width))
        for w in [left_scroll, left_inner]:
            w.bind("<MouseWheel>", lambda e, c=left_scroll: c.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        right = tk.Frame(body, bg=C["panel"])
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        right_scroll = tk.Canvas(right, bg=C["panel"], highlightthickness=0, bd=0)
        right_sb = tk.Scrollbar(right, orient="vertical", command=right_scroll.yview, width=8)
        right_inner = tk.Frame(right_scroll, bg=C["panel"])
        right_inner.bind("<Configure>", lambda e: right_scroll.configure(scrollregion=right_scroll.bbox("all")))
        right_scroll.create_window((0, 0), window=right_inner, anchor="nw")
        right_scroll.configure(yscrollcommand=right_sb.set)
        right_sb.pack(side="right", fill="y")
        right_scroll.pack(side="left", fill="both", expand=True)
        right_scroll.bind("<Configure>", lambda e: right_scroll.itemconfig("all", width=e.width))
        for w in [right_scroll, right_inner]:
            w.bind("<MouseWheel>", lambda e, c=right_scroll: c.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._section(left_inner, "⚔ Кого ты контришь", C["good"])
        if plan.i_counter:
            for ci in plan.i_counter:
                self._counter_row(left_inner, ci, C["good"])
        else:
            tk.Label(left_inner, text="  Нет ярких контрпиков против врагов",
                     bg=C["panel"], fg=C["text_muted"], font=(FONT, 9, "italic")
                     ).pack(fill="x", padx=8, pady=2)

        self._section(left_inner, "⚠ Кто контрит тебя", C["bad"])
        if plan.counter_me:
            for ci in plan.counter_me:
                self._counter_row(left_inner, ci, C["bad"])
        else:
            tk.Label(left_inner, text="  Нет серьёзных контрпиков у врагов",
                     bg=C["panel"], fg=C["good"], font=(FONT, 9, "italic")
                     ).pack(fill="x", padx=8, pady=2)

        self._section(left_inner, "💙 Синергия с союзниками", C["ally"])
        if plan.synergy_with:
            for s in plan.synergy_with:
                self._synergy_row(left_inner, s)
        else:
            tk.Label(left_inner, text="  Нет особых синергий",
                     bg=C["panel"], fg=C["text_muted"], font=(FONT, 9, "italic")
                     ).pack(fill="x", padx=8, pady=2)

        self._section(left_inner, "🗺 Совет по лайну", C["accent"])
        tk.Label(left_inner, text=plan.lane_advice, bg=C["panel"], fg=C["text"],
                 font=(FONT, 10), wraplength=420, justify="left"
                 ).pack(fill="x", padx=8, pady=4)

        self._section(left_inner, "⚔ Совет по тимфайту", C["enemy"])
        tk.Label(left_inner, text=plan.teamfight_advice, bg=C["panel"], fg=C["text"],
                 font=(FONT, 10), wraplength=420, justify="left"
                 ).pack(fill="x", padx=8, pady=4)

        self._section(right_inner, "🎯 Кого фокусить в драках", C["accent"])
        if plan.focus_targets:
            for ft in plan.focus_targets:
                self._target_row(right_inner, ft, "focus")
        else:
            tk.Label(right_inner, text="  Нет данных",
                     bg=C["panel"], fg=C["text_muted"], font=(FONT, 9)).pack(padx=8, pady=2)

        self._section(right_inner, "🛡 От кого защищаться", C["bad"])
        if plan.protect_from:
            for pf in plan.protect_from:
                self._target_row(right_inner, pf, "protect")
        else:
            tk.Label(right_inner, text="  Нет особых угроз",
                     bg=C["panel"], fg=C["good"], font=(FONT, 9)).pack(padx=8, pady=2)

        self._section(right_inner, "📊 Состав команд", C["mid"])
        comp_f = tk.Frame(right_inner, bg=C["panel"])
        comp_f.pack(fill="x", padx=8, pady=4)
        tk.Label(comp_f, text="Враги:", bg=C["panel"], fg=C["enemy"],
                 font=(FONT, 10, "bold")).pack(anchor="w")
        self._comp_bar(comp_f, plan.enemy_phys_pct, plan.enemy_magic_pct)
        tk.Label(comp_f, text=f"Тайминг: {plan.enemy_timing}", bg=C["panel"],
                 fg=C["text_secondary"], font=(FONT, 9)).pack(anchor="w", pady=(2, 6))
        tk.Label(comp_f, text="Свои:", bg=C["panel"], fg=C["ally"],
                 font=(FONT, 10, "bold")).pack(anchor="w")
        self._comp_bar(comp_f, plan.ally_phys_pct, plan.ally_magic_pct)
        tk.Label(comp_f, text=f"Тайминг: {plan.ally_timing}", bg=C["panel"],
                 fg=C["text_secondary"], font=(FONT, 9)).pack(anchor="w", pady=(2, 4))

        self._section(right_inner, "🎒 Что собирать", C["ban"])
        if plan.items:
            for item in plan.items:
                self._item_row(right_inner, item)
        else:
            tk.Label(right_inner, text="  Нет особых рекомендаций",
                     bg=C["panel"], fg=C["text_muted"], font=(FONT, 9)).pack(padx=8, pady=2)

    def _section(self, parent, title, color):
        f = tk.Frame(parent, bg=C["panel"])
        f.pack(fill="x", padx=6, pady=(10, 2))
        tk.Frame(f, bg=color, height=2).pack(fill="x", pady=(0, 3))
        tk.Label(f, text=title, bg=C["panel"], fg=color,
                 font=(FONT, 11, "bold")).pack(anchor="w")

    def _counter_row(self, parent, ci: CounterInfo, color):
        row = tk.Frame(parent, bg=C["panel"])
        row.pack(fill="x", padx=8, pady=2)
        hero = get_hero_by_id(ci.hero_id)
        roles = hero.get("roles", []) if hero else []
        img = get_hero_image(ci.hero_id, ci.hero_name, 24, roles)
        lbl = tk.Label(row, image=img, bg=C["panel"])
        lbl.image = img
        lbl.pack(side="left", padx=(0, 6))
        tk.Label(row, text=ci.hero_name, bg=C["panel"], fg=C["text"],
                 font=(FONT, 10, "bold"), anchor="w").pack(side="left")
        wr_color = C["good"] if ci.winrate_vs > 52 else C["bad"] if ci.winrate_vs < 48 else C["mid"]
        tk.Label(row, text=f"{ci.winrate_vs:.1f}%", bg=C["panel"], fg=wr_color,
                 font=(FONT, 10, "bold")).pack(side="right", padx=4)
        if ci.games_played > 0:
            tk.Label(row, text=f"({ci.games_played} игр)", bg=C["panel"],
                     fg=C["text_muted"], font=(FONT, 8)).pack(side="right")

    def _synergy_row(self, parent, s: dict):
        row = tk.Frame(parent, bg=C["panel"])
        row.pack(fill="x", padx=8, pady=2)
        hero = get_hero_by_id(s["hero_id"])
        roles = hero.get("roles", []) if hero else []
        img = get_hero_image(s["hero_id"], s["name"], 24, roles)
        lbl = tk.Label(row, image=img, bg=C["panel"])
        lbl.image = img
        lbl.pack(side="left", padx=(0, 6))
        tk.Label(row, text=s["name"], bg=C["panel"], fg=C["text"],
                 font=(FONT, 10, "bold"), anchor="w").pack(side="left")
        if s["synergy_bonus"] > 0:
            tk.Label(row, text=f"+{s['synergy_bonus']}", bg=C["panel"], fg=C["ally"],
                     font=(FONT, 10, "bold")).pack(side="right", padx=4)
        if s["role_overlap"] > 0:
            tk.Label(row, text=f"пересечение ролей", bg=C["panel"], fg=C["mid"],
                     font=(FONT, 8)).pack(side="right")

    def _target_row(self, parent, t: dict, mode: str):
        row = tk.Frame(parent, bg=C["panel"])
        row.pack(fill="x", padx=8, pady=2)
        hero = get_hero_by_id(t["hero_id"])
        roles = hero.get("roles", []) if hero else []
        img = get_hero_image(t["hero_id"], t["name"], 24, roles)
        lbl = tk.Label(row, image=img, bg=C["panel"])
        lbl.image = img
        lbl.pack(side="left", padx=(0, 6))

        priority_val = t.get("priority", t.get("danger", 0))
        if mode == "focus":
            stars = "🔴" * min(priority_val, 5)
        else:
            stars = "⚠" * min(priority_val, 5)
        tk.Label(row, text=f"{t['name']} {stars}", bg=C["panel"], fg=C["text"],
                 font=(FONT, 10, "bold"), anchor="w").pack(side="left")

        reason_txt = ", ".join(t["reasons"][:2])
        tk.Label(row, text=reason_txt, bg=C["panel"], fg=C["text_secondary"],
                 font=(FONT, 8), anchor="w", wraplength=300, justify="left"
                 ).pack(side="left", fill="x", expand=True, padx=4)

    def _comp_bar(self, parent, phys_pct, mag_pct):
        bar = tk.Canvas(parent, height=16, bg=C["card"], highlightthickness=0, bd=0)
        bar.pack(fill="x", pady=2)

        def draw():
            w = bar.winfo_width() or 400
            bar.create_rectangle(0, 0, w, 16, fill=C["card"], outline="")
            pw = w * phys_pct / 100
            bar.create_rectangle(0, 0, pw, 16, fill=C["role_carry"], outline="")
            bar.create_rectangle(pw, 0, w, 16, fill=C["role_mid"], outline="")
            bar.create_text(w / 2, 8,
                           text=f"Физ {phys_pct}%  |  Маг {mag_pct}%",
                           fill="white", font=(FONT, 8, "bold"))

        bar.bind("<Configure>", lambda e: draw())
        bar.after(50, draw)

    def _item_row(self, parent, item: dict):
        row = tk.Frame(parent, bg=C["card"], highlightbackground=C["border"],
                       highlightthickness=1)
        row.pack(fill="x", padx=6, pady=2)

        prio_colors = {5: C["bad"], 4: "#ff8844", 3: C["mid"], 2: C["good"], 1: C["text_muted"]}
        prio_lbl = {5: "МАСТ", 4: "НАДО", 3: "ХОР", 2: "ОК", 1: "ЛАТ"}
        p = item.get("priority", 1)
        p_col = prio_colors.get(p, C["text_muted"])
        p_txt = prio_lbl.get(p, "??")

        tk.Label(row, text=f" {item['icon']} ", bg=C["panel"], fg=p_col,
                 font=(FONT, 14)).pack(side="left", padx=2)

        info = tk.Frame(row, bg=C["card"])
        info.pack(side="left", fill="x", expand=True, padx=4, pady=3)
        tk.Label(info, text=item["name"], bg=C["card"], fg=C["text"],
                 font=(FONT, 10, "bold"), anchor="w").pack(fill="x")
        tk.Label(info, text=item["reason"], bg=C["card"], fg=C["text_secondary"],
                 font=(FONT, 9), anchor="w", wraplength=300, justify="left").pack(fill="x")

        tk.Label(row, text=f"{p_txt}\n{item['cost']}g", bg=C["card"], fg=p_col,
                 font=(FONT, 8, "bold"), padx=6, pady=2, justify="center").pack(side="right")
