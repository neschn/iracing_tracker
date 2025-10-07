# ui.py
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

# -----------------------
# Paramètres faciles à éditer
# -----------------------
WINDOW_TITLE    = "iRacing Tracker"  # Titre de la fenêtre principale
WINDOW_GEOMETRY = "1200x700"         # Taille initiale de la fenêtre (LxH)
MIN_WIDTH       = 900                 # Largeur minimale de la fenêtre
MIN_HEIGHT      = 550                 # Hauteur minimale de la fenêtre
PADDING         = 8                   # Marges externes autour des blocs principaux

# --- Thème / Apparence ---
COLOR_BG_MAIN        = "#f0f0f0"  # Couleur de fond principale de l'application
COLOR_TEXT           = "black"    # Couleur du texte par défaut
COLOR_CONTROL_BG     = "white"    # Fond des contrôles (menus déroulants, etc.)
COLOR_CONTROL_FG     = "black"    # Couleur du texte des contrôles
COLOR_BANNER_BG      = "#f8fbff"  # Fond de la bannière supérieure
COLOR_BANNER_TEXT    = "#0d47a1"  # Couleur du texte de la bannière
COLOR_DEBUG_BG       = "#ffffff"  # Fond du cadre Debug
COLOR_DEBUG_TEXT_BG  = "#f8f8f8"  # Fond de la zone de texte Debug
COLOR_LOG_TEXT_BG    = "#eef"     # Fond de la zone de texte des logs

# --- Polices ---
FONT_FAMILY       = "Consolas"  # Police utilisée globalement
FONT_SIZE_BASE    = 12          # Taille de base pour les labels de contenu
FONT_SIZE_GROUP   = 11          # Taille pour les titres de groupes (LabelFrame)
FONT_SIZE_BANNER  = 14          # Taille du texte de la bannière
FONT_SIZE_DEBUG   = 10          # Taille de police de la zone Debug
FONT_SIZE_LOG     = 15          # Taille de police de la zone Logs

# --- Layout ---
GRID_MAIN_WEIGHT      = 2         # Poids de la colonne principale (2/3 si debug=1)
GRID_DEBUG_WEIGHT     = 1         # Poids de la colonne Debug (1/3 si main=2)
DEBUG_COLUMN_FRACTION = 1/3       # Fraction de la largeur allouée au Debug lors du resize
DEBUG_INITIAL_VISIBLE  = True      # Visibilité par défaut du panneau Debug
DEBUG_TEXT_WIDTH       = 40        # Largeur (caractères) de la zone de texte Debug
LOG_TEXT_HEIGHT        = 8         # Hauteur (lignes) de la zone de texte Logs
BANNER_BORDER_WIDTH    = 1         # Épaisseur de bordure de la bannière
BANNER_RELIEF          = "solid"   # Style de la bordure de la bannière
INNER_PAD_X            = 8         # Padding horizontal interne standard
INNER_PAD_Y            = 2         # Padding vertical interne standard
TEXTBOX_PAD            = 6         # Padding autour des zones de texte (Debug/Logs)

