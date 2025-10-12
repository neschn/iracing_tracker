"""
ui.py - Interface utilisateur Tkinter
"""

import tkinter as tk
from tkinter import scrolledtext 
from tkinter import font as tkfont
from tkinter import ttk
from datetime import datetime
import queue as _q  # pour attraper queue.Empty proprement

# -----------------------
# Paramètres faciles à éditer
# -----------------------
WINDOW_TITLE = "iRacing Tracker"            # Titre de la fenêtre principale
WINDOW_GEOMETRY = "1600x1000"               # Taille initiale (largeur x hauteur)
MIN_WIDTH = 900                             # Largeur minimale de la fenêtre
MIN_HEIGHT = 550                            # Hauteur minimale de la fenêtre

# --- Thème / Apparence ---
COLOR_BG_MAIN = "#f0f0f0"                 # Couleur de fond générale (gris clair)
COLOR_TEXT = "black"                        # Couleur de texte par défaut
COLOR_CONTROL_FG = "black"                  # Couleur du texte des contrôles
COLOR_BANNER_BG = "#f0f0f0"               # Fond de la bannière supérieure
COLOR_BANNER_TEXT = "#0d47a1"             # Couleur du texte de la bannière
COLOR_DEBUG_TEXT_BG = "#f0f0f0"           # Fond de la zone Debug
COLOR_LOG_TEXT_BG = "#f0f0f0"             # Fond de la zone Logs
COLOR_SEPARATOR = "#cccccc"               # Couleur des lignes de séparation
COLOR_CARD_RED = "#e57373"                # Couleur des cartes rouges (pneus)
COLOR_CARD_GREEN = "#9ccc65"              # Couleur des cartes vertes (pneus)

# --- Polices ---
FONT_FAMILY = "Arial"                       # Police utilisée dans l’UI
FONT_SIZE_BASE = 12                         # Taille de texte par défaut
FONT_SIZE_SECTION = 11                      # Taille des titres de section
FONT_SIZE_BANNER = 22                       # Taille du texte de bannière
FONT_SIZE_PLAYER = 20                       # Taille du sélecteur de joueur
FONT_SIZE_VALUE_BIG = 18                    # Taille des valeurs mises en avant
FONT_SIZE_DEBUG = 10                        # Taille du texte de la zone Debug
FONT_SIZE_LOG = 15                          # Taille du texte de la zone Logs

# --- Layout ---
DEBUG_INITIAL_VISIBLE = True                # État initial: panneau Debug visible
LOG_TEXT_HEIGHT = 8                         # Hauteur (lignes) du bloc Logs
BANNER_MIN_HEIGHT = 100                     # Hauteur minimale de la bannière
SECTION_PAD_X = 5                           # Marge interne horizontale standard
SECTION_PAD_Y = 12                          # Marge interne verticale standard
HSEP_INSET = SECTION_PAD_X                  # Retrait horizontal des séparateurs
TIME_COL_PX = 120                           # Largeur colonne "temps" (Derniers tours) en px


