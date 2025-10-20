################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/lap_validator.py                                                                   #
# Date de modification : 20.10.2025                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Valide les tours en suivant incidents et horodatages iRacing.                                  #
################################################################################################################

import time

class LapValidator:
    def __init__(self):
        self.last_completed_lap = 0

        # suivi d'un tour en attente de décision
        self._pending = False
        self._pending_info = {}
        self._pending_since = 0.0
        self.PENDING_MAX_WAIT = 1.5  # s pour attendre la MAJ de LapLastLapTime

        # calibration au 1er passage “en piste”
        self.initialized = False
        self.inc_at_lap_start = 0

    def reset(self):
        """Reset au pit/garage ou nouvelle session."""
        self.last_completed_lap = 0
        self._pending = False
        self._pending_info = {}
        self._pending_since = 0.0
        self.initialized = False
        self.inc_at_lap_start = 0

    def update(self, state):
        """
        state:
          - LapCompleted (int)
          - PlayerTrackSurface (int) 1=garage/pitstall, 2=pit lane, 3=piste
          - LapLastLapTime (float)    temps du tour terminé (<=0 si non comptable)
          - PlayerCarMyIncidentCount (int)
        Retourne (status: "none"|"valid"|"invalid", lap_time: float)
        """
        now       = time.time()
        comp      = int(state.get("LapCompleted", 0) or 0)
        surf      = int(state.get("PlayerTrackSurface", 0) or 0)
        lap_time  = float(state.get("LapLastLapTime", 0.0) or 0.0)
        inc_count = int(state.get("PlayerCarMyIncidentCount", 0) or 0)

        # session relancée (compteur recule) ou retour au box -> reset
        if comp < self.last_completed_lap:
            self.reset()
            return "none", 0.0
        if surf == 1:  # pit box/garage
            self.reset()
            return "none", 0.0

        # 1ère arrivée en piste: on prend la baseline
        if not self.initialized:
            self.last_completed_lap = comp
            self.inc_at_lap_start   = inc_count
            self.initialized        = True
            return "none", 0.0

        # 1) détection d'un tour terminé
        if comp > self.last_completed_lap and not self._pending:
            lap_inc_diff   = inc_count - self.inc_at_lap_start
            expected_valid = (lap_inc_diff == 0)

            # on “arme” l'attente de la MAJ de LapLastLapTime
            self._pending = True
            self._pending_since = now
            self._pending_info = {
                "prev_last_time": lap_time,   # valeur avant MAJ par iRacing
                "expected_valid": expected_valid
            }

            # préparation du tour suivant
            self.last_completed_lap = comp
            self.inc_at_lap_start   = inc_count
            return "none", 0.0

        # 2) un tour est en attente: on guette la MAJ de LapLastLapTime
        if self._pending:
            info = self._pending_info
            prev_last_time  = info.get("prev_last_time", 0.0)
            expected_valid  = info.get("expected_valid", False)

            # a) pas encore de MAJ
            if lap_time == prev_last_time:
                if (now - self._pending_since) >= self.PENDING_MAX_WAIT:
                    # iRacing n’a pas posé de nouveau temps -> invalide
                    self._pending = False
                    self._pending_info = {}
                    self._pending_since = 0.0
                    return "invalid", lap_time
                return "none", 0.0

            # b) MAJ reçue: décision
            self._pending = False
            self._pending_info = {}
            self._pending_since = 0.0

            # valide si: pas d'incidents ET temps strictement positif
            is_valid = expected_valid and (lap_time > 0.0)
            return ("valid" if is_valid else "invalid"), lap_time

        # 3) rien de nouveau
        return "none", 0.0
