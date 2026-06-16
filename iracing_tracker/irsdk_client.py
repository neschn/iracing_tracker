################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/irsdk_client.py                                                                    #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Encapsule le client iRSDK et sécurise la lecture des données télémétriques.                    #
################################################################################################################

import irsdk


#--------------------------------------------------------------------------------------------------------------#
# Encapsule irsdk.IRSDK : démarrage paresseux et lecture sécurisée du buffer télémétrique.                     #
#--------------------------------------------------------------------------------------------------------------#
class IRClient:

    #--------------------------------------------------------------------------------------------------------------#
    # Initialise le client sans démarrer iRSDK (la connexion est tentée à la première lecture).                    #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self):
        self.ir = irsdk.IRSDK()

    #--------------------------------------------------------------------------------------------------------------#
    # Démarre iRSDK tant que le buffer n'est pas prêt, sans bloquer.                                               #
    #--------------------------------------------------------------------------------------------------------------#
    def _ensure_started(self):
        if not getattr(self.ir, "started", False):
            try:
                self.ir.startup()
            except Exception:
                pass

    #--------------------------------------------------------------------------------------------------------------#
    # Fige le buffer télémétrique et lit les variables demandées ; renvoie des None si iRSDK indisponible.         #
    #--------------------------------------------------------------------------------------------------------------#
    def freeze_and_read(self, variables: list) -> dict:
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

    #--------------------------------------------------------------------------------------------------------------#
    # Indique si une session iRacing est active (SessionUniqueID non nul).                                         #
    #--------------------------------------------------------------------------------------------------------------#
    def is_session_active(self) -> bool:
        if not getattr(self.ir, "is_connected", False):
            return False
        data = self.freeze_and_read(["SessionUniqueID"])
        return bool(data.get("SessionUniqueID"))
