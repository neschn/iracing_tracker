################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/data_store.py                                                                      #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Gère la persistance locale (JSON atomique) des joueurs et des meilleurs tours.                 #
################################################################################################################

import os
import sys
import json
import tempfile
from datetime import datetime


#--------------------------------------------------------------------------------------------------------------#
# Détermine le répertoire de stockage des données utilisateur (surchargé par IRTRACKER_DATA_DIR).              #
#--------------------------------------------------------------------------------------------------------------#
def _user_data_dir() -> str:
    env_override = os.getenv("IRTRACKER_DATA_DIR")
    if env_override:
        return env_override
    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
        return os.path.join(base, "iRacingTracker")
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
        return os.path.join(base, "iRacingTracker")
    base = os.getenv("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "iracing_tracker")


DATA_DIR = _user_data_dir()
os.makedirs(DATA_DIR, exist_ok=True)

PLAYERS_PATH   = os.path.join(DATA_DIR, "players.json")
BEST_LAPS_PATH = os.path.join(DATA_DIR, "best_laps.json")


#--------------------------------------------------------------------------------------------------------------#
# Crée le dossier parent d'un chemin si nécessaire.                                                            #
#--------------------------------------------------------------------------------------------------------------#
def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


#--------------------------------------------------------------------------------------------------------------#
# Écrit un fichier JSON de façon atomique (fichier temporaire + fsync + os.replace).                           #
#--------------------------------------------------------------------------------------------------------------#
def _atomic_write_json(path: str, data) -> None:
    _ensure_parent_dir(path)
    dirpath  = os.path.dirname(os.path.abspath(path))
    prefix   = os.path.basename(path) + "."
    fd, tmp  = tempfile.mkstemp(dir=dirpath, prefix=prefix, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        finally:
            raise


#--------------------------------------------------------------------------------------------------------------#
# Charge un JSON ; en cas de fichier illisible, garde une copie « .corrupt » et renvoie le défaut.             #
#--------------------------------------------------------------------------------------------------------------#
def _safe_load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        # JSON corrompu : on en garde une copie horodatée plutôt que de planter
        try:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            corrupt = f"{path}.corrupt-{ts}"
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                bad = f.read()
            with open(corrupt, "w", encoding="utf-8") as f:
                f.write(bad)
        except Exception:
            pass
        return default
    except Exception:
        raise


#--------------------------------------------------------------------------------------------------------------#
# Centralise la lecture et l'écriture des données persistantes (joueurs et meilleurs tours).                   #
#--------------------------------------------------------------------------------------------------------------#
class DataStore:

    #--------------------------------------------------------------------------------------------------------------#
    # Charge la liste des joueurs enregistrés.                                                                     #
    #--------------------------------------------------------------------------------------------------------------#
    @staticmethod
    def load_players():
        data = _safe_load_json(PLAYERS_PATH, default=[])
        if not isinstance(data, list):
            return []
        return [str(x) for x in data]

    #--------------------------------------------------------------------------------------------------------------#
    # Sauvegarde la liste des joueurs (dédupliquée, insensible à la casse, ordre d'apparition préservé).           #
    #--------------------------------------------------------------------------------------------------------------#
    @staticmethod
    def save_players(players: list[str]):
        if players is None:
            players = []
        if not isinstance(players, list):
            raise TypeError("players must be a list[str]")
        seen_lower = set()
        normalized = []
        for p in players:
            name = str(p).strip()
            if not name:
                continue
            key = name.lower()
            if key in seen_lower:
                continue
            seen_lower.add(key)
            normalized.append(name)
        _atomic_write_json(PLAYERS_PATH, normalized)

    #--------------------------------------------------------------------------------------------------------------#
    # Récupère le dictionnaire des meilleurs tours.                                                                #
    #--------------------------------------------------------------------------------------------------------------#
    @staticmethod
    def load_best_laps():
        data = _safe_load_json(BEST_LAPS_PATH, default={})
        if not isinstance(data, dict):
            return {}
        return data

    #--------------------------------------------------------------------------------------------------------------#
    # Normalise (clés en str, joueurs vides écartés) et sauvegarde les meilleurs tours.                            #
    #--------------------------------------------------------------------------------------------------------------#
    @staticmethod
    def save_best_laps(best_laps_dict):
        if not isinstance(best_laps_dict, dict):
            raise TypeError("best_laps_dict must be a dict")
        normalized = {}
        for k, v in best_laps_dict.items():
            k_str = str(k) if k is not None else "None"
            if isinstance(v, dict):
                inner = {}
                for p, pv in v.items():
                    if p is None or p == "---":
                        continue
                    inner[str(p)] = pv
                normalized[k_str] = inner
            else:
                normalized[k_str] = v
        _atomic_write_json(BEST_LAPS_PATH, normalized)

    #--------------------------------------------------------------------------------------------------------------#
    # Supprime un joueur et purge toutes ses entrées dans les meilleurs tours (insensible à la casse).             #
    #--------------------------------------------------------------------------------------------------------------#
    @staticmethod
    def delete_player(name: str):
        if not name:
            return
        # Retrait de players.json
        current = DataStore.load_players()
        target = str(name).strip().lower()
        kept = []
        for p in current:
            if str(p).strip().lower() != target:
                kept.append(p)
        if len(kept) != len(current):
            _atomic_write_json(PLAYERS_PATH, kept)
        # Purge de best_laps.json pour ce joueur
        bl = DataStore.load_best_laps()
        changed = False
        for combo_key, players_map in list(bl.items()):
            if isinstance(players_map, dict):
                new_map = {k: v for k, v in players_map.items() if str(k).strip().lower() != target}
                if len(new_map) != len(players_map):
                    bl[combo_key] = new_map
                    changed = True
        if changed:
            DataStore.save_best_laps(bl)
