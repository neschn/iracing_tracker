# CLAUDE.md — Instructions projet iRacing Tracker

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
