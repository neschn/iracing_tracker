# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# CLAUDE.md — Instructions projet iRacing Tracker

## Commandes

Toutes les commandes s'exécutent depuis `C:\iracing_tracker` avec l'environnement virtuel `.venv310` (Python 3.10, Windows uniquement).

```bash
# Installer les dépendances (PySide6 est requis en plus de pyirsdk)
.venv310\Scripts\python.exe -m pip install -r requirements.txt

# Lancer l'application (iRacing doit tourner pour avoir de la télémétrie réelle)
.venv310\Scripts\python.exe -m iracing_tracker.main

# Vérification syntaxe / imports d'un fichier modifié (pas de tests automatisés)
.venv310\Scripts\python.exe -m py_compile iracing_tracker\<fichier>.py
```

Il n'existe **aucun test automatisé** ni linter configuré. La validation des tours dépend d'une session iRacing réelle : le comportement métier ne peut pas être confirmé sans iRacing lancé (le signaler clairement, cf. règles plus bas). Hors iRacing, `freeze_and_read()` renvoie des `None` et la boucle reste en attente de session.

`requirements.txt` ne liste que `pyirsdk` ; **PySide6 doit aussi être présent** dans l'environnement (déjà installé dans `.venv310`).

## Architecture du code (vue d'ensemble)

> Note : le `README.md` est partiellement obsolète (il mentionne Tkinter, `ui.py` et un dossier `data/`). La réalité du code : **PySide6**, un package `ui/`, et les données stockées dans `%LOCALAPPDATA%\iRacingTracker` (configurable via `IRTRACKER_DATA_DIR`).

### Modèle de threads

Deux threads, comme exigé par les règles projet :

* **Thread principal** : la boucle Qt (`TrackerUI.mainloop()` dans [iracing_tracker/ui/app.py](iracing_tracker/ui/app.py)). Toute mutation de l'UI doit rester ici.
* **Thread worker (daemon)** : `loop()` dans [iracing_tracker/main.py](iracing_tracker/main.py) — lecture télémétrie, détection/validation des tours, sauvegarde des records.

Communication **uniquement** via une `queue.Queue` thread-safe :

* worker → UI : le worker appelle `UIBridge` ([iracing_tracker/ui_bridge.py](iracing_tracker/ui_bridge.py)), qui pousse des tuples `(name, payload)` dans la queue (avec coalescing pour éviter les updates redondants). L'UI vide la queue toutes les 16 ms via un `QTimer` (`_pump_event_queue`).
* UI → worker : l'état partagé (`selected_player`, `runtime_flags`) est protégé par des `threading.Lock` créés dans `main()`.

Ne jamais toucher l'UI depuis le worker autrement que par `UIBridge`.

### Chaîne de traitement (un tour de boucle)

`main.py loop()` orchestre, de façon volontairement légère, des *managers* spécialisés :

