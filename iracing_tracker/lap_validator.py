# lap_validator.py

class LapValidator:
    def __init__(self):
        self.last_completed_lap = 0
        self._pending = False
        self._pending_info = {}

    def reset(self):
        """Reset au pit/garage ou nouvelle session."""
        self.last_completed_lap = 0
        self._pending = False
        self._pending_info = {}

    def update(self, state):
        """
        state doit contenir :
          - 'LapCompleted'            : int  (n° de tours complétés par ta voiture)
          - 'PlayerTrackSurface'      : int  (1=garage/stand,2=pit,3=track)
          - 'LapLastLapTime'          : float
          - 'PlayerCarMyIncidentCount': int  (ton nombre d’incidents)
        Retourne (valid: bool, lap_time: float).
        """

        comp      = state.get("LapCompleted", 0)
        surf      = state.get("PlayerTrackSurface", 0)
        lap_time  = state.get("LapLastLapTime", 0.0)
        inc_count = state.get("PlayerCarMyIncidentCount", 0)

        # Si on sort de piste (pit/garage), on reset tout  
        if surf != 3:
            self.reset()
            return False, 0.0

        # Phase 1 : nouveau tour complété ?  
        if comp > self.last_completed_lap and not self._pending:
            self._pending = True
            self._pending_info = {"comp": comp, "inc": inc_count}
            return False, 0.0

        # Phase 2 : state pending → on lit le vrai lap_time et on valide  
        if self._pending:
            info  = self._pending_info
            valid = (inc_count == info["inc"])
            self.last_completed_lap = info["comp"]
            self._pending = False
            self._pending_info = {}
            return valid, lap_time

        return False, 0.0
