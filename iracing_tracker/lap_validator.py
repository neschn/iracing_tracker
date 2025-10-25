################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/lap_validator.py                                                                   #
# Date de modification : 20.10.2025                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Détecte et valide les tours en suivant incidents et horodatages iRacing.                       #
################################################################################################################

import time
from typing import Optional


#--------------------------------------------------------------------------------------------------------------#
# Détecte quand un tour est terminé en surveillant LapCompleted et LapLastLapTime.                             #
#--------------------------------------------------------------------------------------------------------------#
class LapDetector:
    """
    Responsabilité : Détecter quand un tour est terminé.
    
    Complexité iRacing :
    - LapCompleted s'incrémente immédiatement
    - LapLastLapTime se met à jour avec un léger délai
    - On doit attendre cette MAJ pour avoir le temps correct
    """
    
    def __init__(self, pending_max_wait: float = 1.5):
        self.last_completed_lap = 0
        self.pending_max_wait = pending_max_wait
        
        # État d'un tour en attente de décision
        self._pending = False
        self._pending_info = {}
        self._pending_since = 0.0
        
        # Flag pour éviter reset prématuré au démarrage de session
        self.has_left_pits = False
    
    #--------------------------------------------------------------------------------------------------------------#
    # Réinitialise le détecteur (retour au garage après avoir été sur piste).                                     #
    #--------------------------------------------------------------------------------------------------------------#
    def reset(self):
        """Reset quand on retourne au garage après avoir été sur piste."""
        self.last_completed_lap = 0
        self._pending = False
        self._pending_info = {}
        self._pending_since = 0.0
        self.has_left_pits = False
    
    #--------------------------------------------------------------------------------------------------------------#
    # Détecte si un tour est terminé et retourne les infos si disponibles.                                        #
    #--------------------------------------------------------------------------------------------------------------#
    def detect(self, lap_completed: int, lap_time: float, surface: int) -> Optional[dict]:
        """
        Détecte si un tour est terminé.
        
        Retourne un dict si un tour est détecté :
        {
            "lap_number": int,
            "lap_time": float,
            "prev_lap_time": float,
            "timed_out": bool
        }
        
        Retourne None si aucun tour détecté ou en attente.
        """
        now = time.time()
        
        # Tracker si on a quitté les pits (pour éviter reset prématuré)
        if surface == 3:  # Sur la piste
            self.has_left_pits = True
        
        # Reset uniquement si on retourne au garage APRÈS avoir été sur piste
        if surface == 1 and self.has_left_pits:
            self.reset()
            return None
        
        # Session relancée (compteur recule)
        if lap_completed < self.last_completed_lap:
            self.reset()
            return None
        
        # 1) Détection d'un nouveau tour terminé
        if lap_completed > self.last_completed_lap and not self._pending:
            # Ignorer TOUT changement de LapCompleted avant d'avoir été sur la piste
            if not self.has_left_pits:
                self.last_completed_lap = lap_completed
                return None
            
            # Tous les autres changements : armer l'attente de la MAJ de LapLastLapTime
            self._pending = True
            self._pending_since = now
            self._pending_info = {
                "lap_number": lap_completed,
                "prev_lap_time": lap_time
            }
            
            # Préparer le tour suivant
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
# Orchestre la détection et validation des tours avec gestion des incidents.                                   #
#--------------------------------------------------------------------------------------------------------------#
class LapValidator:
    """
    Responsabilité : Orchestrer détection + validation des tours.
    
    Utilise :
    - LapDetector pour détecter quand un tour est terminé
    - Logique d'incidents pour valider si le tour est propre (0x)
    - Flag "was_in_pits_this_lap" pour détecter les out laps
    
    Retourne :
    - status : "valid" | "invalid" | "none"
    - lap_time : float
    - reason : None | "out_lap" | "incidents:N" | "flag_and_incidents:N"
    """
    
    def __init__(self):
        self.detector = LapDetector()
        
        # Calibration et suivi incidents
        self.initialized = False
        self.inc_at_lap_start = 0
        
        # Flag pour détecter les out laps (sortie des stands)
        self.was_in_pits_this_lap = False
    
    #--------------------------------------------------------------------------------------------------------------#
    # Réinitialise le validateur (retour au garage).                                                              #
    #--------------------------------------------------------------------------------------------------------------#
    def reset(self):
        """Reset au retour garage."""
        self.detector.reset()
        self.initialized = False
        self.inc_at_lap_start = 0
        self.was_in_pits_this_lap = False
    
    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour l'état et retourne (status, lap_time, reason) si un tour est détecté.                            #
    #--------------------------------------------------------------------------------------------------------------#
    def update(self, state: dict) -> tuple[str, float, Optional[str]]:
        """
        Analyse l'état télémétrique et détecte/valide les tours.
        
        state doit contenir :
          - LapCompleted (int)
          - PlayerTrackSurface (int)
          - LapLastLapTime (float)
          - PlayerCarMyIncidentCount (int)
        
        Retourne (status, lap_time, reason) :
          - status: "none" | "valid" | "invalid"
          - lap_time: temps du tour (0.0 si none)
          - reason: None | "out_lap" | "incidents:N" | "flag_and_incidents:N"
        """
        lap_completed = int(state.get("LapCompleted", 0) or 0)
        surface = int(state.get("PlayerTrackSurface", 0) or 0)
        lap_time = float(state.get("LapLastLapTime", 0.0) or 0.0)
        inc_count = int(state.get("PlayerCarMyIncidentCount", 0) or 0)
        
        # Tracker si on est dans les pits PENDANT le tour
        if surface in (1, 2):
            self.was_in_pits_this_lap = True
        elif surface == 3 and self.was_in_pits_this_lap:
            # On vient d'arriver sur la piste après avoir été dans les pits
            # Reset le flag pour le PROCHAIN tour (pas celui en cours)
            # SAUF si on n'a pas encore détecté le premier tour (changement 0→1 ignoré)
            if self.detector.last_completed_lap > 0:
                self.was_in_pits_this_lap = False
        
        # Reset si retour pit/garage (après avoir été sur piste)
        if surface == 1 and self.detector.has_left_pits:
            self.reset()
            return "none", 0.0, None
        
        # Session relancée (compteur recule)
        if lap_completed < self.detector.last_completed_lap:
            self.reset()
            return "none", 0.0, None
        
        # 1ère arrivée en piste : prendre la baseline d'incidents
        if not self.initialized:
            self.inc_at_lap_start = inc_count
            self.initialized = True
        
        # Détecter si un tour est terminé
        lap_info = self.detector.detect(lap_completed, lap_time, surface)
        
        if lap_info is None:
            return "none", 0.0, None
        
        # Tour détecté : récupérer les infos
        detected_lap_time = lap_info["lap_time"]
        timed_out = lap_info.get("timed_out", False)
        
        # Calculer les incidents pendant ce tour
        lap_inc_delta = inc_count - self.inc_at_lap_start
        
        # Sauvegarder le flag out lap AVANT de le reset
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