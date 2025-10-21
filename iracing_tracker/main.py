################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/main.py                                                                            #
# Date de modification : 20.10.2025                                                                            #
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
# Boucle principale de collecte télémétrie et validation des tours.                                            #
#--------------------------------------------------------------------------------------------------------------#
def loop(ir_client, ui_bridge, validator, session_manager, telemetry_reader, 
         record_manager, selected_player_ref, sel_lock, runtime_flags, flags_lock):
    """
    Boucle principale refactorisée avec managers.
    Orchestration légère : lecture -> validation -> mise à jour UI.
    """
    
    while True:
        # ---- 1) LECTURE CORE EN PREMIER (nécessaire pour connexion iRSDK) ----
        # CRITIQUE : Cette lecture DOIT être faite avant is_session_active()
        # car c'est elle qui initialise la connexion iRSDK !
        try:
            state_core = telemetry_reader.read_core(force=True) or {}
        except Exception:
            state_core = {}
        
        # ---- 2) Vérifier si session active (APRÈS la lecture) ----
        if not session_manager.is_active():
            _handle_session_inactive(ir_client, ui_bridge, validator, session_manager, telemetry_reader)
            time.sleep(0.1)
            continue
        
        # ---- 3) Session active : reset flag d'attente ----
        if session_manager.is_waiting_session_msg_sent:
            session_manager.is_waiting_session_msg_sent = False
        
        # ---- 4) Lecture et mise à jour du contexte ----
        # Forcer la lecture tant qu'on n'a pas de contexte valide
        try:
            force_context_read = not session_manager.context.is_ready
            context_data = telemetry_reader.read_context(force=force_context_read)
            
            if context_data:
                context_changed = session_manager.update_context(context_data)
                
                # Envoyer à l'UI si changement
                if context_changed:
                    ui_bridge.update_context(
                        session_manager.context.track_name,
                        session_manager.context.car_name
                    )
                    # Force mise à jour du best label après changement de contexte
                    ui_bridge.reset_coalescing()
                
                # Message "session démarrée" (une seule fois)
                if session_manager.should_send_session_started_message():
                    track = session_manager.context.track_name
                    car = session_manager.context.car_name
                    ui_bridge.log(f"Nouvelle session démarrée : {track} - {car}")
                    session_manager.mark_session_started_message_sent()
                
        except Exception as e:
            ui_bridge.log(f"Erreur lecture contexte : {e}")
        
        # ---- 5) Lecture debug (si activé) ----
        with flags_lock:
            debug_enabled = bool(runtime_flags.get("debug_enabled", False))
        
        if debug_enabled:
            debug_data = telemetry_reader.read_debug()
            if debug_data:
                # Fusionner avec les données core
                merged_debug = {**state_core, **debug_data}
                # Ajouter les flags de session
                merged_debug["is_waiting_session_msg_sent"] = session_manager.is_waiting_session_msg_sent
                merged_debug["session_start_msg_sent"] = session_manager.session_start_msg_sent
                ui_bridge.update_debug(merged_debug)
        
        # ---- 6) Gestion pit/garage : activer/désactiver menu joueur ----
        surface = int(state_core.get("PlayerTrackSurface") or 0)
        ui_bridge.set_player_menu_state(surface in (1, -1))
        
        # ---- 7) Mise à jour du record personnel du joueur sélectionné ----
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
        
        # ---- 8) Validation des tours ----
        if not player or player == "---":
            time.sleep(0.1)
            continue
        
        lap_state = {
            "LapCompleted": state_core.get("LapCompleted"),
            "PlayerTrackSurface": state_core.get("PlayerTrackSurface"),
            "LapLastLapTime": state_core.get("LapLastLapTime"),
            "PlayerCarMyIncidentCount": state_core.get("PlayerCarMyIncidentCount"),
        }
        
        status, lap_time = validator.update(lap_state)
        
        # ---- 9) Sauvegarde si tour valide ----
        if status == "valid" and session_manager.context.is_ready:
            is_record = record_manager.save_lap(
                player,
                session_manager.context.track_id,
                session_manager.context.car_id,
                lap_time
            )
            suffix = " (record personnel battu)" if is_record else ""
            ui_bridge.log(f"Nouveau tour pour {player} : {format_lap_time(lap_time)}{suffix}")
        
        elif status == "invalid":
            ui_bridge.log(f"Nouveau tour pour {player} : Temps invalide")
        
        time.sleep(0.1)


#--------------------------------------------------------------------------------------------------------------#
# Gère le cas où la session iRacing est inactive (attente, reset).                                             #
#--------------------------------------------------------------------------------------------------------------#
def _handle_session_inactive(ir_client, ui_bridge, validator, session_manager, telemetry_reader):
    """
    Appelé quand aucune session iRacing n'est active.
    - Envoie message "attente session" (une seule fois)
    - Reset validator et télémétrie
    - Reset contexte session ET UI
    - Shutdown ir_client
    - Active menu joueur
    """
    if session_manager.should_send_waiting_message():
        ui_bridge.log("En attente du démarrage d'une session…")
        session_manager.mark_waiting_message_sent()
        
        # Reset état
        validator.reset()
        telemetry_reader.reset_throttling()
        ui_bridge.reset_coalescing()
        session_manager.reset_context()  # ← AJOUT : Reset le contexte interne
        
        # Reset contexte UI
        ui_bridge.update_context("---", "---")
        ui_bridge.update_player_best("-:--.---")
        ui_bridge.update_debug({})
        
        # Shutdown iRSDK
        try:
            ir_client.ir.shutdown()
        except Exception:
            pass
    
    # Hors session : autoriser le changement de joueur
    ui_bridge.set_player_menu_state(True)


#--------------------------------------------------------------------------------------------------------------#
# Point d'entrée principal : initialise les managers et lance la boucle.                                       #
#--------------------------------------------------------------------------------------------------------------#
def main():
    # ---- Initialisation des composants ----
    ir_client = IRClient()
    validator = LapValidator()
    players = DataStore.load_players()
    
    # ---- Initialisation des managers ----
    session_manager = SessionManager(ir_client)
    telemetry_reader = TelemetryReader(ir_client)
    record_manager = RecordManager()
    
    # ---- Création de l'UI ----
    ui = TrackerUI(players, lambda p: None)
    
    # ---- Bridge UI ----
    ui_event_queue = queue.Queue()
    ui_bridge = UIBridge(ui_event_queue)
    ui.bind_event_queue(ui_event_queue)
    
    # ---- Configuration debug ----
    runtime_flags = {"debug_enabled": ui.debug_visible.get()}
    flags_lock = threading.Lock()
    
    def on_debug_toggle(visible: bool):
        with flags_lock:
            runtime_flags["debug_enabled"] = bool(visible)
    
    ui.set_on_debug_toggle(on_debug_toggle)
    
    # ---- État joueur sélectionné (thread-safe) ----
    selected_player = {"name": players[0] if players else "---"}
    sel_lock = threading.Lock()
    
    def on_player_change(p):
        with sel_lock:
            selected_player["name"] = p
        ui.add_log(f"Joueur sélectionné : {p}")
    
    ui.set_on_player_change(on_player_change)
    
    # ---- Lancement du worker ----
    t = threading.Thread(
        target=loop,
        args=(
            ir_client, ui_bridge, validator, session_manager, telemetry_reader,
            record_manager, selected_player, sel_lock, runtime_flags, flags_lock
        ),
        daemon=True
    )
    t.start()
    
    # ---- Boucle Tk ----
    ui.mainloop()


if __name__ == "__main__":
    main()