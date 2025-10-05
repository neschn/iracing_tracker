import time
import threading
from datetime import datetime

from iracing_tracker.irsdk_client import IRClient
from iracing_tracker.lap_validator import LapValidator
from iracing_tracker.data_store import DataStore
from iracing_tracker.ui import TrackerUI

def loop(ir_client, ui, validator, best_laps):
    flag_waiting_for_session = False  # Permet de mémoriser si on as écrit dans les logs qu'on attend une session
    flag_waiting_for_pit = False     # Permet de mémoriser si on as écrit dans les logs qu'on attend d'aller dans les pits pour commencer
    waiting_for_pit = True

    track_id = None
    track_name = "---"
    car_id = None
    car_name = "---"


    # Variables à debugger en permanence
    debug_vars = [
        "SessionTime", "SessionNum", "SessionUniqueID", "CarIdxTrackSurface", "SessionTimeRemain",
        "CarIdxLapCompleted", "CarIdxLapLastLapInvalid",
        "LapLastLapTime", "CarIdxLapPct",
        "CarIdxTrackSurface", "CarIdxOnPitRoad",
        "CarIdxPosition", "CarIdxSpeed", "CarIdxRPM", "WeekendInfoTrackName", "WeekendInfo", "DriverInfo", "PlayerCarIdx", "PlayerCarMyIncidentCount", "PlayerTrackSurface",
        "WeekendInfoTrackID", "WeekendInfoTrackDisplayName", "carId", "carDisplayName"
    ]

    while True:
        # Lecture + affichage systématique du debug
        try:
            state_debug = ir_client.freeze_and_read(debug_vars)
        except Exception:
            state_debug = {}
        ui.update_debug({
            **state_debug,
            "flag_waiting_for_session": flag_waiting_for_session,
            "flag_waiting_for_pit": flag_waiting_for_pit,
            "waiting_for_pit": waiting_for_pit,
        })


        # Si pas de session active, on bloque tout et on vide le contexte
        if not ir_client.is_session_active():
            if not flag_waiting_for_session:
                ui.add_log("En attente du démarrage d’une session…")
                flag_waiting_for_session = True
                waiting_for_pit = True
            ui.update_context("---", "---", "---")
            ui.set_player_menu_state(False)
            time.sleep(0.1)
            continue

        # Reset du flag pour avertir qu'on attends une session
        flag_waiting_for_session = False

        # Récupère le YAML session + ton index de pilote en SAFE
        try:
            ctx = ir_client.freeze_and_read([
                "WeekendInfo",    # dict YAML du week-end
                "DriverInfo",     # dict YAML des pilotes
                "PlayerCarIdx"    # ton index dans la liste Drivers
            ]) or {}
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
        except Exception as e:
            ui.add_log(f"Erreur lecture contexte : {e}")
            track_id, track_name = None, "---"
            car_id, car_name = None, "---"

        ui.update_context(track_name, car_name)


        # Lecture SAFE de la surface de
        try:
            surface = ir_client.freeze_and_read(["PlayerTrackSurface"]).get("PlayerTrackSurface")
        except Exception:
            surface = None

        # Gestion du pit/garage
        if surface == 1 or surface == -1:
            ui.set_player_menu_state(True)
            if waiting_for_pit:
                ui.add_log("C'est parti, vous pouvez démarrer !")
                waiting_for_pit = False
        else:
            ui.set_player_menu_state(False)
            if waiting_for_pit:
                if not flag_waiting_for_pit:
                    ui.add_log("Veuillez rentrer au stand pour commencer.")
                    flag_waiting_for_pit = True
                time.sleep(0.1)
                continue

        player = ui.get_selected_player()

        # Affichage du meilleur temps du joueur 
        key = f"{track_id}|{car_id}"
        entry = best_laps.get(key, {}).get(player)
        personnal_best_str = f"{entry['time']:.3f}s" if entry else "---"
        ui.update_player_personnal_record(personnal_best_str)


        # Lecture SAFE pour le validateur
        try:
            lap_state = ir_client.freeze_and_read([
                "LapCompleted",
                "PlayerTrackSurface",
                "LapLastLapTime",
                "PlayerCarMyIncidentCount"
            ]) or {}
        except Exception:
            lap_state = {
                "LapCompleted": 0,
                "PlayerTrackSurface": 0,
                "LapLastLapTime": 0.0,
                "PlayerCarMyIncidentCount": 0
            }

       
        valid, lap_time = validator.update(lap_state)
        

        if valid:
            ui.add_log(f"Nouveau tour pour {player} : {lap_time:.3f}s")
            
            # On charge les meilleurs temps afin d'être sur d'avoir les derniers
            best_laps  = DataStore.load_best_laps()

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
                ui.add_log(f"Record personnel battu {player} : {lap_time:.3f}s")

        time.sleep(0.1)




def main():
    ir_client  = IRClient()
    validator  = LapValidator()
    best_laps  = DataStore.load_best_laps()
    players    = DataStore.load_players()

    ui = TrackerUI(players, lambda p: ui.add_log(f"Joueur sélectionné : {p}"))

    t = threading.Thread(
        target=loop,
        args=(ir_client, ui, validator, best_laps),
        daemon=True
    )
    t.start()
    ui.mainloop()

if __name__ == "__main__":
    main()
