# lap_validator.py
import time

class LapValidator:
    def __init__(self):
        # Compteur du dernier tour complété
        self.last_completed_lap = 0

        # Gestion du suivi du tour en attente de validation
        self._pending = False
        self._pending_info = {}
        self._pending_since = 0.0
        self.PENDING_MAX_WAIT = 1.5  # secondes max pour attendre la MAJ de LapLastLapTime

        # Gestion de l’état de calibration (arrivée en piste)
        self.initialized = False           # calibrage fait au premier passage "en piste"
        self.inc_at_lap_start = 0          # incidents au début du tour courant

    def reset(self):
        """Reset au pit/garage ou nouvelle session."""
        self.last_completed_lap = 0
        self._pending = False
        self._pending_info = {}
        self._pending_since = 0.0
        self.initialized = False  

    def update(self, state):
        """
        state doit contenir :
        - 'LapCompleted'            : int
        - 'PlayerTrackSurface'      : int (1=garage/pitbox, 2=pit lane, 3=piste)
        - 'LapLastLapTime'          : float
        - 'PlayerCarMyIncidentCount': int
        Retourne (status: "none" | "valid" | "invalid", lap_time: float).
        """
        now       = time.time()
        comp      = state.get("LapCompleted", 0)
        surf      = state.get("PlayerTrackSurface", 0)
        lap_time  = state.get("LapLastLapTime", 0.0)
        inc_count = state.get("PlayerCarMyIncidentCount", 0)

        # Si on n'est pas en piste -> on se met en attente et on ne décide rien
        if surf != 3:
            self.reset()
            return "none", 0.0

        # Première arrivée en piste : on se calibre pour ne PAS valider un tour fantôme
        if not self.initialized:
            self.last_completed_lap = comp
            self.inc_at_lap_start   = inc_count
            self.initialized        = True
            # pas d'évènement au tick d'init
            return "none", 0.0

        # 1) Détection du passage de ligne : un tour vient d’être terminé
        if comp > self.last_completed_lap and not self._pending:
            # On évalue si le tour terminé est 0x en comparant incidents du tour
            lap_inc_diff = inc_count - self.inc_at_lap_start
            expected_valid = (lap_inc_diff == 0)

            # On "arme" l'attente de la mise à jour de LapLastLapTime
            self._pending = True
            self._pending_since = now
            self._pending_info = {
                "prev_last_time": lap_time,   # valeur avant que iRacing pose la nouvelle
                "expected_valid": expected_valid
            }

            # Préparer le tour suivant (nouveau départ de tour)
            self.last_completed_lap = comp
            self.inc_at_lap_start   = inc_count

            # On attend la MAJ du temps : pour l’instant, rien à logguer
            return "none", 0.0

        # 2) Un tour attend d'être résolu : on guette la MAJ de LapLastLapTime
        if self._pending:
            info = self._pending_info
            prev_last_time  = info.get("prev_last_time", 0.0)
            expected_valid  = info.get("expected_valid", False)

            # a) Pas encore de MAJ -> on attend, sauf si délai dépassé (tour invalide)
            if lap_time == prev_last_time:
                if (now - self._pending_since) >= self.PENDING_MAX_WAIT:
                    # délai dépassé : iRacing n'a pas posé de nouveau temps -> on conclut invalide
                    self._pending = False
                    self._pending_info = {}
                    self._pending_since = 0.0
                    return "invalid", lap_time
                return "none", 0.0

            # b) LapLastLapTime a été mis à jour -> on peut décider
            self._pending = False
            self._pending_info = {}
            self._pending_since = 0.0

            is_valid = expected_valid and (lap_time is not None) and (lap_time > 0.0)
            return ("valid" if is_valid else "invalid"), lap_time

        # 3) Pas de nouvel évènement (on est en cours de tour)
        return "none", 0.0
