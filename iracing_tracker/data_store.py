# data_store.py (simplifié, sans fallback)
import os
import sys
import json
import tempfile
from datetime import datetime

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

def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

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

def _safe_load_json(path: str, default):
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

class DataStore:
    @staticmethod
    def load_players():
        data = _safe_load_json(PLAYERS_PATH, default=[])
        if not isinstance(data, list):
            return []
        return [str(x) for x in data]

    @staticmethod
    def load_best_laps():
        data = _safe_load_json(BEST_LAPS_PATH, default={})
        if not isinstance(data, dict):
            return {}
        return data

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