1. **`IRClient`** ([irsdk_client.py](iracing_tracker/irsdk_client.py)) — encapsule `irsdk.IRSDK`. `freeze_and_read(vars)` fige le buffer et lit ; gère startup paresseux et déconnexions (renvoie des `None`). `is_session_active()` teste `SessionUniqueID`.
2. **`TelemetryReader`** ([telemetry_reader.py](iracing_tracker/telemetry_reader.py)) — lit les variables iRSDK par catégorie avec throttling : `read_core` (10 Hz, état tour/incidents), `read_context` (0.5 Hz, track/car), `read_debug` (≈3 Hz).
3. **`SessionManager`** ([session_manager.py](iracing_tracker/session_manager.py)) — détecte session active (grâce anti-rebond `SESSION_INACTIVE_GRACE_SECONDS`), maintient le `SessionContext` (track_id/car_id), détecte les changements de contexte et gère les flags de messages.
4. **`LapValidator`** ([lap_validator.py](iracing_tracker/lap_validator.py)) — cœur métier. `LapDetector` détecte la fin d'un tour (gère le délai de MAJ de `LapLastLapTime` via un état *pending*) ; `LapValidator` compare `PlayerCarMyIncidentCount` entre début et fin de tour. Retourne `(status, lap_time, reason)` avec `status ∈ {"valid","invalid","none"}`. Un tour n'est `valid` que si delta incidents = 0, que ce n'est pas un out lap, et que le premier tour (tour de lancement) est ignoré.
5. **`RecordManager`** ([record_manager.py](iracing_tracker/record_manager.py)) — compare au record perso/absolu, sauvegarde via `DataStore`, fournit `get_ranking()`. `format_lap_time()` **tronque** aux millièmes (jamais d'arrondi vers le haut).
6. **`DataStore`** ([data_store.py](iracing_tracker/data_store.py)) — persistance JSON **atomique** (`tempfile` + `os.replace` + `fsync`). Sauvegarde un `.corrupt-<timestamp>` si un JSON est illisible plutôt que de planter.

### Modèle de données

* Clé d'un combo : `"<track_id>|<car_id>"`. `best_laps.json` : `{"<track_id>|<car_id>": {"<player>": {"time": float_secondes, "date": iso8601}}}`.
* `players.json` : liste de noms (dédupliqués, insensible à la casse).
* C'est cette clé `track_id|car_id` qui garantit la règle métier « un record ne doit jamais écraser celui d'un autre circuit ou d'une autre voiture ».

### UI (package `ui/`)

`TrackerUI` ([ui/app.py](iracing_tracker/ui/app.py)) est la façade. L'écran est découpé en panneaux (`session_panel`, `player_panel`, `session_times_panel`, `debug_panel`, `logs_panel`), avec barre de titre custom (`titlebar.py`), thème clair/sombre/système (`theme.py`), bannière de messages (`banner_manager.py`) et constantes de mise en page (`constants.py`). `_pump_event_queue()` est le seul point d'entrée des messages worker→UI.

## Contexte du projet

Ce projet est un logiciel personnel Python pour iRacing.

Objectif : enregistrer, comparer et afficher en temps réel les meilleurs tours locaux de plusieurs joueurs, par combinaison :

* joueur,
* circuit,
* voiture.

Le programme est destiné à être lancé en même temps qu’iRacing. Il utilise `irsdk` / `pyirsdk` pour lire les données de télémétrie et stocke les records localement en JSON.

La météo n’est pas prise en compte pour l’instant.

## Stack technique

* Langage : Python.
* SDK : `irsdk` / `pyirsdk`.
* Interface graphique : Qt / PySide6.
* Stockage : fichiers JSON locaux, lisibles et stables.
* Plateforme cible : Windows uniquement.
* Le programme doit rester léger, fluide et utilisable pendant une session iRacing.

## Architecture générale

Respecter l’architecture existante du projet.

Ne pas déplacer, renommer ou restructurer des fichiers sans raison claire et sans me prévenir avant.

L’interface graphique doit rester gérée par le thread principal.

La lecture télémétrie iRacing doit rester séparée de l’UI pour éviter les blocages.

Les échanges entre la télémétrie et l’UI doivent rester thread-safe.

Le programme doit fonctionner à la fois :

* en local / Test Drive,
* en Practice,
* en Qualifs,
* en Course,
* et plus généralement dans les sessions en ligne.

## Règles métier iRacing importantes

Ne jamais enregistrer un tour invalide.

Seuls les tours complets et propres, avec 0x incident, peuvent être sauvegardés dans `best_laps.json`.

Le premier tour ne doit jamais être pris en compte, car il sert de tour de lancement.

Un temps réalisé avec une voiture ne doit jamais écraser le record d’une autre voiture.

Un temps réalisé sur un circuit ne doit jamais écraser le record d’un autre circuit.

Les records doivent être distingués au minimum par :

* joueur,
* circuit,
* voiture.

Lors d’un changement de session, de circuit ou de voiture, il est impératif de réinitialiser proprement iRSDK.

En particulier, conserver cette logique sauf raison très solide :

```python
ir_client.ir.shutdown()
```

Ce reset permet d’éviter de continuer à lire temporairement l’ancien contexte iRacing après un changement de session.

Ne pas supprimer cette logique sans m’expliquer précisément pourquoi.

## Validation des tours

Le validateur de tours doit surveiller les incidents iRacing.

La logique de validation doit comparer les incidents entre le début et la fin du tour.

Un tour avec une différence d’incidents supérieure à 0 doit être rejeté.

Le validateur doit éviter les faux positifs lors des changements de session, sorties du garage, tours de lancement ou reset iRacing.

Si une correction touche la validation des tours, être très prudent et expliquer le raisonnement avant de modifier.

## Fichiers de données

Les fichiers JSON doivent rester simples, lisibles et robustes.

Ne pas casser la compatibilité des fichiers existants sans proposer une migration.

Les écritures JSON doivent être sûres et éviter autant que possible la corruption de fichier.

Préférer les écritures atomiques lorsqu’un fichier important est modifié.

## Règles de développement

Avant de modifier du code, commencer par comprendre la structure existante.

Pour une tâche non triviale, proposer d’abord un plan court.

Ne jamais modifier le comportement global du programme si la demande concerne seulement une partie précise.

Ne pas supprimer une fonctionnalité existante sans confirmation explicite.

Ne pas remplacer une logique métier spécifique iRacing par une logique générique sans vérifier pourquoi elle existe.

Si une logique semble inutile, chercher d’abord sa raison d’être.

Si un correctif ne fonctionne pas, ne pas tout remettre en cause immédiatement. Chercher aussi si le problème vient d’un autre endroit.

Préférer les solutions simples, lisibles et robustes.

Principe général : less is more.

Éviter la complexité inutile, les abstractions prématurées et les refactors trop larges.

Les refactors sont autorisés et appréciés lorsqu’ils améliorent vraiment la lisibilité ou la stabilité, mais ils doivent être proposés avant d’être appliqués.

## Style de code

Le code doit être clair, concis et maintenable.

Les commentaires doivent être en français.

Les commentaires doivent expliquer la logique métier ou une décision technique importante, pas simplement répéter le code.

Utiliser des commentaires avec `#`.

Ne pas utiliser de chaînes de caractères comme faux commentaires multilignes.

Garder les noms explicites.

Éviter les noms trop courts sauf pour des variables locales évidentes.

Ne pas ajouter de dépendance sans justification.

## En-tête des fichiers Python

Chaque fichier Python doit conserver un en-tête au format suivant.

Mettre à jour la date de modification lorsqu’un fichier est modifié.

```python
################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : dossier/fichier.py                                                                                 #
# Date de modification : JJ.MM.AAAA                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : description de l'utilité du fichier                                                            #
################################################################################################################
```

## Commentaires de sections, classes, méthodes et fonctions

Ajouter un petit descriptif avant les classes, méthodes, fonctions ou sections importantes.

Utiliser ce format :

```python
#--------------------------------------------------------------------------------------------------------------#
# Description de la classe / méthode / section / fonction                                                      #
#--------------------------------------------------------------------------------------------------------------#
```

## Workflow Git

Ne jamais supposer que les changements sont validés tant qu’ils ne sont pas commités.

Avant un changement important :

* vérifier l’état Git,
* identifier les fichiers concernés,
* expliquer brièvement le plan.

Après modification :

* afficher ou résumer le diff,
* expliquer ce qui a changé,
* indiquer les fichiers modifiés,
* proposer un message de commit clair.

Ne pas faire de commit si je n’ai pas demandé explicitement de commiter.

Ne pas faire de push si je n’ai pas demandé explicitement de pousser.

Quand je demande un commit, faire un commit par unité logique cohérente.

Éviter les commits énormes qui mélangent bugfix, refactor et nouvelle fonctionnalité.

Messages de commit recommandés :

* `fix: ...`
* `feat: ...`
* `refactor: ...`
* `docs: ...`
* `chore: ...`

## Tests et vérifications

Avant de considérer une tâche comme terminée, lancer les vérifications adaptées au projet quand c’est possible.

Si aucun test automatique n’existe, au minimum :

* vérifier la syntaxe Python,
* vérifier les imports touchés,
* expliquer ce qui doit être testé manuellement dans iRacing.

Ne pas prétendre qu’un comportement iRacing est validé si aucun test réel ou simulation fiable n’a été fait.

Quand un test dépend d’iRacing lancé, le signaler clairement.

## Sécurité et fichiers sensibles

Ne pas lire, afficher ou modifier de secrets inutilement.

Ne pas inclure de tokens, clés API, mots de passe ou chemins sensibles dans les commits.

Ne pas modifier les fichiers d’environnement ou de configuration sensible sans demande explicite.

## Recherche et incertitude

Si une information liée à iRacing, iRSDK ou pyirsdk est incertaine, ne pas inventer.

Chercher dans le code existant, dans les commentaires et dans la documentation disponible.

Si l’accès web est disponible, consulter au besoin :

* la documentation iRacing pertinente,
* le repo pyirsdk : https://github.com/kutu/pyirsdk

Si l’information reste incertaine, me le dire clairement et proposer une approche prudente.

## Façon de répondre

Être direct et pratique.

Éviter les longues explications inutiles.

Quand plusieurs options existent, recommander clairement la meilleure option.

Toujours signaler les risques d’un changement avant de toucher à une partie sensible du programme.

Ne pas me noyer avec des détails internes si une réponse courte suffit.

## Priorité absolue

La priorité est d’avoir un tracker iRacing :

* fiable,
* simple,
* fluide,
* robuste,
* facile à maintenir,
* et qui ne casse pas les comportements déjà validés.
