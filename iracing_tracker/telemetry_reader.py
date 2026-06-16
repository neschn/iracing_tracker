################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/telemetry_reader.py                                                                #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Lecture des variables iRSDK par catégorie, avec throttling automatique.                        #
################################################################################################################

import time
from typing import Optional


#--------------------------------------------------------------------------------------------------------------#
# Lit les variables iRSDK par catégorie (core / context / debug) avec un throttling propre à chacune.          #
#--------------------------------------------------------------------------------------------------------------#
class TelemetryReader:

    # Variables iRSDK regroupées par catégorie
    CORE_VARS = ["LapCompleted","LapLastLapTime","PlayerTrackSurface","PlayerCarMyIncidentCount","SessionTime",]

    CONTEXT_VARS = [
        "WeekendInfo",
        "DriverInfo",
        "PlayerCarIdx",
    ]

    DEBUG_VARS = [
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

    #--------------------------------------------------------------------------------------------------------------#
    # Mémorise le client iRSDK et initialise les horodatages de throttling.                                        #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self, ir_client):
        self.ir_client = ir_client

        # Horodatage de la dernière lecture de chaque catégorie
        self._last_core_read = 0.0
        self._last_context_read = 0.0
        self._last_debug_read = 0.0

    #--------------------------------------------------------------------------------------------------------------#
    # Lit les variables "core" (état tour, incidents) à 10 Hz ; None si la lecture est throttlée.                  #
    #--------------------------------------------------------------------------------------------------------------#
    def read_core(self, force: bool = False) -> Optional[dict]:
        now = time.time()
        if not force and (now - self._last_core_read) < self.CORE_INTERVAL:
            return None

        self._last_core_read = now
        return self.ir_client.freeze_and_read(self.CORE_VARS)

    #--------------------------------------------------------------------------------------------------------------#
    # Lit le contexte (circuit, voiture) toutes les 2 s ; None si la lecture est throttlée.                        #
    #--------------------------------------------------------------------------------------------------------------#
    def read_context(self, force: bool = False) -> Optional[dict]:
        now = time.time()
        if not force and (now - self._last_context_read) < self.CONTEXT_INTERVAL:
            return None

        self._last_context_read = now
        return self.ir_client.freeze_and_read(self.CONTEXT_VARS)

    #--------------------------------------------------------------------------------------------------------------#
    # Lit les variables debug détaillées (~3 Hz) ; None si la lecture est throttlée.                               #
    #--------------------------------------------------------------------------------------------------------------#
    def read_debug(self, force: bool = False) -> Optional[dict]:
        now = time.time()
        if not force and (now - self._last_debug_read) < self.DEBUG_INTERVAL:
            return None

        self._last_debug_read = now
        return self.ir_client.freeze_and_read(self.DEBUG_VARS)

    #--------------------------------------------------------------------------------------------------------------#
    # Réinitialise les horodatages pour forcer la prochaine lecture (changement de session).                       #
    #--------------------------------------------------------------------------------------------------------------#
    def reset_throttling(self):
        self._last_core_read = 0.0
        self._last_context_read = 0.0
        self._last_debug_read = 0.0
