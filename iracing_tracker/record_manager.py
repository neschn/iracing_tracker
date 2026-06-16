################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/record_manager.py                                                                  #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Gère les meilleurs tours (lecture, sauvegarde, comparaison aux records).                       #
################################################################################################################

from datetime import datetime
from typing import Optional

from iracing_tracker.data_store import DataStore


#--------------------------------------------------------------------------------------------------------------#
# Formate un temps de tour en M:SS.mmm en TRONQUANT aux millièmes (jamais d'arrondi), ou '---' si invalide.    #
#--------------------------------------------------------------------------------------------------------------#
def format_lap_time(lap_time: float) -> str:
    if not lap_time or lap_time <= 0:
        return "---"
    # Conversion en millisecondes puis troncature, pour éviter tout arrondi vers le haut
    try:
        total_ms = int(float(lap_time) * 1000.0)
    except Exception:
        return "---"
    if total_ms < 0:
        return "---"
    minutes = total_ms // 60000
    seconds = (total_ms % 60000) // 1000
    millis = total_ms % 1000
    return f"{minutes}:{seconds:02d}.{millis:03d}"


#--------------------------------------------------------------------------------------------------------------#
# Gère les meilleurs tours : chargement, sauvegarde et comparaison aux records perso/absolu.                   #
#--------------------------------------------------------------------------------------------------------------#
class RecordManager:

    #--------------------------------------------------------------------------------------------------------------#
    # Initialise le cache des meilleurs tours (rechargé après chaque sauvegarde pour rester cohérent).             #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self):
        self._best_laps: dict = DataStore.load_best_laps()

    #--------------------------------------------------------------------------------------------------------------#
    # Recharge les meilleurs tours depuis le disque (ex. après une modification externe).                          #
    #--------------------------------------------------------------------------------------------------------------#
    def reload(self):
        self._best_laps = DataStore.load_best_laps()

    #--------------------------------------------------------------------------------------------------------------#
    # Retourne le meilleur temps d'un joueur pour un combo track|car donné, ou None.                               #
    #--------------------------------------------------------------------------------------------------------------#
    def get_personal_best(self, player: str, track_id: int, car_id: int) -> Optional[float]:
        if not player or player == "---":
            return None

        key = f"{track_id}|{car_id}"
        entry = self._best_laps.get(key, {}).get(player)

        if entry and isinstance(entry, dict):
            return entry.get("time")
        return None

    #--------------------------------------------------------------------------------------------------------------#
    # Sauvegarde un tour s'il bat le record perso ; retourne (is_personal_record, is_absolute_record).             #
    #--------------------------------------------------------------------------------------------------------------#
    def save_lap(self, player: str, track_id: int, car_id: int, lap_time: float) -> tuple[bool, bool]:
        if not player or player == "---":
            return False, False

        # Déterminer le record absolu AVANT d'écrire le nouveau temps
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
            # Recharger après sauvegarde pour rester cohérent avec le disque
            self.reload()

        return is_personal, is_absolute

    #--------------------------------------------------------------------------------------------------------------#
    # Retourne le meilleur temps du joueur formaté (M:SS.mmm), ou '-:--.---' s'il n'y a pas de record.             #
    #--------------------------------------------------------------------------------------------------------------#
    def get_personal_best_formatted(self, player: str, track_id: Optional[int], car_id: Optional[int]) -> str:
        if track_id is None or car_id is None:
            return "-:--.---"

        best = self.get_personal_best(player, track_id, car_id)
        return format_lap_time(best) if best else "-:--.---"

    #--------------------------------------------------------------------------------------------------------------#
    # Retourne le top N des temps d'un combo track|car, trié du meilleur au moins bon.                             #
    #--------------------------------------------------------------------------------------------------------------#
    def get_ranking(self, track_id: int, car_id: int, limit: int = 3) -> list[dict]:
        if track_id is None or car_id is None:
            return []

        key = f"{track_id}|{car_id}"
        times = self._best_laps.get(key, {})

        ranking = []
        for player, entry in times.items():
            if entry and isinstance(entry, dict):
                lap_time = entry.get("time")
                if lap_time and lap_time > 0:
                    ranking.append({"player": player, "time": lap_time})

        ranking.sort(key=lambda x: x["time"])
        return ranking[:limit]

    #--------------------------------------------------------------------------------------------------------------#
    # Indique si un temps est le record absolu (meilleur parmi tous les joueurs) du combo.                         #
    #--------------------------------------------------------------------------------------------------------------#
    def is_absolute_record(self, track_id: int, car_id: int, lap_time: float) -> bool:
        ranking = self.get_ranking(track_id, car_id, limit=1)
        if not ranking:
            return True  # Premier temps enregistré = record absolu
        return lap_time <= ranking[0]["time"]
