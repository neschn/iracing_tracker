################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/session_manager.py                                                                 #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Gère l'état de la session iRacing (détection des changements, contexte circuit/voiture).       #
################################################################################################################

import time
from typing import Optional
from iracing_tracker.ui.constants import SESSION_INACTIVE_GRACE_SECONDS


#--------------------------------------------------------------------------------------------------------------#
# Encapsule le contexte d'une session iRacing : circuit et voiture.                                            #
#--------------------------------------------------------------------------------------------------------------#
class SessionContext:

    #--------------------------------------------------------------------------------------------------------------#
    # Initialise un contexte vide (circuit et voiture non définis).                                                #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self):
        self.track_id: Optional[int] = None
        self.track_name: str = "---"
        self.car_id: Optional[int] = None
        self.car_name: str = "---"
        self.is_ready: bool = False

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le contexte et retourne True si l'une de ses valeurs a changé.                                    #
    #--------------------------------------------------------------------------------------------------------------#
    def update(self, track_id: Optional[int], track_name: str, car_id: Optional[int], car_name: str):
        changed = (
            self.track_id != track_id or
            self.track_name != track_name or
            self.car_id != car_id or
            self.car_name != car_name
        )

        self.track_id = track_id
        self.track_name = track_name
        self.car_id = car_id
        self.car_name = car_name
        self.is_ready = (track_id is not None) and (car_id is not None)

        return changed

    #--------------------------------------------------------------------------------------------------------------#
    # Retourne la clé unique du combo « track_id|car_id », ou None si le contexte est incomplet.                   #
    #--------------------------------------------------------------------------------------------------------------#
    def get_key(self) -> Optional[str]:
        if not self.is_ready:
            return None
        return f"{self.track_id}|{self.car_id}"


#--------------------------------------------------------------------------------------------------------------#
# Gère l'état de la session iRacing : détection active/inactive, changements de contexte, flags de messages.   #
#--------------------------------------------------------------------------------------------------------------#
class SessionManager:

    #--------------------------------------------------------------------------------------------------------------#
    # Initialise le manager avec le client iRSDK, un contexte vide et les flags de messages.                       #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self, ir_client):
        self.ir_client = ir_client
        self.context = SessionContext()

        # Flags pour éviter de répéter les messages de log (attente / démarrage)
        self.is_waiting_session_msg_sent = False
        self.session_start_msg_sent = False
        # Dernier instant où la session a été vue active (pour l'anti-rebond)
        self._last_active_ts: Optional[float] = None

    #--------------------------------------------------------------------------------------------------------------#
    # Indique si une session est active, avec une grâce anti-rebond pour absorber les micro-coupures.              #
    #--------------------------------------------------------------------------------------------------------------#
    def is_active(self) -> bool:
        active_now = self.ir_client.is_session_active()
        now = time.time()

        if active_now:
            self._last_active_ts = now
            return True

        # Jamais vue active : on prend l'état tel quel
        if self._last_active_ts is None:
            return False

        # Anti-rebond : rester actif tant que la grâce n'est pas écoulée
        if (now - self._last_active_ts) < float(SESSION_INACTIVE_GRACE_SECONDS):
            return True
        return False

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le contexte depuis les données iRSDK (WeekendInfo, DriverInfo) ; retourne True si changement.     #
    #--------------------------------------------------------------------------------------------------------------#
    def update_context(self, context_data: dict) -> bool:
        weekend = context_data.get("WeekendInfo") or {}
        track_id = weekend.get("TrackID")
        base_track_name = weekend.get("TrackDisplayName", "---")
        track_cfg = (weekend.get("TrackConfigName") or "").strip()
        track_name = f"{base_track_name} ({track_cfg})" if track_cfg else base_track_name

        drivers = context_data.get("DriverInfo", {}).get("Drivers", [])
        idx = int(context_data.get("PlayerCarIdx") or 0)
        if 0 <= idx < len(drivers):
            car_info = drivers[idx]
            car_id = car_info.get("CarID")
            car_name = car_info.get("CarScreenName", "---")
        else:
            car_id, car_name = None, "---"

        changed = self.context.update(track_id, track_name, car_id, car_name)
        return changed

    #--------------------------------------------------------------------------------------------------------------#
    # Réinitialise les flags de messages (à l'inactivation de la session).                                         #
    #--------------------------------------------------------------------------------------------------------------#
    def reset_message_flags(self):
        self.is_waiting_session_msg_sent = False
        self.session_start_msg_sent = False

    #--------------------------------------------------------------------------------------------------------------#
    # Marque le message « en attente de session » comme envoyé.                                                    #
    #--------------------------------------------------------------------------------------------------------------#
    def mark_waiting_message_sent(self):
        self.is_waiting_session_msg_sent = True
        self.session_start_msg_sent = False

    #--------------------------------------------------------------------------------------------------------------#
    # Marque le message « session démarrée » comme envoyé.                                                         #
    #--------------------------------------------------------------------------------------------------------------#
    def mark_session_started_message_sent(self):
        self.session_start_msg_sent = True

    #--------------------------------------------------------------------------------------------------------------#
    # Indique s'il faut envoyer le message « en attente de session ».                                              #
    #--------------------------------------------------------------------------------------------------------------#
    def should_send_waiting_message(self) -> bool:
        return not self.is_waiting_session_msg_sent

    #--------------------------------------------------------------------------------------------------------------#
    # Indique s'il faut envoyer le message « session démarrée » (contexte prêt et pas déjà envoyé).                #
    #--------------------------------------------------------------------------------------------------------------#
    def should_send_session_started_message(self) -> bool:
        return self.context.is_ready and not self.session_start_msg_sent

    #--------------------------------------------------------------------------------------------------------------#
    # Réinitialise complètement le contexte (à l'inactivation de la session).                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def reset_context(self):
        self.context = SessionContext()
        # Oublier l'état d'activité précédent
        self._last_active_ts = None
