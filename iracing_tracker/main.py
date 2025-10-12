import time
import queue
import threading
from datetime import datetime

from iracing_tracker.irsdk_client import IRClient
from iracing_tracker.lap_validator import LapValidator
from iracing_tracker.data_store import DataStore
from iracing_tracker.ui import TrackerUI


def fmt_lap(t: float) -> str:
    """Format commun: M:SS.mmm ; '---' si invalide."""
    if not t or t <= 0:
        return "---"
    m, s = divmod(float(t), 60.0)
    return f"{int(m)}:{s:06.3f}"


def loop(ir_client, ui_q, validator, best_laps, selected_player_ref, sel_lock, runtime_flags, flags_lock):
    # ---- Flags d'état généraux ----
    is_waiting_session_msg_sent = False    
    session_start_msg_sent = False
    context_ready = False


    # ---- Contexte courant ----
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

    # --- Télémetrie: listes de variables ---
    CORE_VARS = [
        # nécessaires au fonctionnement toujours
        "LapCompleted",
        "LapLastLapTime",
        "PlayerTrackSurface",
        "PlayerCarMyIncidentCount",
    ]

    DEBUG_VARS_VERBOSE = [
        # variables “bonus” pour debug (coûteuses / arrays)
        "SessionTime", "SessionNum", "SessionTimeRemain",
        "CarIdxLapCompleted", "CarIdxLastLapTime",
        "CarIdxLapDistPct", "CarIdxTrackSurface",
        "CarIdxOnPitRoad", "CarIdxPosition", "CarIdxSpeed", "CarIdxRPM",
    ]

    # YAML lourd ponctuel
    context_vars_heavy = ["WeekendInfo", "DriverInfo", "PlayerCarIdx"]

    # Throttles
    CTX_READ_PERIOD   = 2.0
    DEBUG_PUSH_PERIOD = 0.3

    last_ctx_read_ts   = 0.0
    last_debug_push_ts = 0.0

    # ---- Helpers internes ----

    def _reset_context_and_ui():
        nonlocal cached_track_id, cached_track_name, cached_car_id, cached_car_name
        nonlocal context_ready, last_best_text
        cached_track_id, cached_track_name = None, "---"
        cached_car_id,   cached_car_name   = None, "---"
        context_ready = False
        last_best_text = None
        ui_q.put(("context", {"track": "---", "car": "---"}))
        ui_q.put(("player_best", {"text": "---"}))

    def _handle_session_not_active():
        nonlocal is_waiting_session_msg_sent, session_start_msg_sent
        if not is_waiting_session_msg_sent:
            ui_q.put(("log", {"message": "En attente du démarrage d’une session…"}))
            is_waiting_session_msg_sent = True
            session_start_msg_sent = False
            ui_q.put(("debug", {}))     # vider la zone Debug
            validator.reset()           # repartir proprement côté tours
            _reset_context_and_ui()
            try:
                ir_client.ir.shutdown()
            except Exception:
                pass
        # Hors session: autoriser le changement de joueur
        ui_q.put(("player_menu_state", {"enabled": True}))


    def _maybe_update_context(now_ts):
        nonlocal last_ctx_read_ts, track_id, track_name, car_id, car_name
        nonlocal cached_track_id, cached_track_name, cached_car_id, cached_car_name, context_ready, last_best_text
        nonlocal session_start_msg_sent

        if now_ts - last_ctx_read_ts < CTX_READ_PERIOD:
            return

        ctx = ir_client.freeze_and_read(context_vars_heavy) or {}
        weekend = ctx.get("WeekendInfo") or {}
        track_id = weekend.get("TrackID")
        base_track_name = weekend.get("TrackDisplayName", "---")
        track_cfg = (weekend.get("TrackConfigName") or "").strip()
        track_name = f"{base_track_name} ({track_cfg})" if track_cfg else base_track_name

        drivers = ctx.get("DriverInfo", {}).get("Drivers", [])
        idx = int(ctx.get("PlayerCarIdx") or 0)
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
            last_best_text = None  # force une MAJ du label

            # Message unique de démarrage de session
            if context_ready and not session_start_msg_sent:
                ui_q.put(("log", {"message": f"Nouvelle session démarrée : {track_name} - {car_name}"}))
                session_start_msg_sent = True


    def _update_best_label_if_changed():
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

    # ---- Boucle principale ----
    while True:
        now = time.time()

        # lecture “core” à 10 Hz env
        try:
            state_core = ir_client.freeze_and_read(CORE_VARS) or {}
        except Exception:
            state_core = {}

        # session inactive -> attente
        if not ir_client.is_session_active():
            _handle_session_not_active()
            time.sleep(0.1)
            continue

        # Reset du flag informant qu'on attend le démarrage d'une session
        if is_waiting_session_msg_sent:
            is_waiting_session_msg_sent = False

        # contexte YAML ponctuel
        try:
            _maybe_update_context(now)
        except Exception as e:
            ui_q.put(("log", {"message": f"Erreur lecture contexte : {e}"}))

        # lecture / push DEBUG uniquement si visible
        with flags_lock:
            debug_enabled = bool(runtime_flags.get("debug_enabled", False))

        if debug_enabled and (now - last_debug_push_ts) >= DEBUG_PUSH_PERIOD:
            try:
                dbg = ir_client.freeze_and_read(DEBUG_VARS_VERBOSE) or {}
            except Exception:
                dbg = {}
            payload = {
                **state_core,
                **dbg,
                "is_waiting_session_msg_sent": is_waiting_session_msg_sent,
                "session_start_msg_sent": session_start_msg_sent,
            }
            ui_q.put(("debug", payload))
            last_debug_push_ts = now

        # gestion pit/garage (surface: -1=au démarrage, avant d'aller au garage 0=hors des track limit, 1=pitstall/garage, 2= dans la pitlane, 3=sur la piste)
        surface = int(state_core.get("PlayerTrackSurface") or 0)
        ui_q.put(("player_menu_state", {"enabled": surface in (1, -1)}))


        # coalescing du label “record personnel”
        _update_best_label_if_changed()

        # joueur courant
        with sel_lock:
            player = selected_player_ref["name"]
        if not player or player == "---":
            time.sleep(0.1)
            continue

        # validator
        lap_state = {
            "LapCompleted": state_core.get("LapCompleted"),
            "PlayerTrackSurface": state_core.get("PlayerTrackSurface"),
            "LapLastLapTime": state_core.get("LapLastLapTime"),
            "PlayerCarMyIncidentCount": state_core.get("PlayerCarMyIncidentCount"),
        }

        status, lap_time = validator.update(lap_state)

        if status == "valid" and context_ready:
            ui_q.put(("log", {"message": f"Nouveau tour pour {player} : {fmt_lap(lap_time)}"}))
            best_laps = DataStore.load_best_laps()
            key = f"{track_id}|{car_id}"
            times = best_laps.setdefault(key, {})
            prev = times.get(player)
            if prev is None or lap_time < prev["time"]:
                times[player] = {"time": lap_time, "date": datetime.now().isoformat()}
                DataStore.save_best_laps(best_laps)
                ui_q.put(("log", {"message": f"Record personnel battu {player} : {fmt_lap(lap_time)}"}))
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

    runtime_flags = {"debug_enabled": ui.debug_visible.get()}
    flags_lock = threading.Lock()

    def on_debug_toggle(visible: bool):
        with flags_lock:
            runtime_flags["debug_enabled"] = bool(visible)

    ui.set_on_debug_toggle(on_debug_toggle)

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
        args=(ir_client, ui_event_queue, validator, best_laps, selected_player, sel_lock, runtime_flags, flags_lock),
        daemon=True
    )

    t.start()

    # 5) Boucle Tk
    ui.mainloop()


if __name__ == "__main__":
    main()
