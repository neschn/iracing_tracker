################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/main.py                                                                            #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Coordonne la collecte iRacing, la validation des tours et l'interface graphique.               #
################################################################################################################

import time
import queue
import threading

from iracing_tracker.irsdk_client import IRClient
from iracing_tracker.lap_validator import LapValidator
from iracing_tracker.data_store import DataStore
from iracing_tracker.ui import TrackerUI

from iracing_tracker.session_manager import SessionManager
from iracing_tracker.telemetry_reader import TelemetryReader
from iracing_tracker.record_manager import RecordManager, format_lap_time
from iracing_tracker.ui_bridge import UIBridge


#--------------------------------------------------------------------------------------------------------------#
# Boucle principale (thread worker) : lecture télémétrie → validation des tours → mise à jour de l'UI.         #
#--------------------------------------------------------------------------------------------------------------#
def loop(ir_client, ui_bridge, validator, session_manager, telemetry_reader,
         record_manager, selected_player_ref, sel_lock, runtime_flags, flags_lock):
    last_laps_feed = []

    while True:
        # 1) Lecture core en premier : CRITIQUE, c'est elle qui initialise la connexion iRSDK,
        #    donc elle DOIT précéder is_session_active().
        try:
            state_core = telemetry_reader.read_core(force=True) or {}
        except Exception:
            state_core = {}

        # 2) Vérifier si une session est active (après la lecture core)
        if not session_manager.is_active():
            _handle_session_inactive(ir_client, ui_bridge, validator, session_manager, telemetry_reader)
            if last_laps_feed:
                last_laps_feed.clear()
                ui_bridge.update_last_laps([])
            time.sleep(0.1)
            continue

        # 3) Session active : effacer le message d'attente
        if session_manager.is_waiting_session_msg_sent:
            session_manager.is_waiting_session_msg_sent = False
            ui_bridge.show_banner_message("clear")

        # 4) Lecture et mise à jour du contexte (forcée tant qu'on n'a pas de contexte valide)
        try:
            force_context_read = not session_manager.context.is_ready
            context_data = telemetry_reader.read_context(force=force_context_read)

            if context_data:
                context_changed = session_manager.update_context(context_data)

                if context_changed:
                    ui_bridge.update_context(
                        session_manager.context.track_name,
                        session_manager.context.car_name,
                        session_manager.context.track_id,
                        session_manager.context.car_id,
                    )
                    # Forcer la MAJ du record affiché et recharger les records du disque
                    ui_bridge.reset_coalescing()
                    record_manager.reload()

                # Message « session démarrée » (une seule fois)
                if session_manager.should_send_session_started_message():
                    track = session_manager.context.track_name
                    track_id = session_manager.context.track_id
                    car = session_manager.context.car_name
                    car_id = session_manager.context.car_id
                    if track_id is not None and car_id is not None:
                        ui_bridge.log(f"Nouvelle session démarrée : {track} - N° {track_id} - {car} - N° {car_id}")
                    elif track_id is not None:
                        ui_bridge.log(f"Nouvelle session démarrée : {track} - N° {track_id} - {car}")
                    elif car_id is not None:
                        ui_bridge.log(f"Nouvelle session démarrée : {track} - {car} - N° {car_id}")
                    else:
                        ui_bridge.log(f"Nouvelle session démarrée : {track} - {car}")
                    session_manager.mark_session_started_message_sent()

                    # Classement initial
                    ranking = record_manager.get_ranking(
                        session_manager.context.track_id,
                        session_manager.context.car_id,
                        limit=3
                    )
                    ui_bridge.update_ranking(ranking)

        except Exception as e:
            ui_bridge.log(f"Erreur lecture contexte : {e}")

        # 5) Lecture debug (si la zone est activée)
        with flags_lock:
            debug_enabled = bool(runtime_flags.get("debug_enabled", False))

        if debug_enabled:
            debug_data = telemetry_reader.read_debug()
            if debug_data:
                # Fusionner avec les valeurs core et ajouter les flags de session
                merged_debug = {**state_core, **debug_data}
                merged_debug["is_waiting_session_msg_sent"] = session_manager.is_waiting_session_msg_sent
                merged_debug["session_start_msg_sent"] = session_manager.session_start_msg_sent
                ui_bridge.update_debug(merged_debug)

        # 5bis) Horloge de session → UI (valeur core 10 Hz, coalescée à 1 s côté UI)
        try:
            ui_bridge.update_session_time(state_core.get("SessionTime"))
        except Exception:
            pass

        # 6) Pit/garage : activer/désactiver le sélecteur de joueur
        surface = int(state_core.get("PlayerTrackSurface") or 0)
        ui_bridge.set_player_menu_state(surface in (1, -1))

        # 7) Mise à jour du record personnel du joueur sélectionné
        with sel_lock:
            player = selected_player_ref["name"]

        if player and player != "---" and session_manager.context.is_ready:
            best_text = record_manager.get_personal_best_formatted(
                player,
                session_manager.context.track_id,
                session_manager.context.car_id
            )
            ui_bridge.update_player_best(best_text)
        else:
            ui_bridge.update_player_best("---")

        # 8) Validation du tour
        if not player or player == "---":
            time.sleep(0.1)
            continue

        lap_state = {
            "LapCompleted": state_core.get("LapCompleted"),
            "PlayerTrackSurface": state_core.get("PlayerTrackSurface"),
            "LapLastLapTime": state_core.get("LapLastLapTime"),
            "PlayerCarMyIncidentCount": state_core.get("PlayerCarMyIncidentCount"),
        }

        status, lap_time, reason = validator.update(lap_state)

        # 9) Sauvegarde si le tour est valide
        if status == "valid" and session_manager.context.is_ready:
            is_personal, is_absolute = record_manager.save_lap(
                player,
                session_manager.context.track_id,
                session_manager.context.car_id,
                lap_time
            )

            # Log et bannière selon le type de record
            if is_absolute:
                suffix = " (record absolu battu)"
                ui_bridge.show_banner_message("absolute_record")
            elif is_personal:
                suffix = " (record personnel battu)"
                ui_bridge.show_banner_message("personal_record")
            else:
                suffix = ""
            ui_bridge.log(f"Nouveau tour pour {player} : {format_lap_time(lap_time)}{suffix}")

            # Classement en temps réel
            ranking = record_manager.get_ranking(
                session_manager.context.track_id,
                session_manager.context.car_id,
                limit=3
            )
            ui_bridge.update_ranking(ranking)

            # Alimenter la liste des temps de la session (plus récent en bas)
            try:
                lap_no = int(state_core.get("LapCompleted") or 0)
            except Exception:
                lap_no = 0
            last_laps_feed.append(f"{lap_no}\t{format_lap_time(lap_time)}\t{player}")
            ui_bridge.update_last_laps(last_laps_feed)

        elif status == "invalid":
            # Messages selon la raison d'invalidité
            if reason == "out_lap":
                ui_bridge.log(f"Nouveau tour pour {player} : tour sortie des stands")
                try:
                    lap_no = int(state_core.get("LapCompleted") or 0)
                except Exception:
                    lap_no = 0
                last_laps_feed.append(f"{lap_no}\tTour sortie des stands\t{player}")
            elif reason and reason.startswith("flag_and_incidents:"):
                x_count = reason.split(":")[1]
                ui_bridge.log(f"Nouveau tour pour {player} : tour invalide (drapeau - {x_count}x)")
                try:
                    lap_no = int(state_core.get("LapCompleted") or 0)
                except Exception:
                    lap_no = 0
                last_laps_feed.append(f"{lap_no}\tTour invalide ({x_count}x)\t{player}")
            elif reason and reason.startswith("incidents:"):
                x_count = reason.split(":")[1]
                ui_bridge.log(f"Nouveau tour pour {player} : tour invalide ({x_count}x)")
                try:
                    lap_no = int(state_core.get("LapCompleted") or 0)
                except Exception:
                    lap_no = 0
                last_laps_feed.append(f"{lap_no}\tTour invalide ({x_count}x)\t{player}")
            else:
                ui_bridge.log(f"Nouveau tour pour {player} : tour invalide")
                try:
                    lap_no = int(state_core.get("LapCompleted") or 0)
                except Exception:
                    lap_no = 0
                last_laps_feed.append(f"{lap_no}\tTour invalide\t{player}")
            ui_bridge.update_last_laps(last_laps_feed)

        time.sleep(0.1)


