import os
import json
import tempfile
from datetime import datetime

def _module_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))

def _project_root() -> str:
    # dossier parent du package "iracing_tracker"
    return os.path.dirname(_module_dir())

# Dossier data au niveau racine du projet: C:\iracing_tracker\data
DATA_DIR = os.path.join(_project_root(), "data")

# Assure-toi que le dossier existe (créé au besoin)
os.makedirs(DATA_DIR, exist_ok=True)

PLAYERS_PATH   = os.path.join(DATA_DIR, "players.json")
BEST_LAPS_PATH = os.path.join(DATA_DIR, "best_laps.json")


def _ensure_parent_dir(path: str) -> None:
    """Crée le dossier parent si nécessaire (idempotent)."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def _atomic_write_json(path: str, data) -> None:
    """
    Écriture ATOMIQUE d'un JSON :
    - écrit dans un .tmp à côté
    - flush + fsync
    - os.replace(tmp -> path) (opération atomique)
    """
    _ensure_parent_dir(path)
    dirpath  = os.path.dirname(os.path.abspath(path))
    prefix   = os.path.basename(path) + "."
    fd, tmp  = tempfile.mkstemp(dir=dirpath, prefix=prefix, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            # JSON compact mais lisible ; ajuste si tu veux
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        # Remplacement atomique (POSIX & Windows 10+)
        os.replace(tmp, path)
    except Exception:
        # En cas d’erreur d’écriture, on tente de supprimer le .tmp
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        finally:
            raise


def _safe_load_json(path: str, default):
    """
    Lecture “robuste” :
    - si fichier absent → default
    - si JSON invalide → crée un backup .corrupt horodaté et retourne default
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        # Sauvegarde le fichier corrompu pour inspection
        try:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            corrupt = f"{path}.corrupt-{ts}"
            # Copie le texte brut pour debug
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                bad = f.read()
            with open(corrupt, "w", encoding="utf-8") as f:
                f.write(bad)
        except Exception:
            # On ignore les erreurs de backup ; le but est de continuer proprement
            pass
        # Repart sur un fichier propre
        return default
    except Exception:
        # Autre erreur I/O → on remonte l’exception (utile pour voir un vrai souci disque)
        raise


class DataStore:
    # ---------- PLAYERS ----------
    @staticmethod
    def load_players():
        """
        Retourne une LISTE de joueurs (ex: ["Nico", "Alex", ...]).
        Si le fichier n’existe pas / est corrompu → [].
        """
        data = _safe_load_json(PLAYERS_PATH, default=[])
        # Normalisation douce : on s’assure que c’est une liste de strings
        if not isinstance(data, list):
            return []
        return [str(x) for x in data]

    @staticmethod
    def save_players(players_list):
        """
        Écrit la liste des joueurs de manière atomique.
        """
        if not isinstance(players_list, list):
            raise TypeError("players_list must be a list")
        # (Optionnel) tri pour stabilité de diff Git
        _atomic_write_json(PLAYERS_PATH, list(players_list))

    # ---------- BEST LAPS ----------
    @staticmethod
    def load_best_laps():
        """
        Retourne un DICT de la forme:
        {
          "trackId|carId": {
             "Nico": {"time": 1.234, "date": "2025-10-05T21:35:12.345678"},
             "Alex": {...}
          },
          ...
        }
        Si le fichier n’existe pas / est corrompu → {}.
        """
        data = _safe_load_json(BEST_LAPS_PATH, default={})
        # Normalisation douce
        if not isinstance(data, dict):
            return {}
        return data

    @staticmethod
    def save_best_laps(best_laps_dict):
        """
        Écrit le dict des meilleurs temps de manière atomique,
        en normalisant les clés pour éviter None / non-string.
        """
        if not isinstance(best_laps_dict, dict):
            raise TypeError("best_laps_dict must be a dict")

        # Normalisation douce : top-level keys en str
        normalized = {}
        for k, v in best_laps_dict.items():
            k_str = str(k) if k is not None else "None"
            # Sous-dict: joueurs -> données
            if isinstance(v, dict):
                inner = {}
                for p, pv in v.items():
                    # skip joueurs invalides
                    if p is None or p == "---":
                        continue
                    inner[str(p)] = pv
                normalized[k_str] = inner
            else:
                normalized[k_str] = v

        _atomic_write_json(BEST_LAPS_PATH, normalized)
