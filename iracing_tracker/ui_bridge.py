################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui_bridge.py                                                                       #
# Date de modification : 20.10.2025                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Gère la communication avec l'UI via queue, avec coalescing automatique.                        #
################################################################################################################

import queue
from typing import Optional


#--------------------------------------------------------------------------------------------------------------#
# Pont entre la boucle télémétrie et l'UI, avec coalescing pour éviter les updates inutiles.                   #
#--------------------------------------------------------------------------------------------------------------#
class UIBridge:
    """
    Responsabilités :
    - Envoyer des messages à la queue UI
    - Coalescing automatique (évite d'envoyer la même valeur 2 fois)
    - Méthodes pratiques pour chaque type de message
    
    Types de messages UI gérés :
    - context : mise à jour circuit/voiture
    - player_best : record personnel du joueur
    - player_menu_state : activer/désactiver le sélecteur de joueur
    - log : message de log
    - debug : données de debug
    """
    
    def __init__(self, ui_queue: queue.Queue):
        self.ui_queue = ui_queue
        
        # Cache pour coalescing (évite d'envoyer la même valeur)
        self._last_context: Optional[tuple] = None
        self._last_player_best: Optional[str] = None
        self._last_player_menu_state: Optional[bool] = None
        self._last_session_time_sec: Optional[int] = None
    
    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le contexte (circuit + voiture) dans l'UI, avec coalescing.                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def update_context(self, track: str, car: str, track_id: int | None = None, car_id: int | None = None):
        """
        Envoie le contexte (circuit, voiture) à l'UI.
        Coalescing : n'envoie que si différent de la dernière valeur.
        """
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
    # Met à jour le temps de session affiché (coalescé à la seconde).                                             #
    #--------------------------------------------------------------------------------------------------------------#
    def update_session_time(self, seconds: float | int | None):
        """Envoie le temps de session (en secondes), coalescé à l'entier.
        S'il est None, on force toujours un envoi (reset d'affichage).
        """
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
    # Met à jour le record personnel du joueur sélectionné, avec coalescing.                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def update_player_best(self, best_time_text: str):
        """
        Envoie le meilleur temps du joueur sélectionné à l'UI.
        Coalescing : n'envoie que si différent de la dernière valeur.
        """
        if best_time_text != self._last_player_best:
            self.ui_queue.put(("player_best", {"text": best_time_text}))
            self._last_player_best = best_time_text
    
    #--------------------------------------------------------------------------------------------------------------#
    # Active/désactive le sélecteur de joueur selon la position (garage/piste).                                   #
    #--------------------------------------------------------------------------------------------------------------#
    def set_player_menu_state(self, enabled: bool):
        """
        Active/désactive le menu de sélection des joueurs.
        Coalescing : n'envoie que si l'état change.
        """
        if enabled != self._last_player_menu_state:
            self.ui_queue.put(("player_menu_state", {"enabled": enabled}))
            self._last_player_menu_state = enabled
    
    #--------------------------------------------------------------------------------------------------------------#
    # Envoie un message de log (toujours envoyé, pas de coalescing).                                              #
    #--------------------------------------------------------------------------------------------------------------#
    def log(self, message: str):
        """Envoie un message de log à l'UI (pas de coalescing)."""
        self.ui_queue.put(("log", {"message": message}))
    
    #--------------------------------------------------------------------------------------------------------------#
    # Envoie les données de debug à l'UI (pas de coalescing, si zone visible).                                    #
    #--------------------------------------------------------------------------------------------------------------#
    def update_debug(self, debug_data: dict):
        """Envoie les données de debug à l'UI (pas de coalescing)."""
        self.ui_queue.put(("debug", debug_data))
    
    #--------------------------------------------------------------------------------------------------------------#
    # Réinitialise le cache de coalescing (utile lors d'un changement de session).                                #
    #--------------------------------------------------------------------------------------------------------------#
    def reset_coalescing(self):
        """Réinitialise le cache de coalescing (force prochaine mise à jour)."""
        self._last_context = None
        self._last_player_best = None
        self._last_player_menu_state = None
        self._last_session_time_sec = None
    
    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le classement (top 3) affiché dans l'UI.                                                         #
    #--------------------------------------------------------------------------------------------------------------#
    def update_ranking(self, ranking: list[dict]):
        """
        Envoie le classement à l'UI.
        Format attendu : [{"player": "Nico", "time": 65.123}, ...]
        """
        self.ui_queue.put(("ranking", {"ranking": ranking}))

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour la liste des derniers tours (texte ou couples (time, player)).                                   #
    #--------------------------------------------------------------------------------------------------------------#
    def update_last_laps(self, entries):
        """Envoie la liste des derniers tours à afficher (ordre: plus récent en haut)."""
        self.ui_queue.put(("last_laps", {"entries": entries}))
    
    #--------------------------------------------------------------------------------------------------------------#
    # Envoie un message à afficher dans la bannière.                                                              #
    #--------------------------------------------------------------------------------------------------------------#
    def show_banner_message(self, message_type: str):
        """
        Affiche un message dans la bannière.
        message_type: "waiting" | "personal_record" | "absolute_record" | "clear"
        """
        self.ui_queue.put(("banner", {"type": message_type}))
