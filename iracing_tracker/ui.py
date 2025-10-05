#ui.py
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

class TrackerUI(tk.Tk):
    """
    Interface graphique principale pour iRacing Tracker.
    Affiche le contexte (circuit, voiture, meilleur temps),
    une zone de debug des variables iRacing, et une zone de logs.
    """
    def __init__(self, players: list, on_player_change):
        """
        Initialise la fenêtre et les widgets.

        Args:
            players (list): Liste initiale des noms de joueurs.
            on_player_change (callable): Fonction à appeler lors du changement de joueur.
        """
        super().__init__()
        self.title("iRacing Tracker")
        self.geometry("1000x600")
        self.configure(bg="#f0f0f0")

        self.on_player_change = on_player_change

        # Frame de gauche pour le contexte et la sélection de joueur
        self.left_frame = tk.Frame(self, bg="#f0f0f0")
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)

        # Frame de droite pour le debug
        self.right_frame = tk.Frame(self, bg="#ffffff")
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Styles partagés
        style = {"bg": "#f0f0f0", "fg": "black", "font": ("Consolas", 12)}

        # Labels de contexte
        self.track_label = tk.Label(self.left_frame, text="Circuit : ---", **style)
        self.track_label.pack(pady=2)
        self.car_label = tk.Label(self.left_frame, text="Voiture : ---", **style)
        self.car_label.pack(pady=2)
        self.best_time_label = tk.Label(self.left_frame, text="Meilleur : ---", **style)
        self.best_time_label.pack(pady=2)

        # Sélection du joueur
        player_frame = tk.Frame(self.left_frame, bg="#f0f0f0")
        player_frame.pack(pady=5)
        tk.Label(player_frame, text="Joueur :", **style).pack(side="left")
        self.current_player = tk.StringVar(value=players[0] if players else "")
        self.current_player.trace_add("write", self._on_player_change)
        self.player_menu = tk.OptionMenu(player_frame, self.current_player, *players)
        self.player_menu.config(bg="white", fg="black", font=("Consolas", 11))
        self.player_menu.pack(side="left")

        # Zone de debug des variables iRacing
        debug_label = tk.Label(self.right_frame, text="Debug iRacing", font=("Consolas", 12, "bold"), bg="#ffffff")
        debug_label.pack(anchor="nw")
        self.debug_text = tk.Text(self.right_frame, wrap="none", font=("Consolas", 10), bg="#f8f8f8", height=15)
        self.debug_text.pack(fill="both", expand=True)

        # Frame de logs en bas de la fenêtre
        self.log_frame = tk.Frame(self, bg="#f0f0f0")
        self.log_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        log_label = tk.Label(self.log_frame, text="Logs", font=("Consolas", 12, "bold"), bg="#f0f0f0")
        log_label.pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            wrap="word",
            font=("Consolas", 10),
            height=8,
            bg="#eef"
        )
        self.log_text.pack(fill="x", expand=False)

    def _on_player_change(self, *args):
        """
        Callback interne invoqué lors du changement de joueur.
        """
        self.on_player_change(self.current_player.get())

    def update_context(self, track: str, car: str):
        """
        Met à jour les labels du circuit et de la voiture.
        """
        self.track_label.config(text=f"Circuit : {track}")
        self.car_label.config(text=f"Voiture : {car}")

    def update_player_personnal_record(self, best_time_str: str):
        """
        Met à jour le label du meilleur temps.
        """
        self.best_time_label.config(text=f"Record personnel : {best_time_str}")


    def update_debug(self, data: dict):
        """
        Affiche les variables de debug dans la zone dédiée.
        """
        self.debug_text.delete("1.0", "end")
        for k, v in data.items():
            self.debug_text.insert("end", f"{k}: {v}\n")

    def add_log(self, message: str):
        """
        Ajoute une ligne dans la zone de logs avec horodatage.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def update_players(self, players: list, current: str):
        """
        Met à jour la liste déroulante des joueurs.
        """
        menu = self.player_menu['menu']
        menu.delete(0, 'end')
        for name in players:
            menu.add_command(label=name, command=lambda n=name: self.current_player.set(n))
        self.current_player.set(current)

    def set_player_menu_state(self, enabled: bool):
        """
        Active ou désactive la liste des joueurs.
        """
        state = "normal" if enabled else "disabled"
        self.player_menu.config(state=state)

    def get_selected_player(self) -> str:
        """
        Retourne le joueur actuellement sélectionné dans l'OptionMenu.
        """
        return self.current_player.get()