#--------------------------------------------------------------------------------------------------------------#
# Gère l'absence de session : message d'attente, reset complet (validator, télémétrie, contexte, UI), shutdown iRSDK.#
#--------------------------------------------------------------------------------------------------------------#
def _handle_session_inactive(ir_client, ui_bridge, validator, session_manager, telemetry_reader):
    if session_manager.should_send_waiting_message():
        ui_bridge.log("En attente du démarrage d'une session…")
        ui_bridge.show_banner_message("waiting")
        session_manager.mark_waiting_message_sent()

        # Reset de l'état interne
        validator.reset()
        telemetry_reader.reset_throttling()
        ui_bridge.reset_coalescing()
        session_manager.reset_context()

        # Reset de l'affichage
        ui_bridge.update_ranking([])
        ui_bridge.update_context("---", "---")
        ui_bridge.update_session_time(None)
        ui_bridge.update_player_best("-:--.---")
        ui_bridge.update_debug({})

        # Shutdown iRSDK pour ne pas continuer à lire l'ancien contexte
        try:
            ir_client.ir.shutdown()
        except Exception:
            pass

    # Hors session : autoriser le changement de joueur
    ui_bridge.set_player_menu_state(True)


#--------------------------------------------------------------------------------------------------------------#
# Point d'entrée : initialise les composants/managers, câble l'UI et lance le thread worker.                   #
#--------------------------------------------------------------------------------------------------------------#
def main():
    # Composants de base
    ir_client = IRClient()
    validator = LapValidator()
    players = DataStore.load_players()

    # Managers
    session_manager = SessionManager(ir_client)
    telemetry_reader = TelemetryReader(ir_client)
    record_manager = RecordManager()

    # UI
    ui = TrackerUI(players, lambda p: None)

    # Pont UI (queue worker → UI)
    ui_event_queue = queue.Queue()
    ui_bridge = UIBridge(ui_event_queue)
    ui.bind_event_queue(ui_event_queue)

    # Flag debug partagé (protégé par un lock)
    runtime_flags = {"debug_enabled": ui.debug_visible.get()}
    flags_lock = threading.Lock()

    def on_debug_toggle(visible: bool):
        with flags_lock:
            runtime_flags["debug_enabled"] = bool(visible)

    ui.set_on_debug_toggle(on_debug_toggle)

    # Joueur sélectionné (état partagé thread-safe)
    selected_player = {"name": players[0] if players else "---"}
    sel_lock = threading.Lock()

    def on_player_change(p):
        with sel_lock:
            selected_player["name"] = p
        ui.add_log(f"Joueur sélectionné : {p}")

    ui.set_on_player_change(on_player_change)

    # Lancement du thread worker (daemon)
    t = threading.Thread(
        target=loop,
        args=(
            ir_client, ui_bridge, validator, session_manager, telemetry_reader,
            record_manager, selected_player, sel_lock, runtime_flags, flags_lock
        ),
        daemon=True
    )
    t.start()

    # Boucle Qt (thread principal)
    ui.mainloop()


if __name__ == "__main__":
    main()
