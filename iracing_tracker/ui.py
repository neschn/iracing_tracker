# ui.py
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

# -----------------------
# Paramètres faciles à éditer
# -----------------------
WINDOW_TITLE    = "iRacing Tracker"
WINDOW_GEOMETRY = "1200x700"
MIN_WIDTH       = 900
MIN_HEIGHT      = 550
PADDING         = 8

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
        self.configure(bg="#f0f0f0")

        self.on_player_change = on_player_change
        self.debug_visible = tk.BooleanVar(value=True)
        
        # --- Menu principal (squelette) ---
        self._build_menubar()

        # --- Grille maître: 3 lignes / 2 colonnes ---
        # row0 = bannière
        # row1 = contenu (col0) + debug (col1)
        # row2 = logs
        self.grid_rowconfigure(0, weight=0)   # bannière
        self.grid_rowconfigure(1, weight=1)   # zone centrale extensible
        self.grid_rowconfigure(2, weight=0)   # logs
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        # -----------------------
        # Bannière (messages importants)
        # -----------------------
        self.banner_frame = tk.Frame(self, bg="#f8fbff", bd=1, relief="solid")
        self.banner_frame.grid(row=0, column=0, columnspan=2, sticky="nsew",
                               padx=PADDING, pady=(PADDING, 0))
        self.banner_label = tk.Label(
            self.banner_frame,
            text="",  # vide par défaut
            font=("Consolas", 14, "bold"),
            bg="#f8fbff", fg="#0d47a1", anchor="center"
        )
        self.banner_label.pack(fill="x", padx=8, pady=8)

        # -----------------------
        # Zone principale (col0)
        # -----------------------
        self.content_frame = tk.Frame(self, bg="#f0f0f0")
        self.content_frame.grid(row=1, column=0, sticky="nsew",
                                padx=PADDING, pady=PADDING)
        self.content_frame.grid_rowconfigure(0, weight=0)
        self.content_frame.grid_rowconfigure(1, weight=0)
        self.content_frame.grid_rowconfigure(2, weight=1)  # espace extensible
        self.content_frame.grid_columnconfigure(0, weight=1)

        style = {"bg": "#f0f0f0", "fg": "black", "font": ("Consolas", 12)}

        # Groupe Contexte
        context_box = tk.LabelFrame(self.content_frame, text="Contexte",
                                    bg="#f0f0f0", font=("Consolas", 11, "bold"))
        context_box.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, PADDING))

        self.track_label = tk.Label(context_box, text="Circuit : ---", **style)
        self.car_label   = tk.Label(context_box, text="Voiture : ---", **style)
        self.best_time_label = tk.Label(context_box, text="Record personnel : ---", **style)
        self.current_lap_label = tk.Label(context_box, text="Tour en cours : ---", **style)

        self.track_label.pack(anchor="w", padx=8, pady=2)
        self.car_label.pack(anchor="w", padx=8, pady=2)
        self.best_time_label.pack(anchor="w", padx=8, pady=2)
        self.current_lap_label.pack(anchor="w", padx=8, pady=(2, 8))

        # Groupe Joueur
        player_box = tk.LabelFrame(self.content_frame, text="Joueur",
                                   bg="#f0f0f0", font=("Consolas", 11, "bold"))
        player_box.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, PADDING))

        self.current_player = tk.StringVar(value=players[0] if players else "---")
        self.current_player.trace_add("write", self._on_player_change)

        initial_value = players[0] if players else "---"
        self.current_player.set(initial_value)
        extra_values = players[1:] if len(players) > 1 else []

        self.player_menu = tk.OptionMenu(player_box, self.current_player,
                                         initial_value, *extra_values)
        self.player_menu.config(bg="white", fg="black", font=("Consolas", 11))
        self.player_menu.pack(anchor="w", padx=8, pady=8)

        # (zone extensible réservée dans content_frame si tu veux ajouter autre chose)
        tk.Frame(self.content_frame, bg="#f0f0f0").grid(
            row=2, column=0, sticky="nsew"
        )

        # -----------------------
        # Zone debug (col1)
        # -----------------------
        self.debug_frame = tk.LabelFrame(self, text="Debug iRacing",
                                         bg="#ffffff", font=("Consolas", 11, "bold"))
        self.debug_frame.grid(row=1, column=1, sticky="nsew",
                              padx=(0, PADDING), pady=PADDING)
        self.debug_frame.grid_rowconfigure(0, weight=1)
        self.debug_frame.grid_columnconfigure(0, weight=1)

        self.debug_text = tk.Text(self.debug_frame, wrap="none",
                                  font=("Consolas", 10), bg="#f8f8f8")
        self.debug_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        # -----------------------
        # Logs (plein largeur)
        # -----------------------
        self.log_frame = tk.LabelFrame(self, text="Logs",
                                       bg="#f0f0f0", font=("Consolas", 11, "bold"))
        self.log_frame.grid(row=2, column=0, columnspan=2, sticky="nsew",
                            padx=PADDING, pady=(0, PADDING))
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame, wrap="word", font=("Consolas", 10), height=8, bg="#eef"
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

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

    def _toggle_debug(self):
        """
        Affiche/masque la frame de debug (self.debug_frame) et ajuste la grille.
        """
        if self.debug_visible.get():
            # Ré-affiche le panneau Debug avec les mêmes options grid
            self.debug_frame.grid(row=1, column=1, sticky="nsew",
                                padx=(0, PADDING), pady=PADDING)
            # Rétablit la répartition des colonnes
            self.grid_columnconfigure(0, weight=3)
            self.grid_columnconfigure(1, weight=2)
        else:
            # Cache proprement la frame Debug
            self.debug_frame.grid_remove()
            # Donne tout l'espace à la colonne 0
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)

    # API simple pour mettre à jour la bannière
    def set_banner(self, text: str = ""):
        self.banner_label.config(text=text)