class TrackerUI(tk.Tk):
    """Interface principale, refonte UI selon maquette.

    Layout:
      - row0: bannière (messages importants)
      - row1: colonnes: Session | Joueur | Derniers tours | Debug (optionnel)
      - row2: messages/logs
    """

    def __init__(self, players: list, on_player_change, on_debug_toggle=None):
        super().__init__()

        # Fenêtre
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_GEOMETRY)
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.configure(bg=COLOR_BG_MAIN)

        self.on_player_change = on_player_change
        self.debug_visible = tk.BooleanVar(value=DEBUG_INITIAL_VISIBLE)
        self.on_debug_toggle = on_debug_toggle

        # Menu principal
        self._build_menubar()

        # --- Grille fenêtre: 3 lignes / 1 colonne ---
        self.grid_rowconfigure(0, weight=0, minsize=BANNER_MIN_HEIGHT)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # -----------------------
        # Bannière
        # -----------------------
        self.banner_frame = tk.Frame(self, bg=COLOR_BANNER_BG, bd=0, relief="flat", highlightthickness=0)
        self.banner_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.banner_label = tk.Label(
            self.banner_frame,
            text="",
            font=(FONT_FAMILY, FONT_SIZE_BANNER, "bold"),
            bg=COLOR_BANNER_BG,
            fg=COLOR_BANNER_TEXT,
            anchor="center",
        )
        self.banner_label.pack(fill="x", padx=SECTION_PAD_X, pady=SECTION_PAD_Y)
        # fine bordure basse
        tk.Frame(self.banner_frame, bg=COLOR_SEPARATOR, height=1).pack(fill="x", side="bottom")

        # -----------------------
        # Zone centrale: 3 colonnes (+1 Debug optionnelle)
        # -----------------------
        self.columns = tk.Frame(self, bg=COLOR_BG_MAIN, bd=0, relief="flat", highlightthickness=0)
        self.columns.grid(row=1, column=0, sticky="nsew")
        self.columns.grid_rowconfigure(0, weight=1)
        for c in (0, 2, 4, 6):
            self.columns.grid_columnconfigure(c, weight=1)
        for s in (1, 3, 5):
            self.columns.grid_columnconfigure(s, weight=0, minsize=1)

        def _vsep(col):
            f = tk.Frame(self.columns, bg=COLOR_SEPARATOR, width=1)
            f.grid(row=0, column=col, sticky="ns")
            return f

        # Session (col 0)
        self.session_col = tk.Frame(self.columns, bg=COLOR_BG_MAIN, bd=0, relief="flat", highlightthickness=0)
        self.session_col.grid(row=0, column=0, sticky="nsew", padx=SECTION_PAD_X)

        # Joueur (col 2)
        self.player_col = tk.Frame(self.columns, bg=COLOR_BG_MAIN, bd=0, relief="flat", highlightthickness=0)
        self.player_col.grid(row=0, column=2, sticky="nsew", padx=SECTION_PAD_X)

        # Derniers tours (col 4)
        self.laps_col = tk.Frame(self.columns, bg=COLOR_BG_MAIN, bd=0, relief="flat", highlightthickness=0)
        self.laps_col.grid(row=0, column=4, sticky="nsew", padx=SECTION_PAD_X)

        # Séparateurs verticaux
        self.sep_0 = _vsep(1)
        self.sep_1 = _vsep(3)
        self.sep_2 = _vsep(5)

        # --- Contenu colonne Session ---
        section_style = {"bg": COLOR_BG_MAIN, "fg": COLOR_TEXT, "font": (FONT_FAMILY, FONT_SIZE_SECTION, "bold")}
        base_style = {"bg": COLOR_BG_MAIN, "fg": COLOR_TEXT, "font": (FONT_FAMILY, FONT_SIZE_BASE)}

        def hsep(parent):
            f = tk.Frame(parent, bg=COLOR_SEPARATOR, height=1)
            f.pack(fill="x", padx=HSEP_INSET, pady=8)
            return f

        tk.Label(self.session_col, text="SESSION", **section_style, anchor="w").pack(
            fill="x", padx=SECTION_PAD_X, pady=(SECTION_PAD_Y // 2, 6)
        )
        self.session_time_label = tk.Label(
            self.session_col, text="Temps de session : 1:23:45", **base_style, anchor="w"
        )
        self.session_time_label.pack(fill="x", padx=SECTION_PAD_X, pady=(0, 2))
        self.track_label = tk.Label(self.session_col, text="Circuit : ---", **base_style, anchor="w")
        self.track_label.pack(fill="x", padx=SECTION_PAD_X, pady=(0, 2))
        self.car_label = tk.Label(self.session_col, text="Voiture : ---", **base_style, anchor="w")
        self.car_label.pack(fill="x", padx=SECTION_PAD_X, pady=(0, 10))

        hsep(self.session_col)
        self.absolute_record_info = tk.Label(
            self.session_col, text="Record absolu (détenu par ---) :", **base_style, anchor="w"
        )
        self.absolute_record_info.pack(fill="x", padx=SECTION_PAD_X)
        self.absolute_record_value = tk.Label(
            self.session_col,
            text="---",
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT,
            font=(FONT_FAMILY, FONT_SIZE_VALUE_BIG, "bold"),
            anchor="center",
        )
        self.absolute_record_value.pack(fill="x", padx=SECTION_PAD_X, pady=(2, 10))

        # Séparateur entre le bloc "Record absolu" et la section pneus
        hsep(self.session_col)

        tk.Label(
            self.session_col, text="Température et usure des pneus :", **base_style, anchor="w"
        ).pack(fill="x", padx=SECTION_PAD_X, pady=(0, 6))

        def tire_square(parent, text, color):
            frm = tk.Frame(parent, bg=color, width=48, height=48)
            frm.pack_propagate(False)
            tk.Label(frm, text=text, bg=color, fg="black", font=(FONT_FAMILY, 12, "bold")).pack(
                expand=True, fill="both"
            )
            return frm

        tires_grid = tk.Frame(self.session_col, bg=COLOR_BG_MAIN)
        tires_grid.pack(anchor="w", padx=SECTION_PAD_X)
        for _ in range(2):
            row = tk.Frame(tires_grid, bg=COLOR_BG_MAIN)
            row.pack(anchor="w")
            tire_square(row, "65°", COLOR_CARD_RED).pack(side="left", padx=8, pady=6)
            tire_square(row, "65°", COLOR_CARD_RED).pack(side="left", padx=8, pady=6)
            tire_square(row, "98%", COLOR_CARD_GREEN).pack(side="left", padx=24, pady=6)
            tire_square(row, "98%", COLOR_CARD_GREEN).pack(side="left", padx=8, pady=6)

        # --- Contenu colonne Joueur ---
        header_player = tk.Frame(self.player_col, bg=COLOR_BG_MAIN)
        header_player.pack(fill="x", padx=SECTION_PAD_X, pady=(SECTION_PAD_Y // 2, 0))
        tk.Label(header_player, text="JOUEUR", **section_style).pack(side="left")
        tk.Button(
            header_player,
            text="Éditer la liste",
            relief="flat",
            bd=0,
            highlightthickness=0,
            bg=COLOR_BG_MAIN,
            activebackground=COLOR_BG_MAIN,
            cursor="hand2",
            command=lambda: None,
        ).pack(side="right")

        # Sélecteur joueur (ttk.Combobox, plein-largeur, flèche ▼, fond gris, police grande)
        self.current_player = tk.StringVar(value=players[0] if players else "---")
        self.current_player.trace_add("write", self._on_player_change)
        initial_value = players[0] if players else "---"
        self.current_player.set(initial_value)
        extra_values = players[1:] if len(players) > 1 else []

        select_wrap = tk.Frame(self.player_col, bg=COLOR_BG_MAIN)
        select_wrap.pack(fill="x", padx=SECTION_PAD_X, pady=(10, 14))
        # Affichage actuel + flèche ▼
        self._players_list = list(players) if players else ["---"]
        self.player_display = tk.Label(
            select_wrap, textvariable=self.current_player,
            bg=COLOR_BG_MAIN, fg=COLOR_CONTROL_FG,
            font=(FONT_FAMILY, FONT_SIZE_PLAYER), anchor="center"
        )
        self.player_display.pack(fill="x", side="left", expand=True)
        self.player_arrow = tk.Label(
            select_wrap, text="▼",
            bg=COLOR_BG_MAIN, fg=COLOR_CONTROL_FG,
            font=(FONT_FAMILY, FONT_SIZE_PLAYER-2), width=2, anchor="center"
        )
        self.player_arrow.pack(side="right")

        def _open_player_dropdown(event=None):
            # ferme popup existant
            try:
                if hasattr(self, "_player_popup") and self._player_popup.winfo_exists():
                    self._player_popup.destroy()
            except Exception:
                pass
            popup = tk.Toplevel(self)
            self._player_popup = popup
            popup.overrideredirect(True)
            popup.configure(bg=COLOR_SEPARATOR)
            x = select_wrap.winfo_rootx()
            y = select_wrap.winfo_rooty() + select_wrap.winfo_height()
            w = select_wrap.winfo_width()
            # Calcule une hauteur adaptée à la police pour éviter le texte tronqué
            try:
                fnt = tkfont.Font(family=FONT_FAMILY, size=FONT_SIZE_PLAYER)
                line_h = max(1, int(fnt.metrics("linespace")))
            except Exception:
                line_h = 20
            item_h = line_h + 10
            max_visible = min(8, max(1, len(self._players_list)))
            total_h = int(item_h * max_visible + 2)
            popup.geometry(f"{w}x{total_h}+{x}+{y}")

            container = tk.Frame(popup, bg=COLOR_SEPARATOR)
            container.pack(fill="both", expand=True)
            canvas = tk.Canvas(container, bg=COLOR_BG_MAIN, highlightthickness=0, bd=0)
            vsb = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=vsb.set)
            canvas.pack(side="left", fill="both", expand=True)
            vsb.pack(side="right", fill="y")
            cont = tk.Frame(canvas, bg=COLOR_BG_MAIN)
            canvas.create_window((0, 0), window=cont, anchor="nw")
            
            def _choose(name):
                self.current_player.set(name)
                try:
                    popup.destroy()
                except Exception:
                    pass
            for name in self._players_list:
                lbl = tk.Label(
                    cont, text=name,
                    bg=COLOR_BG_MAIN, fg=COLOR_CONTROL_FG,
                    font=(FONT_FAMILY, FONT_SIZE_PLAYER), anchor="center",
                    padx=6
                )
                lbl.pack(fill="x", ipady=6)
                lbl.bind("<Button-1>", lambda e, n=name: _choose(n))
                # pas de surbrillance bleue — garder gris
                lbl.bind("<Enter>", lambda e, w=lbl: w.configure(bg=COLOR_BG_MAIN))
                lbl.bind("<Leave>", lambda e, w=lbl: w.configure(bg=COLOR_BG_MAIN))
            try:
                cont.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            except Exception:
                pass
            def _wheel(ev):
                delta = -1 if getattr(ev, "delta", 0) > 0 else 1
                canvas.yview_scroll(delta, "units")
                return "break"
            canvas.bind("<MouseWheel>", _wheel)
            canvas.bind("<Button-4>", lambda e: (canvas.yview_scroll(-1, "units"), "break"))
            canvas.bind("<Button-5>", lambda e: (canvas.yview_scroll(1, "units"), "break"))

            def _close_on_click(event):
                try:
                    if not (x <= event.x_root <= x+w and y <= event.y_root <= y+popup.winfo_height()):
                        if popup.winfo_exists():
                            popup.destroy()
                except Exception:
                    pass
            self.bind_all("<Button-1>", _close_on_click, add=True)

        self.player_display.bind("<Button-1>", _open_player_dropdown)
        self.player_arrow.bind("<Button-1>", _open_player_dropdown)
        tk.Frame(select_wrap, bg=COLOR_SEPARATOR, height=1).pack(fill="x", pady=(4, 0))

        # Bloc Record personnel
        hsep(self.player_col)
        tk.Label(self.player_col, text="Record personnel :", **base_style, anchor="w").pack(
            fill="x", padx=SECTION_PAD_X, pady=(6, 2)
        )
        self.best_time_label = tk.Label(
            self.player_col,
            text="---",
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT,
            font=(FONT_FAMILY, FONT_SIZE_VALUE_BIG, "bold"),
            anchor="center",
        )
        self.best_time_label.pack(fill="x", padx=SECTION_PAD_X, pady=(0, 10))

        hsep(self.player_col)
        tk.Label(self.player_col, text="Dernier tour :", **base_style, anchor="w").pack(
            fill="x", padx=SECTION_PAD_X, pady=(6, 2)
        )
        self.current_lap_label = tk.Label(
            self.player_col,
            text="---",
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT,
            font=(FONT_FAMILY, FONT_SIZE_VALUE_BIG, "bold"),
            anchor="center",
        )
        self.current_lap_label.pack(fill="x", padx=SECTION_PAD_X)

        # --- Contenu colonne Derniers tours ---
        tk.Label(self.laps_col, text="DERNIERS TOURS", **section_style, anchor="w").pack(
            fill="x", padx=SECTION_PAD_X, pady=(SECTION_PAD_Y // 2, 0)
        )
        laps_box = tk.Frame(self.laps_col, bg=COLOR_BG_MAIN)
        laps_box.pack(expand=True, fill="both", padx=SECTION_PAD_X, pady=(6, 0))
        self.laps_text = tk.Text(
            laps_box,
            wrap="none",
            font=(FONT_FAMILY, FONT_SIZE_BASE),
            bg=COLOR_BG_MAIN,
            state="disabled",
            height=10,
            takefocus=0,
            cursor="arrow",
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        self.laps_text.pack(expand=True, fill="both")
        self.laps_text.bind("<MouseWheel>", self._on_laps_mousewheel)
        self.laps_text.bind("<Button-4>", self._on_laps_mousewheel_linux)
        self.laps_text.bind("<Button-5>", self._on_laps_mousewheel_linux)
        self.laps_text.bind("<Configure>", self._update_laps_tabs)
        self._populate_laps_placeholder()

        # --- Colonne Debug (col 6) ---
        self.debug_col = tk.Frame(self.columns, bg=COLOR_BG_MAIN, bd=0, relief="flat", highlightthickness=0)
        # Marge gauche/droite homogène pour éviter d'être collé aux bords
        self.debug_col.grid(row=0, column=6, sticky="nsew", padx=(SECTION_PAD_X, SECTION_PAD_X))
        self.debug_col.grid_rowconfigure(1, weight=1)
        self.debug_col.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self.debug_col, bg=COLOR_BG_MAIN)
        header.grid(row=0, column=0, sticky="ew", padx=SECTION_PAD_X, pady=(SECTION_PAD_Y // 2, 0))
        header.grid_columnconfigure(0, weight=1)
        lbl = tk.Label(header, text="DEBUG", **section_style)
        lbl.grid(row=0, column=0, sticky="w")
        btn = tk.Button(
            header,
            text="Masquer",
            relief="flat",
            bd=0,
            highlightthickness=0,
            bg=COLOR_BG_MAIN,
            activebackground=COLOR_BG_MAIN,
            fg=COLOR_CONTROL_FG,
            cursor="hand2",
            command=lambda: self._set_debug_visible(False),
        )
        btn.grid(row=0, column=1, sticky="e")

        self.debug_text = tk.Text(
            self.debug_col,
            wrap="word",
            font=(FONT_FAMILY, FONT_SIZE_DEBUG),
            bg=COLOR_DEBUG_TEXT_BG,
            state="disabled",
            takefocus=0,
            cursor="arrow",
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        # Padding gauche/droite homogène pour éviter d'être collé aux bords
        self.debug_text.grid(row=1, column=0, sticky="nsew", padx=(SECTION_PAD_X, SECTION_PAD_X), pady=(6, 6))
        self.debug_text.bind("<MouseWheel>", self._on_debug_mousewheel)
        self.debug_text.bind("<Button-4>", self._on_debug_mousewheel_linux)
        self.debug_text.bind("<Button-5>", self._on_debug_mousewheel_linux)

        self._apply_debug_visibility()
        self.after(0, self._update_laps_tabs)

        # -----------------------
        # Logs (plein largeur)
        # -----------------------
        self.log_container = tk.Frame(self, bg=COLOR_BG_MAIN, bd=0, relief="flat", highlightthickness=0)
        self.log_container.grid(row=2, column=0, sticky="nsew")
        self.log_container.grid_columnconfigure(0, weight=1)
        tk.Frame(self.log_container, bg=COLOR_SEPARATOR, height=1).grid(row=0, column=0, sticky="ew", padx=0)
        tk.Label(
            self.log_container,
            text="MESSAGES / LOGS",
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT,
            font=(FONT_FAMILY, FONT_SIZE_SECTION, "bold"),
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=SECTION_PAD_X, pady=(SECTION_PAD_Y // 2, 0))
        self.log_text = scrolledtext.ScrolledText(
            self.log_container,
            wrap="word",
            font=(FONT_FAMILY, FONT_SIZE_LOG),
            height=LOG_TEXT_HEIGHT,
            bg=COLOR_LOG_TEXT_BG,
            state="disabled",
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        self.log_text.grid(row=2, column=0, sticky="nsew", padx=SECTION_PAD_X, pady=(6, SECTION_PAD_Y))
        self.log_text.configure(takefocus=0, cursor="arrow", borderwidth=0)
        self.log_text.bind("<MouseWheel>", self._on_log_mousewheel)
        self.log_text.bind("<Button-4>", self._on_log_mousewheel_linux)
        self.log_text.bind("<Button-5>", self._on_log_mousewheel_linux)

    # -----------------------
    # Menu bar
    # -----------------------
    def _build_menubar(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="(à venir)", state="disabled")
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="(à venir)", state="disabled")
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(label="Debug", variable=self.debug_visible, command=self._toggle_debug)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        menubar.add_cascade(label="Édition", menu=edit_menu)
        menubar.add_cascade(label="Affichage", menu=view_menu)
        self.config(menu=menubar)
        self._menubar = menubar

    # -----------------------
    # API publique utilisée par main.py
    # -----------------------
    def _on_player_change(self, *args):
        self.on_player_change(self.current_player.get())

    def update_context(self, track: str, car: str):
        self.track_label.config(text=f"Circuit : {track}")
        self.car_label.config(text=f"Voiture : {car}")

    def update_player_personal_record(self, best_time_str: str):
        self.best_time_label.config(text=f"{best_time_str}")

    def update_current_lap_time(self, text: str):
        self.current_lap_label.config(text=f"{text}")

    def update_debug(self, data: dict):
        first_visible_idx = self.debug_text.index("@0,0")
        first_fraction, last = self.debug_text.yview()
        at_bottom = first_fraction > 0.0 and last >= 0.999
        self.debug_text.config(state="normal")
        try:
            self.debug_text.delete("1.0", "end")
            for k, v in data.items():
                self.debug_text.insert("end", f"{k}: {v}\n")
            if at_bottom:
                self.debug_text.see("end")
            else:
                try:
                    self.debug_text.yview(first_visible_idx)
                except tk.TclError:
                    self.debug_text.see(first_visible_idx)
        finally:
            self.debug_text.config(state="disabled")

    def _on_debug_mousewheel(self, event):
        if event.delta == 0:
            return "break"
        direction = -1 if event.delta > 0 else 1
        self.debug_text.yview_scroll(direction, "units")
        return "break"

    def _on_debug_mousewheel_linux(self, event):
        if event.num == 4:
            self.debug_text.yview_scroll(-1, "units")
        elif event.num == 5:
            self.debug_text.yview_scroll(1, "units")
        return "break"

    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        try:
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
            self.log_text.see("end")
        finally:
            self.log_text.config(state="disabled")

    def _on_log_mousewheel(self, event):
        if event.delta == 0:
            return "break"
        direction = -1 if event.delta > 0 else 1
        self.log_text.yview_scroll(direction, "units")
        return "break"

    def _on_log_mousewheel_linux(self, event):
        if event.num == 4:
            self.log_text.yview_scroll(-1, "units")
        elif event.num == 5:
            self.log_text.yview_scroll(1, "units")
        return "break"

    # Laps scrolling (texte sans scrollbar visible)
    def _on_laps_mousewheel(self, event):
        if event.delta == 0:
            return "break"
        direction = -1 if event.delta > 0 else 1
        self.laps_text.yview_scroll(direction, "units")
        return "break"

    def _on_laps_mousewheel_linux(self, event):
        if event.num == 4:
            self.laps_text.yview_scroll(-1, "units")
        elif event.num == 5:
            self.laps_text.yview_scroll(1, "units")
        return "break"

    def update_players(self, players: list, current: str):
        self._players_list = list(players) if players else ['---']
        if current and players and current in players:
            self.current_player.set(current)
        elif players:
            self.current_player.set(players[0])
        else:
            self.current_player.set('---')

    def set_player_menu_state(self, enabled: bool):
        self._player_enabled = bool(enabled)
        state_fg = COLOR_CONTROL_FG if enabled else "#888"
        try:
            self.player_display.configure(fg=state_fg)
            self.player_arrow.configure(fg=state_fg)
        except Exception:
            pass

    def get_selected_player(self) -> str:
        return self.current_player.get()

    # -----------------------
    # Intégration avec la queue (thread-safe)
    # -----------------------
    def set_on_player_change(self, cb):
        """Permet de modifier le callback après création de l'UI."""
        self.on_player_change = cb

    def bind_event_queue(self, q):
        """Enregistre la queue d'événements UI et lance la pompe .after()."""
        self._event_queue = q
        self.after(16, self._pump_event_queue)  # ~60 FPS

    def _pump_event_queue(self):
        if not hasattr(self, "_event_queue") or self._event_queue is None:
            self.after(16, self._pump_event_queue)
            return
        try:
            while True:
                name, payload = self._event_queue.get_nowait()
                if name == "debug":
                    self.update_debug(payload)
                elif name == "context":
                    self.update_context(payload.get("track", "---"), payload.get("car", "---"))
                elif name == "player_menu_state":
                    self.set_player_menu_state(payload.get("enabled", False))
                elif name == "log":
                    self.add_log(payload.get("message", ""))
                elif name == "player_best":
                    self.update_player_personal_record(payload.get("text", "---"))
                elif name == "current_lap":
                    self.update_current_lap_time(payload.get("text", "---"))
                elif name == "banner":
                    self.set_banner(payload.get("text", ""))
        except _q.Empty:
            pass
        except Exception as e:
            try:
                self.add_log(f"UI error: {e}")
            except Exception:
                pass
        self.after(16, self._pump_event_queue)

    def _on_root_resize(self, event):
        # plus de réglage manuel des colonnes; les weights suffisent
        pass

    def _toggle_debug(self):
        """Affiche/masque la colonne Debug et le séparateur associé."""
        self._apply_debug_visibility()
        if self.on_debug_toggle is not None:
            try:
                self.on_debug_toggle(bool(self.debug_visible.get()))
            except Exception:
                self.add_log("UI error: on_debug_toggle callback")

    def _set_debug_visible(self, flag: bool):
        try:
            self.debug_visible.set(bool(flag))
        except Exception:
            pass
        self._toggle_debug()

    def _apply_debug_visibility(self):
        visible = bool(self.debug_visible.get())
        if visible:
            for c in (0, 2, 4, 6):
                self.columns.grid_columnconfigure(c, weight=1, uniform="cols4", minsize=0)
            self.debug_col.grid(row=0, column=6, sticky="nsew")
            self.sep_2.grid(row=0, column=5, sticky="ns")
        else:
            self.debug_col.grid_remove()
            self.sep_2.grid_remove()
            self.columns.grid_columnconfigure(6, weight=0, minsize=0, uniform="col6")
            for c in (0, 2, 4):
                self.columns.grid_columnconfigure(c, weight=1, uniform="cols3", minsize=0)

    def _populate_laps_placeholder(self):
        lines = [
            "0:34.678\tNico",
            "0:36.878\tNico",
            "0:35.679\tNico",
            "0:34.678\tBooki",
            "0:36.878\tNico",
            "0:35.679\tJacques",
            "0:34.678\tNico",
            "0:34.132\tNico",
            "0:34.678\tNico",
        ]
        self.laps_text.config(state="normal")
        try:
            for ln in lines:
                self.laps_text.insert("end", ln + "\n")
            self.laps_text.see("end")
        finally:
            self.laps_text.config(state="disabled")

    def set_banner(self, text: str = ""):
        self.banner_label.config(text=text)

    def set_on_debug_toggle(self, cb):
        """Permet de modifier le callback de notification Debug visible/masqué."""
        self.on_debug_toggle = cb

    def _update_laps_tabs(self, event=None):
        try:
            width = int(self.laps_text.winfo_width())
        except Exception:
            return
        # Tab-stop 1 = temps (gauche), Tab-stop 2 = nom (aligné à droite)
        time_px = TIME_COL_PX
        min_right = time_px + 60
        right_px = max(min_right, width - SECTION_PAD_X - 6)
        self.laps_text.configure(tabs=(f"{time_px}p", f"{right_px}p right"))






