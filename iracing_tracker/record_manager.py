################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/record_manager.py                                                                  #
# Date de modification : 20.10.2025                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Gère les meilleurs tours (lecture, sauvegarde, comparaison).                                   #
################################################################################################################

from datetime import datetime
from typing import Optional

from iracing_tracker.data_store import DataStore


#--------------------------------------------------------------------------------------------------------------#
# Formate un temps de tour au format M:SS.mmm, ou '---' si invalide.                                           #
#--------------------------------------------------------------------------------------------------------------#
def format_lap_time(lap_time: float) -> str:
    """Formate un temps en M:SS.mmm. Retourne '---' si temps invalide."""
    if not lap_time or lap_time <= 0:
        return "---"
    minutes, seconds = divmod(float(lap_time), 60.0)
    return f"{int(minutes)}:{seconds:06.3f}"


#--------------------------------------------------------------------------------------------------------------#
# Gère les meilleurs tours : chargement, sauvegarde, comparaison aux records.                                  #
#--------------------------------------------------------------------------------------------------------------#
class RecordManager:
    """
    Responsabilités :
    - Charger/sauvegarder les meilleurs temps (via DataStore)
    - Comparer un temps au record personnel d'un joueur
    - Obtenir le meilleur temps pour un joueur/combo donné
    - Formater les temps pour l'affichage
    """
    
    def __init__(self):
        # Cache des meilleurs tours (rechargé à chaque sauvegarde pour cohérence)
        self._best_laps: dict = DataStore.load_best_laps()
    
    #--------------------------------------------------------------------------------------------------------------#
    # Recharge les meilleurs tours depuis le disque (après modification externe par exemple).                     #
    #--------------------------------------------------------------------------------------------------------------#
    def reload(self):
        """Recharge les meilleurs tours depuis le fichier."""
        self._best_laps = DataStore.load_best_laps()
    
    #--------------------------------------------------------------------------------------------------------------#
    # Retourne le meilleur temps d'un joueur pour un combo track|car donné, ou None.                              #
    #--------------------------------------------------------------------------------------------------------------#
    def get_personal_best(self, player: str, track_id: int, car_id: int) -> Optional[float]:
        """
        Retourne le meilleur temps enregistré pour un joueur sur un combo track|car.
        Retourne None si aucun temps enregistré.
        """
        if not player or player == "---":
            return None
        
        key = f"{track_id}|{car_id}"
        entry = self._best_laps.get(key, {}).get(player)
        
        if entry and isinstance(entry, dict):
            return entry.get("time")
        return None
    
    #--------------------------------------------------------------------------------------------------------------#
    # Sauvegarde un tour et détermine s'il bat le record personnel du joueur.                                     #
    #--------------------------------------------------------------------------------------------------------------#
    def save_lap(self, player: str, track_id: int, car_id: int, lap_time: float) -> bool:
        """
        Sauvegarde un tour valide pour un joueur.
        Retourne True si ce temps bat le record personnel, False sinon.
        """
        if not player or player == "---":
            return False
        
        key = f"{track_id}|{car_id}"
        times = self._best_laps.setdefault(key, {})
        
        prev = times.get(player)
        is_record = (prev is None) or (lap_time < prev["time"])
        
        if is_record:
            times[player] = {
                "time": lap_time,
                "date": datetime.now().isoformat()
            }
            DataStore.save_best_laps(self._best_laps)
            # Recharger après sauvegarde pour cohérence
            self.reload()
        
        return is_record
    
    #--------------------------------------------------------------------------------------------------------------#
    # Retourne le meilleur temps formaté pour l'affichage UI.                                                     #
    #--------------------------------------------------------------------------------------------------------------#
    def get_personal_best_formatted(self, player: str, track_id: Optional[int], car_id: Optional[int]) -> str:
        """
        Retourne le meilleur temps du joueur formaté (M:SS.mmm).
        Retourne '---' si aucun temps ou contexte invalide.
        """
        if track_id is None or car_id is None:
            return "---"
        
        best = self.get_personal_best(player, track_id, car_id)
        return format_lap_time(best) if best else "---"