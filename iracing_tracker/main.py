import time
import queue
import threading
from datetime import datetime

from iracing_tracker.irsdk_client import IRClient
from iracing_tracker.lap_validator import LapValidator
from iracing_tracker.data_store import DataStore
from iracing_tracker.ui import TrackerUI

# --- Helpers ---

def _normalize_lap_state(raw):
    """Return a dict with numeric, non-None values for the validator."""
    if not isinstance(raw, dict):
        raw = {}
    def _to_int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0
    def _to_float(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0
    return {
        "LapCompleted": _to_int(raw.get("LapCompleted")),
        "PlayerTrackSurface": _to_int(raw.get("PlayerTrackSurface")),
        "LapLastLapTime": _to_float(raw.get("LapLastLapTime")),
        "PlayerCarMyIncidentCount": _to_int(raw.get("PlayerCarMyIncidentCount")),
    }

def fmt_lap(t: float) -> str:
    """Format commun: M:SS.mmm ; '---' si invalide."""
    if not t or t <= 0:
        return "---"
    m, s = divmod(float(t), 60.0)
    return f"{int(m)}:{s:06.3f}"


def loop(ir_client, ui_q, validator, best_laps, selected_player_ref, sel_lock):
    # ---- Flags d'état généraux ----
    flag_waiting_for_session = False
    waiting_for_pit = True
    flag_waiting_for_pit = False
    context_ready = False

    # ---- Contexte courant mis en cache ----
    track_id = None
    track_name = "---"
    car_id = None
    car_name = "---"

    cached_track_id   = None
    cached_track_name = "---"
    cached_car_id     = None
    cached_car_name   = "---"

    # Coalescing UI
    last_best_text = None

    # Détection des changements de session
    last_session_uid = None

    # Debug LÉGER (tick ~10 Hz) — pas de gros arrays CarIdx*
    debug_vars_light = [
        "SessionTime", "SessionNum", "SessionUniqueID", "SessionTimeRemain",
        "LapCompleted", "LapLastLapTime",
        "PlayerCarMyIncidentCount", "PlayerTrackSurface",
    ]

    # Clés LOURDES (YAML) — lues moins souvent
    context_vars_heavy = ["WeekendInfo", "DriverInfo", "PlayerCarIdx"]

    # Throttle des lectures
    CTX_READ_PERIOD   = 2.0   # lecture YAML toutes les 2 s
    DEBUG_PUSH_PERIOD = 0.3   # push debug vers UI max ~3 Hz

    last_ctx_read_ts   = 0.0
    last_debug_push_ts = 0.0

    # ---- Fonctions internes (lisibilité) ----

    def _push_debug(now_ts, state_debug):
        nonlocal last_debug_push_ts
        if now_ts - last_debug_push_ts < DEBUG_PUSH_PERIOD:
            return
        ui_q.put(("debug", {
            **(state_debug or {}),
            "flag_waiting_for_session": flag_waiting_for_session,
            "flag_waiting_for_pit": flag_waiting_for_pit,
            "waiting_for_pit": waiting_for_pit,
        }))
        last_debug_push_ts = now_ts

    def _reset_context_and_ui():
        """Vide le contexte UI + reset affichage best lap."""
        nonlocal cached_track_id, cached_track_name, cached_car_id, cached_car_name
        nonlocal context_ready, last_best_text
        cached_track_id, cached_track_name = None, "---"
        cached_car_id,   cached_car_name   = None, "---"
        context_ready = False
        last_best_text = None
        ui_q.put(("context", {"track": "---", "car": "---"}))
        ui_q.put(("player_best", {"text": "---"}))

    def _handle_session_not_active():
        """État 'en attente de session' : reset flags et buffer iRSDK."""
        nonlocal flag_waiting_for_session, waiting_for_pit, flag_waiting_for_pit, last_session_uid
        if not flag_waiting_for_session:
            ui_q.put(("log", {"message": "En attente du démarrage d’une session…"}))
            flag_waiting_for_session = True
            waiting_for_pit = True
            flag_waiting_for_pit = False  # réarmement
            _reset_context_and_ui()
            try:
                ir_client.ir.shutdown()  # purge de l'ancien contexte iRSDK
            except Exception:
                pass
        last_session_uid = None
        ui_q.put(("player_menu_state", {"enabled": False}))

    def _maybe_update_context(now_ts):
        """Lit ponctuellement le YAML et met à jour le contexte piste/voiture."""
        nonlocal last_ctx_read_ts, track_id, track_name, car_id, car_name
        nonlocal cached_track_id, cached_track_name, cached_car_id, cached_car_name, context_ready, last_best_text

        if now_ts - last_ctx_read_ts < CTX_READ_PERIOD:
            return

        ctx = ir_client.freeze_and_read(context_vars_heavy) or {}
        weekend = ctx.get("WeekendInfo") or {}
        track_id = weekend.get("TrackID")
        base_track_name = weekend.get("TrackDisplayName", "---")
        track_cfg = (weekend.get("TrackConfigName") or "").strip()
        track_name = f"{base_track_name} ({track_cfg})" if track_cfg else base_track_name

        drivers = ctx.get("DriverInfo", {}).get("Drivers", [])
        idx = ctx.get("PlayerCarIdx") or 0
        if 0 <= idx < len(drivers):
            car_info = drivers[idx]
            car_id = car_info.get("CarID")
            car_name = car_info.get("CarScreenName", "---")
        else:
            car_id, car_name = None, "---"

        last_ctx_read_ts = now_ts

        if (track_id != cached_track_id) or (car_id != cached_car_id) \
           or (track_name != cached_track_name) or (car_name != cached_car_name):
            cached_track_id, cached_track_name = track_id, track_name
            cached_car_id,   cached_car_name   = car_id, car_name
            context_ready = (track_id is not None) and (car_id is not None)
            ui_q.put(("context", {"track": track_name, "car": car_name}))
            # invalide la coalescence du best lap pour forcer 1 affichage correct
            last_best_text = None

    def _update_best_label_if_changed():
        """Met à jour l'étiquette 'Record personnel' si nécessaire (coalescing)."""
        nonlocal last_best_text
        with sel_lock:
            player_curr = selected_player_ref["name"]
        if not context_ready or not player_curr or player_curr == "---":
            best_text = "---"
        else:
            key = f"{track_id}|{car_id}"
            entry = best_laps.get(key, {}).get(player_curr)
            best_text = fmt_lap(entry["time"]) if entry else "---"

        if best_text != last_best_text:
            ui_q.put(("player_best", {"text": best_text}))
            last_best_text = best_text

    # ---- Boucle de travail ----
    while True:
        now = time.time()

        # Lecture DEBUG légère (pas de YAML)
        try:
            state_debug = ir_client.freeze_and_read(debug_vars_light) or {}
        except Exception:
            state_debug = {}

        # Détection de changement de session (à chaud)
        curr_uid = state_debug.get("SessionUniqueID")
        if curr_uid and last_session_uid and curr_uid != last_session_uid:
            ui_q.put(("log", {"message": "Changement de session détecté, reset iRSDK…"}))
            try:
                ir_client.ir.shutdown()
            except Exception:
                pass
            validator.reset()
            waiting_for_pit = True
            flag_waiting_for_pit = False
            _reset_context_and_ui()

        if curr_uid:
            last_session_uid = curr_uid

        # Push debug throttle
        _push_debug(now, state_debug)

        # Si pas de session active -> état attente
        if not ir_client.is_session_active():
            _handle_session_not_active()
            time.sleep(0.1)
            continue

        # Session active : on enlève le flag d'attente
        flag_waiting_for_session = False

        # Lecture du CONTEXTE (YAML) ponctuelle
        try:
            _maybe_update_context(now)
        except Exception as e:
            ui_q.put(("log", {"message": f"Erreur lecture contexte : {e}"}))

        # Gestion du pit/garage via la lecture légère
        surface = state_debug.get("PlayerTrackSurface")
        if surface == 1:
            # autorise la sélection du joueur et signale que c'est prêt à rouler
            ui_q.put(("player_menu_state", {"enabled": True}))
            if waiting_for_pit:
                ui_q.put(("log", {"message": "C’est parti, vous pouvez démarrer !"}))
                waiting_for_pit = False
                flag_waiting_for_pit = False
        else:
            ui_q.put(("player_menu_state", {"enabled": False}))
            if waiting_for_pit and not flag_waiting_for_pit:
                ui_q.put(("log", {"message": "Veuillez rentrer au stand pour commencer."}))
                flag_waiting_for_pit = True
            if waiting_for_pit:
                time.sleep(0.1)
                continue

        # Mise à jour coalescée du libellé 'Record personnel'
        _update_best_label_if_changed()

        # Prépare l'état pour le validateur depuis la lecture légère
        lap_state = _normalize_lap_state({
            "LapCompleted": state_debug.get("LapCompleted"),
            "PlayerTrackSurface": state_debug.get("PlayerTrackSurface"),
            "LapLastLapTime": state_debug.get("LapLastLapTime"),
            "PlayerCarMyIncidentCount": state_debug.get("PlayerCarMyIncidentCount"),
        })

        # Joueur courant
        with sel_lock:
            player = selected_player_ref["name"]
        if not player or player == "---":
            time.sleep(0.1)
            continue

        # Résolution du tour
        status, lap_time = validator.update(lap_state)

        if status == "valid" and context_ready:
            ui_q.put(("log", {"message": f"Nouveau tour pour {player} : {fmt_lap(lap_time)}"}))

            # Recharger les bests (garantit qu'on a la version la plus fraîche)
            best_laps = DataStore.load_best_laps()

            key = f"{track_id}|{car_id}"
            times = best_laps.setdefault(key, {})

            prev = times.get(player)
            if prev is None or lap_time < prev["time"]:
                times[player] = {"time": lap_time, "date": datetime.now().isoformat()}
                DataStore.save_best_laps(best_laps)
                ui_q.put(("log", {"message": f"Record personnel battu {player} : {fmt_lap(lap_time)}"}))
                # Forcer la MAJ du label (coalescing se recalculera)
                _update_best_label_if_changed()

        elif status == "invalid":
            ui_q.put(("log", {"message": f"Nouveau tour pour {player} : Temps invalide"}))

        time.sleep(0.1)


def main():
    ir_client  = IRClient()
    validator  = LapValidator()
    best_laps  = DataStore.load_best_laps()
    players    = DataStore.load_players()

    # 1) Crée l'UI sans callback (temporaire)
    ui = TrackerUI(players, lambda p: None)

    # ---- ÉTAT JOUEUR SÉLECTIONNÉ (thread-safe) ----
    selected_player = {"name": players[0] if players else "---"}
    sel_lock = threading.Lock()

    def on_player_change(p):
        with sel_lock:
            selected_player["name"] = p
        ui.add_log(f"Joueur sélectionné : {p}")

    ui.set_on_player_change(on_player_change)

    # 3) Queue d’événements UI + pompe .after()
    ui_event_queue = queue.Queue()
    ui.bind_event_queue(ui_event_queue)

    # 4) Lance le worker
    t = threading.Thread(
        target=loop,
        args=(ir_client, ui_event_queue, validator, best_laps, selected_player, sel_lock),
        daemon=True
    )
    t.start()

    # 5) Boucle Tk
    ui.mainloop()


if __name__ == "__main__":
    main()
