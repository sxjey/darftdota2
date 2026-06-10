"""
Dota 2 Draft Assistant — Compact pink dark UI
2-column: hero grid (wide) | sidebar (teams + analysis + recs)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.draft_state import get_draft_state, reset_draft
from core.auto_updater import auto_update_if_needed
from scoring.recommender import HeroRecommender, HeroScore, BRACKETS
from scoring.position_assigner import assign_positions, get_priority_position, POSITIONS
from data.heroes_static import search_hero, get_all_heroes, get_hero_by_id
from ui.theme import C, FONT, POSITION_INFO, ROLE_COLORS, get_hero_image, score_color
from ui.hero_grid import HeroGrid
from ui.game_plan_window import GamePlanWindow


class TeamBar(tk.Frame):
    def __init__(self, parent, title, is_ally, on_change):
        super().__init__(parent, bg=C["panel"])
        self.is_ally = is_ally
        self.on_change = on_change
        self.accent = C["ally"] if is_ally else C["enemy"]
        self.accent_bg = C["ally_bg"] if is_ally else C["enemy_bg"]

        hdr = tk.Frame(self, bg=self.accent_bg)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title, bg=self.accent_bg, fg=self.accent,
                 font=(FONT, 9, "bold"), pady=2, padx=6, anchor="w").pack(side="left")
        self.count_lbl = tk.Label(hdr, text="0/5", bg=self.accent_bg,
                                  fg=C["text_secondary"], font=(FONT, 8))
        self.count_lbl.pack(side="right", padx=6)

        self.slots = tk.Frame(self, bg=C["panel"])
        self.slots.pack(fill="both", expand=True, padx=4, pady=2)
        self.refresh()

    def refresh(self):
        for w in self.slots.winfo_children():
            w.destroy()
        state = get_draft_state()
        picks = state.ally_picks if self.is_ally else state.enemy_picks
        overrides = state.ally_position_overrides if self.is_ally else {}
        assignment = assign_positions(picks, overrides=overrides)
        for pick in picks:
            pos = next((p for p, h in assignment.items()
                        if h and h["hero_id"] == pick.hero_id), "")
            is_ov = (self.is_ally and pick.hero_id in overrides)
            self._slot(pick.hero_id, pick.hero_name, pos, is_ov)
        self.count_lbl.config(text=f"{len(picks)}/5")

    def _slot(self, hero_id, hero_name, pos, is_ov):
        row = tk.Frame(self.slots, bg=C["card"], highlightbackground=C["border"],
                       highlightthickness=1)
        row.pack(fill="x", pady=1)

        img = get_hero_image(hero_id, hero_name, 22,
                             get_hero_by_id(hero_id).get("roles", []))
        lbl = tk.Label(row, image=img, bg=C["card"])
        lbl.image = img
        lbl.pack(side="left", padx=(3, 2), pady=1)

        tk.Label(row, text=hero_name, bg=C["card"], fg=C["text"],
                 font=(FONT, 8, "bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=2)

        if pos:
            pinfo = POSITION_INFO[pos]
            txt = f"📌{pinfo['label']}" if is_ov else pinfo["label"]
            badge = tk.Label(row, text=txt, bg=pinfo["color"], fg="#fff",
                             font=(FONT, 7, "bold"), padx=3, pady=0,
                             cursor="hand2" if self.is_ally else "")
            badge.pack(side="left", padx=1)
            if self.is_ally:
                badge.bind("<Button-1>", lambda e, hid=hero_id: self._popup_role(e, hid))
                badge.bind("<Enter>", lambda e, b=badge: b.config(bg=C["highlight"]))
                badge.bind("<Leave>", lambda e, b=badge, p=pos: b.config(bg=POSITION_INFO[p]["color"]))

        x = tk.Label(row, text="✕", bg=C["card"], fg=C["bad"],
                     font=(FONT, 8, "bold"), cursor="hand2", padx=4)
        x.pack(side="right")
        x.bind("<Button-1>", lambda e, hid=hero_id: self._remove(hid))
        x.bind("<Enter>", lambda e, l=x: l.config(bg=C["card_hover"]))
        x.bind("<Leave>", lambda e, l=x: l.config(bg=C["card"]))

    def _remove(self, hero_id):
        state = get_draft_state()
        state.push_undo()
        if self.is_ally:
            state.remove_ally_pick(hero_id)
        else:
            state.remove_enemy_pick(hero_id)
        self.on_change()

    def _change_role(self, hero_id, position):
        get_draft_state().set_position_override(hero_id, position)
        self.on_change()

    def _popup_role(self, event, hero_id):
        menu = tk.Menu(self, tearoff=0, bg=C["card"], fg=C["text"],
                       activebackground=C["accent"], activeforeground="white",
                       font=(FONT, 9), bd=0)
        for pos in POSITIONS:
            pinfo = POSITION_INFO[pos]
            menu.add_command(
                label=f"  {pinfo['icon']}  {pinfo['label']} — {pinfo['sub']}",
                command=lambda p=pos: self._change_role(hero_id, p))
        menu.add_separator()
        menu.add_command(label="  ↺  Авто",
                         command=lambda: self._change_role(hero_id, None))
        menu.post(event.x_root, event.y_root)


class BanBar(tk.Frame):
    def __init__(self, parent, on_change):
        super().__init__(parent, bg=C["panel"])
        self.on_change = on_change

        hdr = tk.Frame(self, bg=C["ban_bg"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="💀 Баны", bg=C["ban_bg"], fg=C["ban"],
                 font=(FONT, 9, "bold"), pady=2, padx=6, anchor="w").pack(side="left")
        add = tk.Label(hdr, text="＋", bg=C["ban_bg"], fg=C["ban"],
                       font=(FONT, 9, "bold"), cursor="hand2", padx=6)
        add.pack(side="right")
        add.bind("<Button-1>", lambda e: self._activate_ban_search())

        self.bans_frame = tk.Frame(self, bg=C["panel"])
        self.bans_frame.pack(fill="x", padx=4, pady=2)
        self.add_frame = tk.Frame(self, bg=C["panel"])
        self.add_frame.pack(fill="x", padx=4, pady=(0, 2))
        self.refresh()

    def refresh(self):
        for w in self.bans_frame.winfo_children():
            w.destroy()
        for w in self.add_frame.winfo_children():
            w.destroy()
        state = get_draft_state()
        for hero_id in state.ally_bans + state.enemy_bans:
            hero = get_hero_by_id(hero_id)
            img = get_hero_image(hero_id, hero.get("localized_name", "?"), 18,
                                 hero.get("roles", []))
            lbl = tk.Label(self.bans_frame, image=img, bg=C["card"],
                           highlightbackground=C["border"], highlightthickness=1,
                           cursor="hand2")
            lbl.image = img
            lbl.pack(side="left", padx=1, pady=1)
            lbl.bind("<Button-1>", lambda e, hid=hero_id: self._remove_ban(hid))
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(highlightbackground=C["bad"]))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(highlightbackground=C["border"]))

    def _remove_ban(self, hero_id):
        state = get_draft_state()
        state.push_undo()
        state.remove_ally_ban(hero_id) if hero_id in state.ally_bans else \
            state.remove_enemy_ban(hero_id)
        self.on_change()

    def _activate_ban_search(self):
        for w in self.add_frame.winfo_children():
            w.destroy()
        entry = tk.Entry(self.add_frame, font=(FONT, 8), bg=C["card"], fg=C["text"],
                         insertbackground=C["accent"], relief="flat",
                         highlightthickness=1, highlightbackground=C["ban"],
                         highlightcolor=C["accent"])
        entry.pack(fill="x", ipady=2, pady=1)
        entry.focus_set()
        self._ban_entry = entry
        self._ban_results = None
        entry.bind("<KeyRelease>", self._on_ban_type)
        entry.bind("<Escape>", lambda e: self._close_ban())

    def _on_ban_type(self, event):
        q = self._ban_entry.get().strip().lower()
        if not q:
            return
        results = [r for r in search_hero(q)[:6]
                   if r["id"] not in get_draft_state().get_all_picked_heroes()
                   and r["id"] not in get_draft_state().get_all_banned_heroes()]
        if self._ban_results:
            self._ban_results.destroy()
        if not results:
            return
        self._ban_results = tk.Frame(self.add_frame, bg=C["card"],
                                      highlightbackground=C["ban"], highlightthickness=1)
        self._ban_results.pack(fill="x")
        for r in results:
            lbl = tk.Label(self._ban_results, text=f"  {r['localized_name']}",
                           bg=C["card"], fg=C["text"], font=(FONT, 8),
                           anchor="w", cursor="hand2", pady=1)
            lbl.pack(fill="x")
            lbl.bind("<Button-1>", lambda e, hid=r["id"]: self._do_ban(hid))
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(bg=C["card_hover"]))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(bg=C["card"]))

    def _do_ban(self, hero_id):
        get_draft_state().push_undo()
        get_draft_state().add_ally_ban(hero_id)
        self._close_ban()
        self.on_change()

    def _close_ban(self):
        for w in self.add_frame.winfo_children():
            w.destroy()
        self.refresh()


class AnalysisBlock(tk.Frame):
    def __init__(self, parent, recommender):
        super().__init__(parent, bg=C["panel"])
        self.recommender = recommender

        hdr = tk.Frame(self, bg=C["panel"])
        hdr.pack(fill="x", padx=4, pady=(4, 1))
        tk.Label(hdr, text="📊 Анализ", bg=C["panel"], fg=C["accent"],
                 font=(FONT, 9, "bold")).pack(side="left")
        self.verdict_lbl = tk.Label(hdr, text="", bg=C["panel"],
                                    fg=C["text"], font=(FONT, 8, "bold"))
        self.verdict_lbl.pack(side="right")

        self.bar = tk.Canvas(self, height=14, bg=C["panel"], highlightthickness=0)
        self.bar.pack(fill="x", padx=4, pady=1)

        self.tags = tk.Frame(self, bg=C["panel"])
        self.tags.pack(fill="x", padx=4, pady=0)

        self.factors = tk.Frame(self, bg=C["panel"])
        self.factors.pack(fill="x", padx=4, pady=(0, 2))

    def refresh(self):
        self.bar.delete("all")
        self.verdict_lbl.config(text="")
        for w in self.tags.winfo_children():
            w.destroy()
        for w in self.factors.winfo_children():
            w.destroy()
        state = get_draft_state()
        if not state.ally_picks and not state.enemy_picks:
            self.bar.create_text(self.bar.winfo_width() / 2 or 200, 7,
                                text="Добавь героев", fill=C["text_muted"],
                                font=(FONT, 7, "italic"))
            return
        a = self.recommender.analyze_matchup(state)
        w = max(self.bar.winfo_width(), 100)
        h = 14
        self.bar.create_rectangle(0, 0, w, h, fill=C["card"], outline="")
        pct = a["advantage_pct"]
        aw = max(0, min(w, w * (50 + pct / 2) / 100))
        self.bar.create_rectangle(0, 0, aw, h, fill=C["ally"], outline="")
        self.bar.create_rectangle(aw, 0, w, h, fill=C["enemy"], outline="")
        self.bar.create_text(w / 2, h / 2,
                            text=f"{a['ally_total']:.0f} vs {a['enemy_total']:.0f}",
                            fill="white", font=(FONT, 7, "bold"))
        color = C["good"] if a["winner"] == "ally" else \
                C["bad"] if a["winner"] == "enemy" else C["mid"]
        self.verdict_lbl.config(text=a["verdict"], fg=color)
        comp = a.get("composition", {})
        if comp:
            phys, mag = comp.get("physical_pct", 0), comp.get("magical_pct", 0)
            tm = comp.get("timing", "balanced")
            tagdata = [("Phys", C["role_carry"]) if phys > 60 else
                       ("Magic", C["role_mid"]) if mag > 60 else ("Mixed", C["mid"]),
                       ("Early" if tm == "early" else "Late" if tm == "late"
                        else "Bal",
                        C["good"] if tm == "early" else C["role_carry"] if tm == "late"
                        else C["text_secondary"])]
            for txt, col in tagdata:
                tk.Label(self.tags, text=f" {txt} ", bg=col, fg="#fff",
                         font=(FONT, 7, "bold"), padx=2, pady=0).pack(side="left", padx=1)
        for f in a["key_factors"][:3]:
            tk.Label(self.factors, text=f"• {f}", bg=C["panel"],
                     fg=C["text_secondary"], font=(FONT, 7), anchor="w").pack(fill="x")


class LaneBlock(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["panel"])
        hdr = tk.Frame(self, bg=C["panel"])
        hdr.pack(fill="x", padx=4, pady=(4, 1))
        tk.Label(hdr, text="🗺 Лайны", bg=C["panel"], fg=C["accent"],
                 font=(FONT, 9, "bold")).pack(side="left")
        self.lanes = tk.Frame(self, bg=C["panel"])
        self.lanes.pack(fill="x", padx=4, pady=(0, 4))

    def refresh(self):
        for w in self.lanes.winfo_children():
            w.destroy()
        state = get_draft_state()
        asgn = assign_positions(state.ally_picks, overrides=state.ally_position_overrides)
        ov = state.ally_position_overrides
        for lane, pos in [("Top", "Offlane"), ("Mid", "Mid"),
                          ("Bot", "Carry"), ("Bot", "Support"), ("Roam", "Roaming")]:
            hero = asgn.get(pos)
            is_ov = hero and hero["hero_id"] in ov and ov[hero["hero_id"]] == pos
            self._row(lane, pos, hero, is_ov)

    def _row(self, lane, pos, hero, is_ov):
        pinfo = POSITION_INFO.get(pos, {})
        row = tk.Frame(self.lanes, bg=C["card"], highlightbackground=C["border"],
                       highlightthickness=1)
        row.pack(fill="x", pady=0)
        tk.Label(row, text=lane, bg=C["card"], fg=C["text"],
                 font=(FONT, 7, "bold"), width=5, anchor="w").pack(side="left", padx=2, pady=1)
        txt = f"📌{pinfo['label']}" if is_ov else pinfo["label"]
        tk.Label(row, text=txt, bg=pinfo["color"], fg="#fff",
                 font=(FONT, 7, "bold"), padx=2, pady=0).pack(side="left", padx=1, pady=1)
        if hero:
            img = get_hero_image(hero["hero_id"], hero["name"], 16,
                                 get_hero_by_id(hero["hero_id"]).get("roles", []))
            lbl = tk.Label(row, image=img, bg=C["card"])
            lbl.image = img
            lbl.pack(side="left", padx=1, pady=1)
            tk.Label(row, text=hero["name"] + ("✋" if is_ov else ""),
                     bg=C["card"], fg=C["text"], font=(FONT, 7), anchor="w"
                     ).pack(side="left", padx=1, fill="x", expand=True)
        else:
            tk.Label(row, text="???", bg=C["card"], fg=C["bad"],
                     font=(FONT, 7, "italic"), anchor="w"
                     ).pack(side="left", padx=1, fill="x", expand=True)


class RecsBlock(tk.Frame):
    def __init__(self, parent, recommender, on_pick):
        super().__init__(parent, bg=C["panel"])
        self.recommender = recommender
        self.on_pick = on_pick

        hdr = tk.Frame(self, bg=C["panel"])
        hdr.pack(fill="x", padx=4, pady=(4, 1))
        tk.Label(hdr, text="🏆 Реки", bg=C["panel"], fg=C["accent"],
                 font=(FONT, 9, "bold")).pack(side="left")
        self.pri_lbl = tk.Label(hdr, text="", bg=C["panel"],
                                fg=C["highlight"], font=(FONT, 7, "italic"))
        self.pri_lbl.pack(side="right")
        self.content = tk.Frame(self, bg=C["panel"])
        self.content.pack(fill="both", expand=True, padx=2, pady=1)

    def refresh(self):
        for w in self.content.winfo_children():
            w.destroy()
        state = get_draft_state()
        by_role = self.recommender.get_recommendations_by_role(state, top_per_role=3)
        pri = get_priority_position(state.ally_picks)
        self.pri_lbl.config(text=f"Нужен: {POSITION_INFO[pri]['label']}" if pri
                           else "Все заняты")
        for col, role in enumerate(POSITIONS):
            self.content.grid_columnconfigure(col, weight=1, uniform="r")
            is_pri = role == pri
            color = POSITION_INFO[role]["color"]
            cf = tk.Frame(self.content, bg=C["card"],
                          highlightbackground=C["highlight"] if is_pri else C["border"],
                          highlightthickness=2 if is_pri else 1)
            cf.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
            hbg = C["highlight"] if is_pri else color
            hfg = "#1a1a1a" if is_pri else "#ffffff"
            tk.Label(cf, text=f"{POSITION_INFO[role]['icon']}{POSITION_INFO[role]['label']}",
                     bg=hbg, fg=hfg, font=(FONT, 7, "bold"), pady=1).pack(fill="x")
            heroes = by_role.get(role, [])
            if not heroes:
                tk.Label(cf, text="—", bg=C["card"], fg=C["text_muted"],
                         font=(FONT, 7), pady=2).pack()
                continue
            for i, h in enumerate(heroes):
                self._row(cf, h, i + 1)

    def _row(self, parent, hero, rank):
        row = tk.Frame(parent, bg=C["card_hover"], cursor="hand2")
        row.pack(fill="x", padx=1, pady=0)
        badges = {1: "🥇", 2: "🥈", 3: "🥉"}
        img = get_hero_image(hero.hero_id, hero.hero_name, 18, hero.roles)
        lbl = tk.Label(row, image=img, bg=C["card_hover"])
        lbl.image = img
        lbl.pack(side="left", padx=1, pady=1)
        tk.Label(row, text=f"{badges.get(rank, '•')} {hero.hero_name}",
                 bg=C["card_hover"], fg=C["text"], font=(FONT, 7, "bold"),
                 anchor="w").pack(side="left", fill="x", expand=True, padx=1)
        tk.Label(row, text=f"{hero.total_score:.0f}", bg=C["card_hover"],
                 fg=score_color(hero.total_score), font=(FONT, 7, "bold"),
                 padx=2).pack(side="right")

        def on_enter(e):
            row.configure(bg=C["card_active"])
            for w2 in row.winfo_children():
                try: w2.configure(bg=C["card_active"])
                except: pass

        def on_leave(e):
            row.configure(bg=C["card_hover"])
            for w2 in row.winfo_children():
                try: w2.configure(bg=C["card_hover"])
                except: pass

        for w2 in [row, lbl] + list(row.winfo_children()):
            w2.bind("<Enter>", on_enter)
            w2.bind("<Leave>", on_leave)
            w2.bind("<Button-1>", lambda e: self.on_pick(hero.hero_id, hero.hero_name))


class DraftAssistantUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dota 2 Draft Assistant")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.root.configure(bg=C["bg"])
        self.root.attributes("-topmost", True)

        icon_path = Path(__file__).parent.parent / "assets" / "app_icon.ico"
        if icon_path.exists():
            try: self.root.iconbitmap(str(icon_path))
            except: pass

        self.recommender = HeroRecommender()
        self._updater = None
        self._pending_refresh = None
        self._build()
        self._schedule_refresh()
        self.root.after(500, self._start_auto_update)

    def _build(self):
        toolbar = tk.Frame(self.root, bg=C["bg"])
        toolbar.pack(fill="x", padx=6, pady=(4, 2))

        tk.Label(toolbar, text="DRAFT ASSISTANT", bg=C["bg"], fg=C["accent"],
                 font=(FONT, 11, "bold")).pack(side="left")

        rank_f = tk.Frame(toolbar, bg=C["bg"])
        rank_f.pack(side="left", padx=10)
        tk.Label(rank_f, text="Ранг:", bg=C["bg"], fg=C["text_secondary"],
                 font=(FONT, 8)).pack(side="left", padx=(0, 2))
        style = ttk.Style()
        style.configure("Rank.TCombobox", fieldbackground=C["card"],
                         background=C["card"], foreground=C["text"],
                         arrowcolor=C["accent"], borderwidth=0)
        bracket_labels = [f"{l} ({m})" for _, l, m in BRACKETS]
        self._bk = [k for k, _, _ in BRACKETS]
        self.bracket_var = tk.StringVar(value=bracket_labels[0])
        self.bracket_cb = ttk.Combobox(rank_f, textvariable=self.bracket_var,
                                        values=bracket_labels, state="readonly",
                                        style="Rank.TCombobox", width=22, font=(FONT, 8))
        self.bracket_cb.pack(side="left")
        self.bracket_cb.bind("<<ComboboxSelected>>", self._on_bracket_change)

        self.status_lbl = tk.Label(toolbar, text="", bg=C["bg"], fg=C["text_secondary"],
                                   font=(FONT, 7, "italic"))
        self.status_lbl.pack(side="left", padx=6)

        for txt, cmd, fg in [("↶ Undo", self._undo, C["text"]),
                              ("🗑 Новый", self._new_draft, C["text"]),
                              ("Далее →", self._open_game_plan, C["accent"])]:
            b = tk.Label(toolbar, text=txt, bg=C["card"], fg=fg,
                         font=(FONT, 8, "bold" if "Далее" in txt else "normal"),
                         cursor="hand2", padx=8 if "Далее" in txt else 6, pady=2)
            b.pack(side="right", padx=1)
            b.bind("<Button-1>", lambda e, c=cmd: c())
            b.bind("<Enter>", lambda e, l=b: l.config(bg=C["card_hover"]))
            b.bind("<Leave>", lambda e, l=b: l.config(bg=C["card"]))

        self.topmost = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar, text="Поверх", variable=self.topmost,
                       command=lambda: self.root.attributes("-topmost", self.topmost.get()),
                       bg=C["bg"], fg=C["text_secondary"],
                       activebackground=C["bg"], selectcolor=C["card"],
                       font=(FONT, 8), bd=0).pack(side="right", padx=4)
        self.root.bind("<Control-z>", lambda e: self._undo())

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=4, pady=2)
        body.grid_columnconfigure(0, weight=3, uniform="col")
        body.grid_columnconfigure(1, weight=2, uniform="col")
        body.grid_rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=C["bg_secondary"],
                        highlightbackground=C["border"], highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        self.hero_grid = HeroGrid(left, on_select=self._on_grid_select, excluded=set())
        self.hero_grid.pack(fill="both", expand=True)

        right = tk.Frame(body, bg=C["bg"])
        right.grid(row=0, column=1, sticky="nsew", padx=(2, 0))
        right.grid_rowconfigure(4, weight=1)

        self.ally = TeamBar(right, "✅ Свои", True, self._schedule_refresh)
        self.ally.grid(row=0, column=0, sticky="ew", pady=(0, 2))

        self.enemy = TeamBar(right, "⚔ Враги", False, self._schedule_refresh)
        self.enemy.grid(row=1, column=0, sticky="ew", pady=(0, 2))

        self.bans = BanBar(right, self._schedule_refresh)
        self.bans.grid(row=2, column=0, sticky="ew", pady=(0, 2))

        self.analysis = AnalysisBlock(right, self.recommender)
        self.analysis.grid(row=3, column=0, sticky="ew", pady=(0, 2))

        self.lane_map = LaneBlock(right)
        self.lane_map.grid(row=4, column=0, sticky="ew", pady=(0, 2))

        self.recs = RecsBlock(right, self.recommender, self._pick_to_ally)
        self.recs.grid(row=5, column=0, sticky="nsew")

        tk.Label(self.root,
                 text="💡 Клик → добавить · Badge роли → сменить линию · Ctrl+Z undo",
                 bg=C["bg"], fg=C["text_muted"], font=(FONT, 7, "italic")
                 ).pack(pady=(0, 4))

    def _on_grid_select(self, hero):
        state = get_draft_state()
        state.push_undo()
        team = self.hero_grid.target_team
        hid, name = hero["id"], hero["localized_name"]
        if hid in state.get_all_picked_heroes():
            return
        if team == "ally" and len(state.ally_picks) < 5:
            state.add_ally_pick(hid, name)
        elif team == "enemy" and len(state.enemy_picks) < 5:
            state.add_enemy_pick(hid, name)
        elif len(state.ally_picks) < 5:
            state.add_ally_pick(hid, name)
        elif len(state.enemy_picks) < 5:
            state.add_enemy_pick(hid, name)
        self._schedule_refresh()

    def _pick_to_ally(self, hero_id, hero_name):
        state = get_draft_state()
        if len(state.ally_picks) >= 5:
            messagebox.showinfo("Full", "5 heroes already")
            return
        if hero_id in state.get_all_picked_heroes():
            return
        state.push_undo()
        state.add_ally_pick(hero_id, hero_name)
        self._schedule_refresh()

    def _schedule_refresh(self, *_):
        if self._pending_refresh:
            self.root.after_cancel(self._pending_refresh)
        self._pending_refresh = self.root.after(30, self._do_refresh)

    def _do_refresh(self):
        self._pending_refresh = None
        state = get_draft_state()
        self.ally.refresh()
        self.enemy.refresh()
        self.bans.refresh()
        self.hero_grid.set_excluded(state.get_all_picked_heroes() | state.get_all_banned_heroes())
        self.hero_grid.refresh()
        self.analysis.refresh()
        self.lane_map.refresh()
        self.recs.refresh()

    def _undo(self):
        if get_draft_state().undo():
            self._schedule_refresh()

    def _new_draft(self):
        if messagebox.askyesno("Новый драфт", "Очистить?"):
            reset_draft()
            self._schedule_refresh()

    def _open_game_plan(self):
        state = get_draft_state()
        if not state.ally_picks:
            messagebox.showinfo("Нет пиков", "Добавь хотя бы одного союзника")
            return
        GamePlanWindow(self.root, self.recommender, on_back=lambda: self.root.deiconify())

    def _on_bracket_change(self, event=None):
        idx = self.bracket_cb.current()
        if 0 <= idx < len(self._bk):
            self.recommender.set_bracket(self._bk[idx])
            self._schedule_refresh()

    def _start_auto_update(self):
        def on_status(msg):
            self.root.after(0, lambda: self._set_status(msg, False))

        def on_done(ok, msg):
            self.root.after(0, lambda: self._on_update_done(ok, msg))

        self._set_status("Проверка обновлений...", False)
        self._updater = auto_update_if_needed(on_status=on_status, on_done=on_done)
        if self._updater is None:
            self._set_status("Актуально", True)
            self.root.after(3000, lambda: self._set_status("", True))

    def _set_status(self, text, finished):
        try:
            self.status_lbl.config(text=text, fg=C["good"] if finished else C["mid"])
        except:
            pass

    def _on_update_done(self, ok, msg):
        if ok:
            self._set_status(f"OK {msg}", True)
            self.recommender._load_data()
            self._schedule_refresh()
            self.root.after(4000, lambda: self._set_status("", True))
        else:
            self._set_status(f"ERR {msg}", True)

    def run(self):
        self.root.mainloop()


def main():
    DraftAssistantUI().run()


if __name__ == "__main__":
    main()
