#data_store.py
import os
import json

# Chemins vers les fichiers de données
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
BEST_LAPS_FILE = os.path.join(BASE_DIR, 'best_laps.json')
PLAYERS_FILE = os.path.join(BASE_DIR, 'players.json')

class DataStore:
    """
    Gère le chargement et la sauvegarde des meilleurs temps
    et de la liste des joueurs au format JSON.
    """

    @staticmethod
    def load_best_laps() -> dict:
        """
        Charge les meilleurs temps depuis le fichier JSON.

        Returns:
            dict: Structure de la forme {
                "track|car": {
                    "player_name": {"time": float, "date": str},
                    ...
                },
                ...
            }
        """
        if not os.path.exists(BEST_LAPS_FILE):
            return {}
        with open(BEST_LAPS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save_best_laps(data: dict):
        """
        Sauvegarde les meilleurs temps dans le fichier JSON.

        Args:
            data (dict): Dictionnaire des meilleurs temps à enregistrer.
        """
        os.makedirs(BASE_DIR, exist_ok=True)
        with open(BEST_LAPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def load_players() -> list:
        """
        Charge la liste des joueurs depuis le fichier JSON.

        Returns:
            list: Liste de chaînes correspondant aux noms de joueurs.
        """
        if not os.path.exists(PLAYERS_FILE):
            return []
        with open(PLAYERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save_players(players: list):
        """
        Sauvegarde la liste des joueurs dans le fichier JSON.

        Args:
            players (list): Liste de chaînes des noms de joueurs.
        """
        os.makedirs(BASE_DIR, exist_ok=True)
        with open(PLAYERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(players, f, ensure_ascii=False, indent=4)
