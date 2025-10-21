################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/telemetry_reader.py                                                                #
# Date de modification : 20.10.2025                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Lecture des variables iRSDK avec throttling automatique.                                       #
################################################################################################################

import time
from typing import Optional


#--------------------------------------------------------------------------------------------------------------#
# Gère la lecture des variables iRSDK avec throttling automatique selon le type de données.                    #
#--------------------------------------------------------------------------------------------------------------#
class TelemetryReader:
    """
    Responsabilités :
    - Lire les variables iRSDK via IRClient
    - Appliquer un throttling automatique selon le type de données
    - Fournir des méthodes spécialisées : read_core(), read_context(), read_debug()
    
    Intervalles de throttling :
    - Core (état tour, incidents) : 0.1s (10 Hz)
    - Context (track, car) : 2.0s
    - Debug (variables détaillées) : 0.3s
    """
    
    # Définition des variables par catégorie
    CORE_VARS = [
        "LapCompleted",
        "LapLastLapTime",
        "PlayerTrackSurface",
        "PlayerCarMyIncidentCount",
    ]
    
    CONTEXT_VARS = [
        "WeekendInfo",
        "DriverInfo",
        "PlayerCarIdx",
    ]
    
    DEBUG_VARS = [
        "SessionTime",
        "SessionNum",
        "SessionTimeRemain",
        "CarIdxLapCompleted",
        "CarIdxLastLapTime",
        "CarIdxLapDistPct",
        "CarIdxTrackSurface",
        "CarIdxOnPitRoad",
        "CarIdxPosition",
        "CarIdxSpeed",
        "CarIdxRPM",
    ]
    
    # Intervalles de throttling (secondes)
    CORE_INTERVAL = 0.1
    CONTEXT_INTERVAL = 2.0
    DEBUG_INTERVAL = 0.3
    
    def __init__(self, ir_client):
        self.ir_client = ir_client
        
        # Timestamps de dernière lecture
        self._last_core_read = 0.0
        self._last_context_read = 0.0
        self._last_debug_read = 0.0
    
    #--------------------------------------------------------------------------------------------------------------#
    # Lit les variables "core" nécessaires à la validation des tours (avec throttling 0.1s).                      #
    #--------------------------------------------------------------------------------------------------------------#
    def read_core(self, force: bool = False) -> Optional[dict]:
        """
        Lit les variables core (LapCompleted, incidents, etc.) avec throttling 0.1s.
        Si force=True, ignore le throttling.
        Retourne None si le throttling bloque la lecture.
        """
        now = time.time()
        if not force and (now - self._last_core_read) < self.CORE_INTERVAL:
            return None
        
        self._last_core_read = now
        return self.ir_client.freeze_and_read(self.CORE_VARS)
    
    #--------------------------------------------------------------------------------------------------------------#
    # Lit les variables "context" (track, car) avec throttling 2.0s.                                              #
    #--------------------------------------------------------------------------------------------------------------#
    def read_context(self, force: bool = False) -> Optional[dict]:
        """
        Lit les variables de contexte (WeekendInfo, DriverInfo) avec throttling 2.0s.
        Si force=True, ignore le throttling.
        Retourne None si le throttling bloque la lecture.
        """
        now = time.time()
        if not force and (now - self._last_context_read) < self.CONTEXT_INTERVAL:
            return None
        
        self._last_context_read = now
        return self.ir_client.freeze_and_read(self.CONTEXT_VARS)
    
    #--------------------------------------------------------------------------------------------------------------#
    # Lit les variables "debug" détaillées avec throttling 0.3s.                                                  #
    #--------------------------------------------------------------------------------------------------------------#
    def read_debug(self, force: bool = False) -> Optional[dict]:
        """
        Lit les variables debug (SessionTime, CarIdx...) avec throttling 0.3s.
        Si force=True, ignore le throttling.
        Retourne None si le throttling bloque la lecture.
        """
        now = time.time()
        if not force and (now - self._last_debug_read) < self.DEBUG_INTERVAL:
            return None
        
        self._last_debug_read = now
        return self.ir_client.freeze_and_read(self.DEBUG_VARS)
    
    #--------------------------------------------------------------------------------------------------------------#
    # Force la réinitialisation des timestamps (utile lors d'un changement de session).                           #
    #--------------------------------------------------------------------------------------------------------------#
    def reset_throttling(self):
        """Réinitialise tous les timestamps de throttling (force prochaine lecture)."""
        self._last_core_read = 0.0
        self._last_context_read = 0.0
        self._last_debug_read = 0.0