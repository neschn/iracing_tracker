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

def loop(ir_client, ui_q, validator, best_laps, selected_player_ref, sel_lock):
    flag_waiting_for_session = False  # Permet de mémoriser si on as écrit dans les logs qu'on attend une session
    flag_waiting_for_pit = False     # Permet de mémoriser si on as écrit dans les logs qu'on attend d'aller dans les pits pour commencer
    waiting_for_pit = True
    context_ready = False

    track_id = None
    track_name = "---"
    car_id = None
    car_name = "---"


    # Debug LÉGER (tick ~10 Hz) — pas de YAML lourd ici
    debug_vars_light = [
        "SessionTime", "SessionNum", "SessionUniqueID", "SessionTimeRemain",
        "CarIdxLapCompleted", "CarIdxLapLastLapInvalid",
        "LapLastLapTime", "CarIdxLapPct",
        "CarIdxTrackSurface", "CarIdxOnPitRoad",
        "CarIdxPosition", "CarIdxSpeed", "CarIdxRPM",
        "PlayerCarMyIncidentCount", "PlayerTrackSurface",
    ]

    # Clés LOURDES (YAML) — lues moins souvent
    context_vars_heavy = ["WeekendInfo", "DriverInfo", "PlayerCarIdx"]

    # Throttle des lectures
    CTX_READ_PERIOD   = 2.0   # lecture YAML toutes les 2 s
    DEBUG_PUSH_PERIOD = 0.3   # push debug vers UI max ~3 Hz

    last_ctx_read_ts   = 0.0
    last_debug_push_ts = 0.0

    # Cache du contexte (évite de spammer l'UI si rien ne change)
    cached_track_id   = None
    cached_track_name = "---"
    cached_car_id     = None
    cached_car_name   = "---"


    while True:
        # Lecture + affichage systématique du debug
        now = time.time()

        # Lecture DEBUG légère (pas de YAML)
        try:
            state_debug = ir_client.freeze_and_read(debug_vars_light) or {}
        except Exception:
            state_debug = {}

        # Push du debug à l’UI au plus toutes les DEBUG_PUSH_PERIOD secondes
        if now - last_debug_push_ts >= DEBUG_PUSH_PERIOD:
            ui_q.put(("debug", {
                **state_debug,
                "flag_waiting_for_session": flag_waiting_for_session,
                "flag_waiting_for_pit": flag_waiting_for_pit,
                "waiting_for_pit": waiting_for_pit,
            }))
            last_debug_push_ts = now



        # Si pas de session active, on bloque tout et on vide le contexte
        if not ir_client.is_session_active():
            if not flag_waiting_for_session:
                ui_q.put(("log", {"message": "En attente du démarrage d’une session…"}))
                flag_waiting_for_session = True
                waiting_for_pit = True
                # Vide le contexte une seule fois
                cached_track_id, cached_track_name = None, "---"
                cached_car_id,   cached_car_name   = None, "---"
                context_ready = False
                ui_q.put(("context", {"track": "---", "car": "---"}))
                ui_q.put(("player_best", {"text": "---"}))
                
                # Forcer un reset du buffer IRSDK (purge de l'ancien contexte)
                try:
                    ir_client.ir.shutdown()
                except Exception:
                    pass

            ui_q.put(("player_menu_state", {"enabled": False}))
            time.sleep(0.1)
            continue


        # Reset du flag pour avertir qu'on attends une session
        flag_waiting_for_session = False

        # Lecture du CONTEXTE LOURD (YAML) toutes les CTX_READ_PERIOD secondes
        if now - last_ctx_read_ts >= CTX_READ_PERIOD:
            try:
                ctx = ir_client.freeze_and_read(context_vars_heavy) or {}
                weekend = ctx.get("WeekendInfo") or {}
                track_id = weekend.get("TrackID")
                track_name = weekend.get("TrackDisplayName", "---")

                drivers = ctx.get("DriverInfo", {}).get("Drivers", [])
                idx = ctx.get("PlayerCarIdx") or 0
                if 0 <= idx < len(drivers):
                    car_info = drivers[idx]
                    car_id = car_info.get("CarID")
                    car_name = car_info.get("CarScreenName", "---")
                else:
                    car_id, car_name = None, "---"

                last_ctx_read_ts = now

                # N’envoie à l’UI que si le contexte a changé
                if (track_id != cached_track_id) or (car_id != cached_car_id) \
                   or (track_name != cached_track_name) or (car_name != cached_car_name):
                    cached_track_id, cached_track_name = track_id, track_name
                    cached_car_id,   cached_car_name   = car_id, car_name
                    context_ready = (track_id is not None) and (car_id is not None)
                    ui_q.put(("context", {"track": track_name, "car": car_name}))
                    # Recalcule immédiatement le record affiché pour le joueur courant
                    with sel_lock:
                        player_curr = selected_player_ref["name"]
                    if context_ready and player_curr and player_curr != "---":
                        key = f"{track_id}|{car_id}"
                        entry = best_laps.get(key, {}).get(player_curr)
                        best_text = f"{entry['time']:.3f}s" if entry else "---"
                    else:
                        best_text = "---"
                    ui_q.put(("player_best", {"text": best_text}))

            except Exception as e:
                ui_q.put(("log", {"message": f"Erreur lecture contexte : {e}"}))
                # On ne touche pas le cache en cas d’erreur



        # Lecture SAFE de la surface de
        try:
            surface = ir_client.freeze_and_read(["PlayerTrackSurface"]).get("PlayerTrackSurface")
        except Exception:
            surface = None

        # Gestion du pit/garage (surface: 1=garage/pitbox, 2=pit lane, 3=piste)
        if surface == 1:
            # Autorise la sélection du joueur et signale que c'est prêt à rouler
            ui_q.put(("player_menu_state", {"enabled": True}))
            if waiting_for_pit:
                ui_q.put(("log", {"message": "C’est parti, vous pouvez démarrer !"}))
                waiting_for_pit = False
        else:
            # Désactive la sélection du joueur dès qu’on quitte le stand
            ui_q.put(("player_menu_state", {"enabled": False}))
            if waiting_for_pit:
                if not flag_waiting_for_pit:
                    ui_q.put(("log", {"message": "Veuillez rentrer au stand pour commencer."}))
                    flag_waiting_for_pit = True
                time.sleep(0.1)
                continue

        with sel_lock:
            player = selected_player_ref["name"]
        
        # Ne rien enregistrer si joueur invalide
        if not player or player == "---":
            # Pas de log ici pour éviter le spam ; on se contente d'ignorer le tour
            time.sleep(0.1)
            continue


        # Affichage du meilleur temps du joueur (protégé par le contexte prêt)
        if context_ready:
            key = f"{track_id}|{car_id}"
            entry = best_laps.get(key, {}).get(player)
            personnal_best_str = f"{entry['time']:.3f}s" if entry else "---"
        else:
            personnal_best_str = "---"
        ui_q.put(("player_best", {"text": personnal_best_str}))


        # Lecture SAFE pour le validateur
        try:
            raw = ir_client.freeze_and_read([
                "LapCompleted",
                "PlayerTrackSurface",
                "LapLastLapTime",
                "PlayerCarMyIncidentCount"
            ]) or {}
        except Exception:
            raw = {}
        lap_state = _normalize_lap_state(raw)

       
        status, lap_time = validator.update(lap_state)

        if status == "valid" and context_ready:
            ui_q.put(("log", {"message": f"Nouveau tour pour {player} : {lap_time:.3f}s"}))

            # On charge les meilleurs temps afin d'être sûr d'avoir les derniers
            best_laps = DataStore.load_best_laps()

            # On utilise track_id|car_id comme clé unique
            key = f"{track_id}|{car_id}"

            # Crée la structure si nécessaire
            times = best_laps.setdefault(key, {})

            # Ancien record pour ce joueur
            prev = times.get(player)
            if prev is None or lap_time < prev["time"]:
                # On stocke uniquement l'ID, le temps, la date
                times[player] = {
                    "time": lap_time,
                    "date": datetime.now().isoformat(),
                }
                DataStore.save_best_laps(best_laps)
                ui_q.put(("log", {"message": f"Record personnel battu {player} : {lap_time:.3f}s"}))

        elif status == "invalid":
            # Tour franchi mais temps invalide (iRacing renvoie souvent -1, 0 ou répète le précédent)
            ui_q.put(("log", {"message": f"Nouveau tour pour {player} : Temps invalide"}))


        time.sleep(0.1)




def main():
    ir_client  = IRClient()
    validator  = LapValidator()
    best_laps  = DataStore.load_best_laps()

    players = DataStore.load_players()

    # 1) Crée l'UI sans callback (temporaire)
    ui = TrackerUI(players, lambda p: None)

    # ---- ÉTAT JOUEUR SÉLECTIONNÉ (thread-safe) ----
    selected_player = {"name": players[0] if players else "---"}
    sel_lock = threading.Lock()

    def on_player_change(p):
        # MAJ de l'état partagé (worker lira cette valeur)
        with sel_lock:
            selected_player["name"] = p
        # Ce log est dans le thread Tk (safe)
        ui.add_log(f"Joueur sélectionné : {p}")

    ui.set_on_player_change(on_player_change)
    

    # 3) Prépare la queue d’événements UI et branche la pompe .after()
    ui_event_queue = queue.Queue()
    ui.bind_event_queue(ui_event_queue)

    # 4) Lance le worker (pas d'appels Tk dans ce thread)
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

