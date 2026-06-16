################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/lap_validator.py                                                                   #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Détecte et valide les tours en suivant les incidents et les horodatages iRacing.               #
################################################################################################################

import time
from typing import Optional


#--------------------------------------------------------------------------------------------------------------#
# Détecte la fin d'un tour via LapCompleted et LapLastLapTime (qui se met à jour avec un léger délai).         #
#--------------------------------------------------------------------------------------------------------------#
class LapDetector:

    #--------------------------------------------------------------------------------------------------------------#
    # Initialise le détecteur : aucun tour terminé, aucun tour en attente.                                         #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self, pending_max_wait: float = 1.5):
        self.last_completed_lap = 0
        self.pending_max_wait = pending_max_wait

        # État d'un tour en attente de la MAJ de LapLastLapTime
        self._pending = False
        self._pending_info = {}
        self._pending_since = 0.0

        # Évite un reset prématuré au démarrage de session (tant qu'on n'a pas roulé)
        self.has_left_pits = False

    #--------------------------------------------------------------------------------------------------------------#
    # Réinitialise le détecteur (retour au garage après avoir été sur piste).                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def reset(self):
        self.last_completed_lap = 0
        self._pending = False
        self._pending_info = {}
        self._pending_since = 0.0
        self.has_left_pits = False

    #--------------------------------------------------------------------------------------------------------------#
    # Détecte si un tour vient de se terminer ; retourne ses infos (dict) ou None si rien/en attente.              #
    #--------------------------------------------------------------------------------------------------------------#
    def detect(self, lap_completed: int, lap_time: float, surface: int) -> Optional[dict]:
        now = time.time()

        # Mémoriser qu'on a quitté les stands (pour éviter un reset prématuré)
        if surface == 3:  # Sur la piste
            self.has_left_pits = True

        # Reset uniquement si on retourne au garage APRÈS avoir été sur piste
        if surface == 1 and self.has_left_pits:
            self.reset()
            return None

        # Session relancée (le compteur recule)
        if lap_completed < self.last_completed_lap:
            self.reset()
            return None

        # 1) Détection d'un nouveau tour terminé
        if lap_completed > self.last_completed_lap and not self._pending:
            # Ignorer tout changement de LapCompleted avant d'avoir été sur la piste
            if not self.has_left_pits:
                self.last_completed_lap = lap_completed
                return None

            # Sinon : armer l'attente de la MAJ de LapLastLapTime
            self._pending = True
            self._pending_since = now
            self._pending_info = {
                "lap_number": lap_completed,
                "prev_lap_time": lap_time
            }

            self.last_completed_lap = lap_completed
            return None

        # 2) Tour en attente : guetter la MAJ de LapLastLapTime
        if self._pending:
            info = self._pending_info
            prev_lap_time = info.get("prev_lap_time", 0.0)

            # a) Pas encore de MAJ
            if lap_time == prev_lap_time:
                if (now - self._pending_since) >= self.pending_max_wait:
                    # Timeout : iRacing n'a pas posé de nouveau temps
                    self._pending = False
                    result = {
                        "lap_number": info["lap_number"],
                        "lap_time": lap_time,
                        "prev_lap_time": prev_lap_time,
                        "timed_out": True
                    }
                    self._pending_info = {}
                    self._pending_since = 0.0
                    return result
                return None

            # b) MAJ reçue : retourner les infos
            self._pending = False
            result = {
                "lap_number": info["lap_number"],
                "lap_time": lap_time,
                "prev_lap_time": prev_lap_time,
                "timed_out": False
            }
            self._pending_info = {}
            self._pending_since = 0.0
            return result

        # 3) Rien de nouveau
        return None


#--------------------------------------------------------------------------------------------------------------#
# Orchestre détection + validation : compare les incidents entre début et fin de tour.                         #
# Gère les out laps et le tour de lancement ; retourne (status, lap_time, reason).                             #
#--------------------------------------------------------------------------------------------------------------#
class LapValidator:

    #--------------------------------------------------------------------------------------------------------------#
    # Initialise le validateur : détecteur, baseline d'incidents et flag out lap.                                  #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self):
        self.detector = LapDetector()

        # Calibration et suivi des incidents
        self.initialized = False
        self.inc_at_lap_start = 0

        # Flag de détection des out laps (sortie des stands)
        self.was_in_pits_this_lap = False

    #--------------------------------------------------------------------------------------------------------------#
    # Réinitialise le validateur (retour au garage).                                                               #
    #--------------------------------------------------------------------------------------------------------------#
    def reset(self):
        self.detector.reset()
        self.initialized = False
        self.inc_at_lap_start = 0
        self.was_in_pits_this_lap = False

    #--------------------------------------------------------------------------------------------------------------#
    # Analyse l'état télémétrique, détecte/valide un tour et retourne (status, lap_time, reason).                  #
    #--------------------------------------------------------------------------------------------------------------#
    def update(self, state: dict) -> tuple[str, float, Optional[str]]:
        lap_completed = int(state.get("LapCompleted", 0) or 0)
        surface = int(state.get("PlayerTrackSurface", 0) or 0)
        lap_time = float(state.get("LapLastLapTime", 0.0) or 0.0)
        inc_count = int(state.get("PlayerCarMyIncidentCount", 0) or 0)

        # Mémoriser le passage par les stands PENDANT le tour
        if surface in (1, 2):
            self.was_in_pits_this_lap = True
        elif surface == 3 and self.was_in_pits_this_lap:
            # Arrivée sur la piste après les stands : reset du flag pour le PROCHAIN tour,
            # sauf si le premier tour n'a pas encore été détecté (changement 0→1 ignoré)
            if self.detector.last_completed_lap > 0:
                self.was_in_pits_this_lap = False

        # Reset si retour pit/garage (après avoir été sur piste)
        if surface == 1 and self.detector.has_left_pits:
            self.reset()
            return "none", 0.0, None

        # Session relancée (le compteur recule)
        if lap_completed < self.detector.last_completed_lap:
            self.reset()
            return "none", 0.0, None

        # Première arrivée en piste : prendre la baseline d'incidents
        if not self.initialized:
            self.inc_at_lap_start = inc_count
            self.initialized = True

        # Détecter si un tour est terminé
        lap_info = self.detector.detect(lap_completed, lap_time, surface)

        if lap_info is None:
            return "none", 0.0, None

        detected_lap_time = lap_info["lap_time"]
        timed_out = lap_info.get("timed_out", False)

        # Incidents survenus pendant ce tour
        lap_inc_delta = inc_count - self.inc_at_lap_start

        # Mémoriser le flag out lap avant de le réinitialiser
        was_out_lap = self.was_in_pits_this_lap

        # Préparer le tour suivant
        self.inc_at_lap_start = inc_count
        self.was_in_pits_this_lap = False

        # Déterminer status et reason
        if detected_lap_time <= 0 or timed_out:
            # Tour incomplet ou annulé
            if was_out_lap:
                return "invalid", detected_lap_time, "out_lap"
            elif lap_inc_delta > 0:
                return "invalid", detected_lap_time, f"flag_and_incidents:{lap_inc_delta}"
            else:
                return "invalid", detected_lap_time, None

        elif lap_inc_delta > 0:
            # Tour avec incidents
            return "invalid", detected_lap_time, f"incidents:{lap_inc_delta}"

        else:
            # Tour valide
            return "valid", detected_lap_time, None
