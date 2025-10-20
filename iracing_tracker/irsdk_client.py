################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/irsdk_client.py                                                                    #
# Date de modification : 20.10.2025                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Encapsule le client iRSDK et sécurise la lecture des données télémétriques.                    #
################################################################################################################

import irsdk

class IRClient:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        # Pas de startup() bloquant ici.

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
        self._ensure_started()

        if not getattr(self.ir, "is_initialized", False) or not getattr(self.ir, "is_connected", False):
            return {v: None for v in variables}

        try:
            self.ir.freeze_var_buffer_latest()
        except AttributeError:
            self._ensure_started()
            try:
                self.ir.freeze_var_buffer_latest()
            except Exception:
                return {v: None for v in variables}

        data = {}
        for v in variables:
            try:
                data[v] = self.ir[v]
            except Exception:
                data[v] = None
        return data

    def is_session_active(self) -> bool:
        if not getattr(self.ir, "is_connected", False):
            return False
        data = self.freeze_and_read(["SessionUniqueID"])
        return bool(data.get("SessionUniqueID"))
