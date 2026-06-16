################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui_bridge.py                                                                       #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Pont thread-safe worker → UI : pousse des messages dans la queue, avec coalescing.             #
################################################################################################################

import queue
from typing import Optional


#--------------------------------------------------------------------------------------------------------------#
# Envoie les messages du worker vers l'UI via une queue, en évitant les updates redondants (coalescing).       #
#--------------------------------------------------------------------------------------------------------------#
class UIBridge:

    #--------------------------------------------------------------------------------------------------------------#
    # Mémorise la queue UI et initialise le cache de coalescing.                                                   #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self, ui_queue: queue.Queue):
        self.ui_queue = ui_queue

        # Dernières valeurs envoyées (pour éviter de renvoyer l'identique)
        self._last_context: Optional[tuple] = None
        self._last_player_best: Optional[str] = None
        self._last_player_menu_state: Optional[bool] = None
        self._last_session_time_sec: Optional[int] = None

    #--------------------------------------------------------------------------------------------------------------#
    # Envoie le contexte (circuit + voiture), seulement s'il diffère du dernier envoyé.                            #
    #--------------------------------------------------------------------------------------------------------------#
    def update_context(self, track: str, car: str, track_id: int | None = None, car_id: int | None = None):
        new_value = (track, car, track_id, car_id)
        if new_value != self._last_context:
            payload = {"track": track, "car": car}
            if track_id is not None:
                payload["track_id"] = track_id
            if car_id is not None:
                payload["car_id"] = car_id
            self.ui_queue.put(("context", payload))
            self._last_context = new_value

    #--------------------------------------------------------------------------------------------------------------#
    # Envoie le temps de session (coalescé à la seconde) ; un None force toujours un reset d'affichage.            #
    #--------------------------------------------------------------------------------------------------------------#
    def update_session_time(self, seconds: float | int | None):
        if seconds is None:
            self.ui_queue.put(("session_time", {"seconds": None}))
            self._last_session_time_sec = None
            return
        try:
            secs = max(0, int(float(seconds)))
        except Exception:
            secs = None
        if secs is None:
            # Valeur invalide -> reset
            self.ui_queue.put(("session_time", {"seconds": None}))
            self._last_session_time_sec = None
            return
        if secs == self._last_session_time_sec:
            return
        self.ui_queue.put(("session_time", {"seconds": secs}))
        self._last_session_time_sec = secs

    #--------------------------------------------------------------------------------------------------------------#
    # Envoie le record personnel du joueur sélectionné, seulement s'il a changé.                                   #
    #--------------------------------------------------------------------------------------------------------------#
    def update_player_best(self, best_time_text: str):
        if best_time_text != self._last_player_best:
            self.ui_queue.put(("player_best", {"text": best_time_text}))
            self._last_player_best = best_time_text

    #--------------------------------------------------------------------------------------------------------------#
    # Active/désactive le sélecteur de joueur (garage/piste), seulement si l'état change.                          #
    #--------------------------------------------------------------------------------------------------------------#
    def set_player_menu_state(self, enabled: bool):
        if enabled != self._last_player_menu_state:
            self.ui_queue.put(("player_menu_state", {"enabled": enabled}))
            self._last_player_menu_state = enabled

    #--------------------------------------------------------------------------------------------------------------#
    # Envoie un message de log (toujours, sans coalescing).                                                        #
    #--------------------------------------------------------------------------------------------------------------#
    def log(self, message: str):
        self.ui_queue.put(("log", {"message": message}))

    #--------------------------------------------------------------------------------------------------------------#
    # Envoie les données de debug (sans coalescing).                                                               #
    #--------------------------------------------------------------------------------------------------------------#
    def update_debug(self, debug_data: dict):
        self.ui_queue.put(("debug", debug_data))

    #--------------------------------------------------------------------------------------------------------------#
    # Réinitialise le cache de coalescing (force le prochain envoi ; utile au changement de session).              #
    #--------------------------------------------------------------------------------------------------------------#
    def reset_coalescing(self):
        self._last_context = None
        self._last_player_best = None
        self._last_player_menu_state = None
        self._last_session_time_sec = None

    #--------------------------------------------------------------------------------------------------------------#
    # Envoie le classement (top 3) à l'UI.                                                                         #
    #--------------------------------------------------------------------------------------------------------------#
    def update_ranking(self, ranking: list[dict]):
        self.ui_queue.put(("ranking", {"ranking": ranking}))

    #--------------------------------------------------------------------------------------------------------------#
    # Envoie la liste des derniers tours à afficher.                                                               #
    #--------------------------------------------------------------------------------------------------------------#
    def update_last_laps(self, entries):
        self.ui_queue.put(("last_laps", {"entries": entries}))

    #--------------------------------------------------------------------------------------------------------------#
    # Envoie un message à afficher dans la bannière (waiting / personal_record / absolute_record / clear).         #
    #--------------------------------------------------------------------------------------------------------------#
    def show_banner_message(self, message_type: str):
        self.ui_queue.put(("banner", {"type": message_type}))
