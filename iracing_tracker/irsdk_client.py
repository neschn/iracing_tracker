import irsdk

class IRClient:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        # on **n**e fait **pas** startup ici, ou alors en boucle :
        # while not self.ir.started:
        #     time.sleep(0.5)
        #     self.ir.startup()

    def _ensure_started(self):
        """Relance self.ir.startup() tant que le buffer n'est pas prêt."""
        if not getattr(self.ir, "started", False):
            try:
                self.ir.startup()
            except Exception:
                pass

    def freeze_and_read(self, variables: list) -> dict:
        """
        Fige le buffer télémétrique et renvoie un dict {var: valeur} ou None si indisponible.
        """
        # 0) Assure-toi que le SDK est bien démarré (relance startup() si nécessaire)
        self._ensure_started()

        # 1) Si pas encore initialisé ou si la session est terminée,
        #    renvoie None pour toutes les variables
        if not getattr(self.ir, "is_initialized", False) or not getattr(self.ir, "is_connected", False):
            return {v: None for v in variables}

        # 2) Essaie de figer le buffer
        try:
            self.ir.freeze_var_buffer_latest()
        except AttributeError:
            # buffer pas prêt : on relance startup et retente une fois
            self._ensure_started()
            try:
                self.ir.freeze_var_buffer_latest()
            except Exception:
                return {v: None for v in variables}

        # 3) Lecture des variables demandées
        data = {}
        for v in variables:
            try:
                data[v] = self.ir[v]
            except Exception:
                data[v] = None
        return data


    def is_session_active(self) -> bool:
        # La connexion SDK elle-même indique si la session tourne
        if not getattr(self.ir, "is_connected", False):
            return False
        # Optionnel : vérifier aussi l’ID pour plus de sécurité
        data = self.freeze_and_read(["SessionUniqueID"])
        return bool(data.get("SessionUniqueID"))

