# ui.py
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import queue as _q  # <-- pour attraper queue.Empty proprement

# -----------------------
# Paramètres faciles à éditer
# -----------------------
WINDOW_TITLE    = "iRacing Tracker"
WINDOW_GEOMETRY = "1200x700"
MIN_WIDTH       = 900
MIN_HEIGHT      = 550
PADDING         = 8

# --- Thème / Apparence ---
COLOR_BG_MAIN        = "#f0f0f0"
COLOR_TEXT           = "black"
COLOR_CONTROL_BG     = "white"
COLOR_CONTROL_FG     = "black"
COLOR_BANNER_BG      = "#f8fbff"
COLOR_BANNER_TEXT    = "#0d47a1"
COLOR_DEBUG_BG       = "#ffffff"
COLOR_DEBUG_TEXT_BG  = "#f8f8f8"
COLOR_LOG_TEXT_BG    = "#eef"

# --- Polices ---
FONT_FAMILY       = "Arial"
FONT_SIZE_BASE    = 12
FONT_SIZE_GROUP   = 11
FONT_SIZE_BANNER  = 14
FONT_SIZE_DEBUG   = 10
FONT_SIZE_LOG     = 15

# --- Layout ---
GRID_MAIN_WEIGHT      = 2
GRID_DEBUG_WEIGHT     = 1
DEBUG_COLUMN_FRACTION = 1/3
DEBUG_INITIAL_VISIBLE  = True
DEBUG_TEXT_WIDTH       = 40
LOG_TEXT_HEIGHT        = 8
BANNER_BORDER_WIDTH    = 1
BANNER_RELIEF          = "solid"
BANNER_MIN_HEIGHT      = 70
INNER_PAD_X            = 8
INNER_PAD_Y            = 2
TEXTBOX_PAD            = 6

class TrackerUI(tk.Tk):
    """
    Interface principale.
    Zones:
      - row0: bannière (messages importants)
      - row1: col0 = zone principale ; col1 = zone debug
      - row2: logs (plein largeur)
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
        
        # --- Menu principal (squelette) ---
        self._build_menubar()

        # --- Grille maître: 3 lignes / 2 colonnes ---
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(0, minsize=BANNER_MIN_HEIGHT)
        self.grid_columnconfigure(0, weight=GRID_MAIN_WEIGHT)
        self.grid_columnconfigure(1, weight=GRID_DEBUG_WEIGHT)
        self.bind("<Configure>", self._on_root_resize)
        self.after(0, self._update_column_sizes)

        # -----------------------
        # Bannière
        # -----------------------
        self.banner_frame = tk.Frame(self, bg=COLOR_BANNER_BG, bd=BANNER_BORDER_WIDTH, relief=BANNER_RELIEF)
        self.banner_frame.grid(row=0, column=0, columnspan=2, sticky="nsew",
                               padx=PADDING, pady=(PADDING, 0))
        self.banner_label = tk.Label(
            self.banner_frame,
            text="",
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
        self.content_frame.grid_rowconfigure(2, weight=1)
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

        tk.Frame(self.content_frame, bg=COLOR_BG_MAIN).grid(row=2, column=0, sticky="nsew")

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
            wrap="word",
            font=(FONT_FAMILY, FONT_SIZE_DEBUG),
            bg=COLOR_DEBUG_TEXT_BG,
            width=DEBUG_TEXT_WIDTH,
            state="disabled",
            takefocus=0,
            cursor="arrow"
        )
        self.debug_text.grid(row=0, column=0, sticky="nsew", padx=TEXTBOX_PAD, pady=TEXTBOX_PAD)
        self.debug_text.bind("<MouseWheel>", self._on_debug_mousewheel)
        self.debug_text.bind("<Button-4>", self._on_debug_mousewheel_linux)
        self.debug_text.bind("<Button-5>", self._on_debug_mousewheel_linux)

        # -----------------------
        # Logs (plein largeur)
        # -----------------------
        self.log_frame = tk.LabelFrame(self, text="Logs",
                                       bg=COLOR_BG_MAIN, font=(FONT_FAMILY, FONT_SIZE_GROUP, "bold"))
        self.log_frame.grid(row=2, column=0, columnspan=2, sticky="nsew",
                            padx=PADDING, pady=(0, PADDING))
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            wrap="word",
            font=(FONT_FAMILY, FONT_SIZE_LOG),
            height=LOG_TEXT_HEIGHT,
            bg=COLOR_LOG_TEXT_BG,
            state="disabled"
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=TEXTBOX_PAD, pady=TEXTBOX_PAD)
        self.log_text.configure(takefocus=0, cursor="arrow")
        self.log_text.bind("<MouseWheel>", self._on_log_mousewheel)
        self.log_text.bind("<Button-4>", self._on_log_mousewheel_linux)
        self.log_text.bind("<Button-5>", self._on_log_mousewheel_linux)

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
        view_menu.add_checkbutton(label="Debug", variable=self.debug_visible, command=self._toggle_debug)

        menubar.add_cascade(label="Fichier",   menu=file_menu)
        menubar.add_cascade(label="Édition",   menu=edit_menu)
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
        self.best_time_label.config(text=f"Record personnel : {best_time_str}")

    def update_current_lap_time(self, text: str):
        self.current_lap_label.config(text=f"Tour en cours : {text}")

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

    def update_players(self, players: list, current: str):
        menu = self.player_menu['menu']
        menu.delete(0, 'end')
        for name in players:
            menu.add_command(label=name, command=lambda n=name: self.current_player.set(n))
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
                    self.update_player_personal_record(payload.get("text","---"))
                elif name == "current_lap":
                    self.update_current_lap_time(payload.get("text","---"))
                elif name == "banner":
                    self.set_banner(payload.get("text", ""))
        except _q.Empty:
            pass
        except Exception as e:
            # On ne casse pas l'UI, mais on trace l'erreur
            try:
                self.add_log(f"UI error: {e}")
            except Exception:
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
        """Affiche/masque la frame de debug et ajuste la grille."""
        visible = bool(self.debug_visible.get())

        if visible:
            self.debug_frame.grid(row=1, column=1, sticky="nsew",
                                padx=(0, PADDING), pady=PADDING)
            self.grid_columnconfigure(0, weight=GRID_MAIN_WEIGHT)
            self.grid_columnconfigure(1, weight=GRID_DEBUG_WEIGHT)
        else:
            self.debug_frame.grid_remove()
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)

        self._update_column_sizes()

        if self.on_debug_toggle is not None:
            try:
                self.on_debug_toggle(visible)
            except Exception:
                self.add_log("UI error: on_debug_toggle callback")



    def set_banner(self, text: str = ""):
        self.banner_label.config(text=text)

    def set_on_debug_toggle(self, cb):
        """Permet de modifier le callback de notification Debug visible/masqué."""
        self.on_debug_toggle = cb
