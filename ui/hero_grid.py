"""
Compact hero grid — 36px icons, tight padding
"""
import tkinter as tk
from typing import Callable, Set
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from data.heroes_static import get_all_heroes, search_hero
from ui.theme import C, FONT, FONT_FALLBACK, get_hero_image, ROLE_COLORS

POSITIONS = ["Carry", "Mid", "Offlane", "Support", "Roaming"]
ICON_SIZE = 36


class HeroGrid(tk.Frame):
    def __init__(self, parent, on_select: Callable, excluded: Set[int]):
        super().__init__(parent, bg=C["bg_secondary"])
        self.on_select = on_select
        self.excluded = excluded
        self.target_team = "ally"
        self._search_var = None
        self._build()

    def _build(self):
        top_bar = tk.Frame(self, bg=C["bg_secondary"])
        top_bar.pack(fill="x", padx=4, pady=(4, 1))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._debounced_refresh())
        self._refresh_job = None

        entry = tk.Entry(top_bar, textvariable=self._search_var,
                         font=(FONT, 9), bg=C["card"], fg=C["text"],
                         insertbackground=C["accent"], relief="flat",
                         highlightthickness=1, highlightbackground=C["border"],
                         highlightcolor=C["accent"])
        entry.pack(side="left", fill="x", expand=True, ipady=2, padx=(0, 4))
        entry.insert(0, "Поиск...")
        self._is_placeholder = True
        entry.bind("<FocusIn>", self._on_focus_in)
        entry.bind("<FocusOut>", self._on_focus_out)

        self._ally_btn = tk.Label(top_bar, text="✅Свои", bg=C["accent"], fg="#ffffff",
                                   font=(FONT, 8, "bold"), padx=4, pady=1, cursor="hand2")
        self._ally_btn.pack(side="right", padx=1)

        self._enemy_btn = tk.Label(top_bar, text="⚔Враги", bg=C["card"], fg=C["text_secondary"],
                                    font=(FONT, 8, "bold"), padx=4, pady=1, cursor="hand2")
        self._enemy_btn.pack(side="right", padx=1)

        self._ally_btn.bind("<Button-1>", lambda e: self._set_team("ally"))
        self._enemy_btn.bind("<Button-1>", lambda e: self._set_team("enemy"))

        canvas_frame = tk.Frame(self, bg=C["bg_secondary"])
        canvas_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self._canvas = tk.Canvas(canvas_frame, bg=C["bg_secondary"],
                                  highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical",
                                  command=self._canvas.yview, width=8)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=C["bg_secondary"])
        self._canvas_window = self._canvas.create_window((0, 0), window=self._inner,
                                                          anchor="nw")
        self._inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._bind_mousewheel(self)

    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)
        for c in widget.winfo_children():
            self._bind_mousewheel(c)

    def _on_inner_configure(self, e):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self._canvas.itemconfig(self._canvas_window, width=e.width)

    def _on_mousewheel(self, e):
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _on_focus_in(self, _):
        if self._is_placeholder:
            self._search_var.set("")
            self._is_placeholder = False

    def _on_focus_out(self, _):
        if not self._search_var.get().strip():
            self._search_var.set("Поиск...")
            self._is_placeholder = True

    def _set_team(self, team):
        self.target_team = team
        if team == "ally":
            self._ally_btn.config(bg=C["accent"], fg="#ffffff")
            self._enemy_btn.config(bg=C["card"], fg=C["text_secondary"])
        else:
            self._enemy_btn.config(bg=C["enemy"], fg="#ffffff")
            self._ally_btn.config(bg=C["card"], fg=C["text_secondary"])

    def set_excluded(self, excluded):
        self.excluded = excluded

    def _debounced_refresh(self):
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
        self._refresh_job = self.after(200, self.refresh)

    def refresh(self):
        for w in self._inner.winfo_children():
            w.destroy()

        query = self._search_var.get().strip().lower() if not self._is_placeholder else ""
        all_h = get_all_heroes()

        if query:
            heroes = [h for h in search_hero(query) if h["id"] not in self.excluded]
            self._render_section(None, heroes)
        else:
            for pos in POSITIONS:
                role_heroes = [
                    {"id": hid, **h} for hid, h in all_h.items()
                    if pos in h.get("roles", []) and hid not in self.excluded
                ]
                role_heroes.sort(key=lambda x: x["localized_name"])
                if role_heroes:
                    self._render_section(pos, role_heroes)

        self._inner.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _render_section(self, role, heroes):
        if role:
            color = ROLE_COLORS.get(role, C["text_muted"])
            header = tk.Frame(self._inner, bg=C["bg_secondary"])
            header.pack(fill="x", pady=(4, 0), padx=2)
            tk.Label(header, text=f" {role}", bg=color, fg="#ffffff",
                     font=(FONT, 7, "bold"), padx=4, pady=0, anchor="w"
                     ).pack(side="left", fill="x", expand=True)
            tk.Label(header, text=str(len(heroes)), bg=C["bg_secondary"],
                     fg=C["text_muted"], font=(FONT, 7)).pack(side="right", padx=2)

        grid = tk.Frame(self._inner, bg=C["bg_secondary"])
        grid.pack(fill="x", padx=2)

        grid.update_idletasks()
        try:
            pw = grid.winfo_width() or self._canvas.winfo_width() or 500
            cols = max(1, pw // (ICON_SIZE + 4))
        except Exception:
            cols = 12

        for i, hero in enumerate(heroes):
            row, col = divmod(i, cols)
            self._render_cell(grid, hero, row, col)

    def _render_cell(self, parent, hero, row, col):
        cell = tk.Frame(parent, bg=C["card"], width=ICON_SIZE, height=ICON_SIZE,
                        highlightbackground=C["border"], highlightthickness=1,
                        cursor="hand2")
        cell.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
        cell.grid_propagate(False)

        img = get_hero_image(hero["id"], hero.get("localized_name", "?"),
                             ICON_SIZE - 2, hero.get("roles", []))
        lbl = tk.Label(cell, image=img, bg=C["card"], cursor="hand2")
        lbl.image = img
        lbl.pack(fill="both", expand=True, padx=0, pady=0)

        def on_enter(e):
            cell.configure(highlightbackground=C["accent"], highlightthickness=2)
            cell.configure(bg=C["card_hover"])
            lbl.configure(bg=C["card_hover"])

        def on_leave(e):
            cell.configure(highlightbackground=C["border"], highlightthickness=1)
            cell.configure(bg=C["card"])
            lbl.configure(bg=C["card"])

        for w in (cell, lbl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", lambda e: self.on_select(hero))
            w.bind("<MouseWheel>", self._on_mousewheel)
