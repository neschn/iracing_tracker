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
    # Sauvegarde un tour et détermine s'il bat le record personnel et/ou absolu.                                  #
    #--------------------------------------------------------------------------------------------------------------#
    def save_lap(self, player: str, track_id: int, car_id: int, lap_time: float) -> tuple[bool, bool]:
        """
        Sauvegarde un tour valide pour un joueur.
        Retourne (is_personal_record, is_absolute_record).
        """
        if not player or player == "---":
            return False, False
        
        # Vérifier si record absolu AVANT sauvegarde
        is_absolute = self.is_absolute_record(track_id, car_id, lap_time)
        
        key = f"{track_id}|{car_id}"
        times = self._best_laps.setdefault(key, {})
        
        prev = times.get(player)
        is_personal = (prev is None) or (lap_time < prev["time"])
        
        if is_personal:
            times[player] = {
                "time": lap_time,
                "date": datetime.now().isoformat()
            }
            DataStore.save_best_laps(self._best_laps)
            # Recharger après sauvegarde pour cohérence
            self.reload()
        
        return is_personal, is_absolute
    
    #--------------------------------------------------------------------------------------------------------------#
    # Retourne le meilleur temps formaté pour l'affichage UI.                                                     #
    #--------------------------------------------------------------------------------------------------------------#
    def get_personal_best_formatted(self, player: str, track_id: Optional[int], car_id: Optional[int]) -> str:
        """
        Retourne le meilleur temps du joueur formaté (M:SS.mmm).
        Retourne toujours '-:--.---' si pas de record (peu importe si session active ou non).
        """
        if track_id is None or car_id is None:
            return "-:--.---"
        
        best = self.get_personal_best(player, track_id, car_id)
        return format_lap_time(best) if best else "-:--.---"
    
    #--------------------------------------------------------------------------------------------------------------#
    # Retourne le classement des N meilleurs temps pour un combo track|car.                                        #
    #--------------------------------------------------------------------------------------------------------------#
    def get_ranking(self, track_id: int, car_id: int, limit: int = 3) -> list[dict]:
        """
        Retourne le top N des temps pour un combo track|car.
        Format : [{"player": "Nico", "time": 65.123}, ...]
        Trié du meilleur au moins bon.
        """
        if track_id is None or car_id is None:
            return []
        
        key = f"{track_id}|{car_id}"
        times = self._best_laps.get(key, {})
        
        # Construire liste [(player, time), ...] et trier
        ranking = []
        for player, entry in times.items():
            if entry and isinstance(entry, dict):
                lap_time = entry.get("time")
                if lap_time and lap_time > 0:
                    ranking.append({"player": player, "time": lap_time})
        
        # Trier par temps croissant
        ranking.sort(key=lambda x: x["time"])
        
        # Retourner les N premiers
        return ranking[:limit]
    
    #--------------------------------------------------------------------------------------------------------------#
    # Vérifie si un temps est le record absolu (meilleur parmi TOUS les joueurs).                                 #
    #--------------------------------------------------------------------------------------------------------------#
    def is_absolute_record(self, track_id: int, car_id: int, lap_time: float) -> bool:
        """
        Retourne True si ce temps est le meilleur absolu pour ce combo track|car.
        """
        ranking = self.get_ranking(track_id, car_id, limit=1)
        if not ranking:
            return True  # Premier temps enregistré = record absolu
        return lap_time <= ranking[0]["time"]