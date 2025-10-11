import os
import sys
import json
import tempfile
from datetime import datetime

# ---------------------------
# Localisation des données
# ---------------------------

def _module_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))

def _project_root() -> str:
    # dossier parent du package "iracing_tracker"
    return os.path.dirname(_module_dir())

def _user_data_dir() -> str:
    """
    Retourne un dossier de données utilisateur cross‑platform.
    Windows : %LOCALAPPDATA%\\iRacingTracker
    macOS   : ~/Library/Application Support/iRacingTracker
    Linux   : $XDG_DATA_HOME/iracing_tracker ou ~/.local/share/iracing_tracker
    """
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

# Nouveau dossier "officiel" de données
DATA_DIR = _user_data_dir()
os.makedirs(DATA_DIR, exist_ok=True)

# Dossier legacy à la racine du projet (fallback lecture)
LEGACY_DATA_DIR = os.path.join(_project_root(), "data")

PLAYERS_PATH           = os.path.join(DATA_DIR, "players.json")
BEST_LAPS_PATH         = os.path.join(DATA_DIR, "best_laps.json")
LEGACY_PLAYERS_PATH    = os.path.join(LEGACY_DATA_DIR, "players.json")
LEGACY_BEST_LAPS_PATH  = os.path.join(LEGACY_DATA_DIR, "best_laps.json")


# ---------------------------
# I/O utilitaires
# ---------------------------

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


# ---------------------------
# API données
# ---------------------------

class DataStore:
    # ---------- PLAYERS ----------
    @staticmethod
    def load_players():
        """
        Retourne une LISTE de joueurs (ex: ["Nico", "Alex", ...]).
        Fallback : si le fichier n’existe pas dans DATA_DIR, on tente LEGACY_DATA_DIR.
        """
        # Essaye d'abord l'emplacement utilisateur
        if os.path.exists(PLAYERS_PATH):
            data = _safe_load_json(PLAYERS_PATH, default=[])
        # Sinon, fallback legacy (projet)
        elif os.path.exists(LEGACY_PLAYERS_PATH):
            data = _safe_load_json(LEGACY_PLAYERS_PATH, default=[])
        else:
            data = []

        if not isinstance(data, list):
            return []
        return [str(x) for x in data]

    @staticmethod
    def save_players(players_list):
        """Écrit la liste des joueurs de manière atomique dans DATA_DIR."""
        if not isinstance(players_list, list):
            raise TypeError("players_list must be a list")
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
        Fallback : tente LEGACY si DATA_DIR est vide.
        """
        if os.path.exists(BEST_LAPS_PATH):
            data = _safe_load_json(BEST_LAPS_PATH, default={})
        elif os.path.exists(LEGACY_BEST_LAPS_PATH):
            data = _safe_load_json(LEGACY_BEST_LAPS_PATH, default={})
        else:
            data = {}

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