class TrackerUI(tk.Tk):
    """
    Interface principale.
    Zones:
      - row0: bannière (messages importants)
      - row1: col0 = zone principale ; col1 = zone debug
      - row2: logs (plein largeur)
    """
    def __init__(self, players: list, on_player_change):
        super().__init__()

        # Fenêtre
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_GEOMETRY)
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.configure(bg=COLOR_BG_MAIN)

        self.on_player_change = on_player_change
        self.debug_visible = tk.BooleanVar(value=DEBUG_INITIAL_VISIBLE)
        
        # --- Menu principal (squelette) ---
        self._build_menubar()

        # --- Grille maître: 3 lignes / 2 colonnes ---
        # row0 = bannière
        # row1 = contenu (col0) + debug (col1)
        # row2 = logs
        self.grid_rowconfigure(0, weight=0)   # bannière
        self.grid_rowconfigure(1, weight=1)   # zone centrale extensible
        self.grid_rowconfigure(2, weight=0)   # logs
        self.grid_columnconfigure(0, weight=GRID_MAIN_WEIGHT)
        self.grid_columnconfigure(1, weight=GRID_DEBUG_WEIGHT)
        self.bind("<Configure>", self._on_root_resize)
        self.after(0, self._update_column_sizes)

        # -----------------------
        # Bannière (messages importants)
        # -----------------------
        self.banner_frame = tk.Frame(self, bg=COLOR_BANNER_BG, bd=BANNER_BORDER_WIDTH, relief=BANNER_RELIEF)
        self.banner_frame.grid(row=0, column=0, columnspan=2, sticky="nsew",
                               padx=PADDING, pady=(PADDING, 0))
        self.banner_label = tk.Label(
            self.banner_frame,
            text="",  # vide par défaut
            font=(FONT_FAMILY, FONT_SIZE_BANNER, "bold"),
            bg=COLOR_BANNER_BG, fg=COLOR_BANNER_TEXT, anchor="center"
        )
        self.banner_label.pack(fill="x", padx=INNER_PAD_X, pady=INNER_PAD_X)

        # -----------------------
        # Zone principale (col0)
        # -----------------------
        self.content_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        self.content_frame.grid(row=1, column=0, sticky="nsew",
                                padx=PADDING, pady=PADDING)
        self.content_frame.grid_rowconfigure(0, weight=0)
        self.content_frame.grid_rowconfigure(1, weight=0)
        self.content_frame.grid_rowconfigure(2, weight=1)  # espace extensible
        self.content_frame.grid_columnconfigure(0, weight=1)

        style = {"bg": COLOR_BG_MAIN, "fg": COLOR_TEXT, "font": (FONT_FAMILY, FONT_SIZE_BASE)}

        # Groupe Contexte
        context_box = tk.LabelFrame(self.content_frame, text="Contexte",
                                    bg=COLOR_BG_MAIN, font=(FONT_FAMILY, FONT_SIZE_GROUP, "bold"))
        context_box.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, PADDING))

        self.track_label = tk.Label(context_box, text="Circuit : ---", **style)
        self.car_label   = tk.Label(context_box, text="Voiture : ---", **style)
        self.best_time_label = tk.Label(context_box, text="Record personnel : ---", **style)
        self.current_lap_label = tk.Label(context_box, text="Tour en cours : ---", **style)

        self.track_label.pack(anchor="w", padx=INNER_PAD_X, pady=INNER_PAD_Y)
        self.car_label.pack(anchor="w", padx=INNER_PAD_X, pady=INNER_PAD_Y)
        self.best_time_label.pack(anchor="w", padx=INNER_PAD_X, pady=INNER_PAD_Y)
        self.current_lap_label.pack(anchor="w", padx=INNER_PAD_X, pady=(INNER_PAD_Y, INNER_PAD_X))

        # Groupe Joueur
        player_box = tk.LabelFrame(self.content_frame, text="Joueur",
                                   bg=COLOR_BG_MAIN, font=(FONT_FAMILY, FONT_SIZE_GROUP, "bold"))
        player_box.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, PADDING))

        self.current_player = tk.StringVar(value=players[0] if players else "---")
        self.current_player.trace_add("write", self._on_player_change)

        initial_value = players[0] if players else "---"
        self.current_player.set(initial_value)
        extra_values = players[1:] if len(players) > 1 else []

        self.player_menu = tk.OptionMenu(player_box, self.current_player,
                                         initial_value, *extra_values)
        self.player_menu.config(bg=COLOR_CONTROL_BG, fg=COLOR_CONTROL_FG, font=(FONT_FAMILY, FONT_SIZE_GROUP))
        self.player_menu.pack(anchor="w", padx=INNER_PAD_X, pady=INNER_PAD_X)

        # (zone extensible réservée dans content_frame si tu veux ajouter autre chose)
        tk.Frame(self.content_frame, bg=COLOR_BG_MAIN).grid(
            row=2, column=0, sticky="nsew"
        )

        # -----------------------
        # Zone debug (col1)
        # -----------------------
        self.debug_frame = tk.LabelFrame(self, text="Debug iRacing",
                                         bg=COLOR_DEBUG_BG, font=(FONT_FAMILY, FONT_SIZE_GROUP, "bold"))
        self.debug_frame.grid(row=1, column=1, sticky="nsew",
                              padx=(0, PADDING), pady=PADDING)
        self.debug_frame.grid_rowconfigure(0, weight=1)
        self.debug_frame.grid_columnconfigure(0, weight=1)

        self.debug_text = tk.Text(
            self.debug_frame,
            wrap="none",
            font=(FONT_FAMILY, FONT_SIZE_DEBUG),
            bg=COLOR_DEBUG_TEXT_BG,
            width=DEBUG_TEXT_WIDTH
        )
        self.debug_text.grid(row=0, column=0, sticky="nsew", padx=TEXTBOX_PAD, pady=TEXTBOX_PAD)

        # -----------------------
        # Logs (plein largeur)
        # -----------------------
        self.log_frame = tk.LabelFrame(self, text="Logs",
                                       bg=COLOR_BG_MAIN, font=(FONT_FAMILY, FONT_SIZE_GROUP, "bold"))
        self.log_frame.grid(row=2, column=0, columnspan=2, sticky="nsew",
                            padx=PADDING, pady=(0, PADDING))
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame, wrap="word", font=(FONT_FAMILY, FONT_SIZE_LOG), height=LOG_TEXT_HEIGHT, bg=COLOR_LOG_TEXT_BG
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=TEXTBOX_PAD, pady=TEXTBOX_PAD)

    # -----------------------
    # Menu bar (squelettes)
    # -----------------------
    def _build_menubar(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="(à venir)", state="disabled")

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="(à venir)", state="disabled")

        view_menu = tk.Menu(menubar, tearoff=0)
        # ⬇️ La case à cocher pour afficher/masquer le panneau Debug
        view_menu.add_checkbutton(
            label="Debug",
            variable=self.debug_visible,
            command=self._toggle_debug
        )

        menubar.add_cascade(label="Fichier",   menu=file_menu)
        menubar.add_cascade(label="Édition",   menu=edit_menu)
        menubar.add_cascade(label="Affichage", menu=view_menu)   # <-- change "Affichage" en "Fenêtre" si tu préfères

        self.config(menu=menubar)
        self._menubar = menubar  # si tu veux y accéder plus tard


    # -----------------------
    # API publique utilisée par main.py
    # -----------------------
    def _on_player_change(self, *args):
        self.on_player_change(self.current_player.get())

    def update_context(self, track: str, car: str):
        self.track_label.config(text=f"Circuit : {track}")
        self.car_label.config(text=f"Voiture : {car}")

    def update_player_personnal_record(self, best_time_str: str):
        self.best_time_label.config(text=f"Record personnel : {best_time_str}")

    def update_current_lap_time(self, text: str):
        # appelé par le dispatcher si tu envoies l’event "current_lap"
        self.current_lap_label.config(text=f"Tour en cours : {text}")

    def update_debug(self, data: dict):
        self.debug_text.delete("1.0", "end")
        for k, v in data.items():
            self.debug_text.insert("end", f"{k}: {v}\n")

    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def update_players(self, players: list, current: str):
        menu = self.player_menu['menu']
        menu.delete(0, 'end')
        for name in players:
            menu.add_command(label=name, command=lambda n=name: self.current_player.set(n))
        # valeur sélectionnée
        if current and current in players:
            self.current_player.set(current)
        elif players:
            self.current_player.set(players[0])
        else:
            self.current_player.set("---")

    def set_player_menu_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.player_menu.config(state=state)

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
            import queue as _q
            while True:
                name, payload = self._event_queue.get_nowait()
                if name == "debug":
                    self.update_debug(payload)
                elif name == "context":
                    self.update_context(payload.get("track","---"), payload.get("car","---"))
                elif name == "player_menu_state":
                    self.set_player_menu_state(payload.get("enabled", False))
                elif name == "log":
                    self.add_log(payload.get("message",""))
                elif name == "player_best":
                    self.update_player_personnal_record(payload.get("text","---"))
                elif name == "current_lap":
                    self.update_current_lap_time(payload.get("text","---"))
                elif name == "banner":
                    self.set_banner(payload.get("text", ""))
        except Exception:
            # queue.Empty, etc. -> on ignore
            pass

        self.after(16, self._pump_event_queue)

    def _on_root_resize(self, event):
        if event.widget is self:
            self._update_column_sizes()

    def _update_column_sizes(self):
        width = self.winfo_width()
        if width <= 1:
            return
        usable_width = max(width - 2 * PADDING, 0)
        if self.debug_visible.get():
            debug_width = int(usable_width * DEBUG_COLUMN_FRACTION)
            main_width = usable_width - debug_width
        else:
            debug_width = 0
            main_width = usable_width

        self.grid_columnconfigure(0, minsize=main_width)
        self.grid_columnconfigure(1, minsize=debug_width)

    def _toggle_debug(self):
        """
        Affiche/masque la frame de debug (self.debug_frame) et ajuste la grille.
        """
        if self.debug_visible.get():
            # Ré-affiche le panneau Debug avec les mêmes options grid
            self.debug_frame.grid(row=1, column=1, sticky="nsew",
                                padx=(0, PADDING), pady=PADDING)
            # Rétablit la répartition des colonnes
            self.grid_columnconfigure(0, weight=GRID_MAIN_WEIGHT)
            self.grid_columnconfigure(1, weight=GRID_DEBUG_WEIGHT)
        else:
            # Cache proprement la frame Debug
            self.debug_frame.grid_remove()
            # Donne tout l'espace à la colonne 0
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)

        self._update_column_sizes()

    # API simple pour mettre à jour la bannière
    def set_banner(self, text: str = ""):
        self.banner_label.config(text=text)
