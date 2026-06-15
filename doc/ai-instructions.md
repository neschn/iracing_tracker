# 🧠 Fichier d’instructions et de mise en contexte pour IA  
*(Projet : iRacing Tracker)*

---

## 🏎️ Contexte général

Je développe un **logiciel personnel** permettant d’enregistrer et d’afficher en temps réel les temps et records réalisés sur **iRacing** avec mes amis.  
iRacing ne proposant pas nativement l’enregistrement local des temps, j’utilise le **SDK officiel d’iRacing (`irsdk`)** pour récupérer la télémétrie en direct.

Le programme est destiné à être lancé **en même temps qu’iRacing**, et détecte automatiquement :
- le **circuit actuel** (et son identifiant unique),
- la **voiture utilisée**,
- les **joueurs enregistrés** dans le fichier `players.json`.
- La **météo** n’est pas prise en compte pour l’instant.

---

## 🎯 Objectif principal (non exhaustif et évolutif)

Créer un **tableau de suivi des performances locales** sur iRacing, capable de :
- Enregistrer automatiquement les **meilleurs tours personnels** pour chaque joueur, circuit et voiture.  
  > Exemple : le temps de “Nico” sur un circuit en F1 ne doit pas écraser son record avec une F3.
- Afficher en temps réel (pour le combo *circuit + voiture*):
  - le **temps du tour actuel**,  
  - le **meilleur temps personnel**,  
  - le **record absolu**,  
  - le **classement global** entre les joueurs.
- Ne valider que des tours **propres (0x)** : sans sortie de piste, contact, ni incident.  
  Le **premier tour** n’est jamais pris en compte (il sert de tour de lancement).
- Gérer dynamiquement les **joueurs** (ajout, suppression, sélection).
- Afficher une **bannière de messages importants** (record battu, session terminée, attente, etc.).
- Mettre en évidence les événements par **animations et couleurs** (record battu personnel ou absolu).
- Fournir une **zone de debug** affichant les variables IRSDK utiles en temps réel.
- Rester léger, fluide et utilisable en course, sans bloquer l’interface.
- Toutes les fonctionnalités doivent impérativement fonctionner à la fois en local (Test Drive) et en ligne (Practice, Qualifs, Course, etc...)

---

## ⚙️ Aspects techniques clés

- Le logiciel est écrit en **Python**.  
- L’interface graphique utilise **Qt**, avec une architecture thread-safe :
  - le **thread principal** gère exclusivement l’UI,  
  - la **boucle de télémétrie** tourne dans un **thread secondaire**,  
  - la communication entre les deux passe par une **`queue.Queue()`** et des appels **`.after()`** côté UI.  
- Les données iRSDK sont lues via :
  - `IRClient.freeze_and_read()` pour récupérer un set de variables,
  - `IRClient.is_session_active()` pour vérifier la connexion et la session.
- Le programme détecte automatiquement :
  - le **changement de session** (nouveau circuit ou redémarrage iRacing),
  - la **position de la voiture** (garage, pit lane, piste),
  - et **relance proprement le SDK** si nécessaire.

---

## 🧩 Particularités et comportements à respecter

- Lors d’un **changement de session**, il est **impératif** d’appeler :
  ```python
  ir_client.ir.shutdown()
  ```
  Cela réinitialise le buffer iRSDK et permet de récupérer correctement le **nouveau contexte (track/car)**.  
  Sans ce reset, les premières lectures après un changement de session renvoient encore les données de la session précédente.

- Les tours **invalides** (1x, off-track, etc.) doivent **absolument être exclus** de l’enregistrement.  
  Seuls les tours **0x et complets** sont sauvegardés dans `best_laps.json`.

- L’UI utilise(ra) une **grille (`grid`)** flexible avec :
  - une **bannière** en haut (messages importants),
  - une **zone principale** à gauche (infos, joueur, records),
  - une **zone debug** à droite (activable/désactivable via le menu “Affichage”),
  - une **zone logs** en bas.

- Le fichier `main.py` gère :
  - la **boucle principale** (`loop()`),
  - la **lecture IRSDK** (10 Hz pour les données légères, 2 s pour le YAML lourd, à voir si on adapte ça),
  - la **validation des tours** via la classe `LapValidator`.

- Le validateur de tours (`lap_validator.py`) :
  - surveille les incidents (`PlayerCarMyIncidentCount`),
  - détecte les passages de ligne (`LapCompleted`),
  - exclut le premier tour et les tours invalides,
  - garde la **baseline d’incidents** du début de tour pour détecter correctement les 1x.

---

## 🧠 Directives importantes pour l'IA

Directives A NE SURTOUT JAMAIS JAMAIS JAMAIS OUBLIER  tu m’aides dans le développement :

- **Ne modifie jamais** le comportement global ou d’autres parties du code que celles que je te demande explicitement.  
- Si tu penses qu’une logique semble inutile ou pourrait être simplifiée, **réfléchis d’abord à sa raison d’être** : certains comportements sont spécifiques à iRacing et ne sont pas toujours logiques à première vue.  
- À contrario, certaines fois avec les modifications de code qui s'enchainent, le code a tendance a se compléxifier et peut au bout d'un moment être refactoriser. Je suis toujours partisans de refactoriser et d'avoir quelque chose de propre, donc même si il faut faire attention à pourquoi les choses sont codées comme ça, il faut toujours se remettre en question pour voir s'il n'y a pas de manière plus simple ou plus optimisée de faire.
- Le refactor seront demandé par l'utilisateur à certaine étapes de développement. Tu peux en proposer également quand tu juge ça nécessaire, mais il faut toujours me prévenir avant de le faire pour pas que je ne sois surpris.
- Préfère toujours le code **clair, concis et commenté** (en français).  
- **Si un correctif ne fonctionne pas**, cherche le problème ailleurs ou aborde-le **sous un autre angle** avant de tout remettre en cause.  
- **“Less is more”** : évite la complexité inutile, favorise la lisibilité et la robustesse.  
- Les commentaires doivent **expliquer la logique métier** et non juste paraphraser le code.
- Renseigne toi sur IRSDK et son comportement si tu n'est pas certains de ce que tu proposes, tu es autorisé à consulter sur le web et Github si nécessaire
- Tu as le droit de remettre en question ce qui a été fait, tout peut toujours être améioré.
- Toujours garder le format d'ent-ête (exemple plus bas dans ce fichier) et mettre à jour la date de modification dans cet en-tête
- Toujours intégrer un petit descriptif devant une classe / méthode / section / fonction, selon le même format (exemple plus bas dans ce fichier)
- Toujours utiliser le "#" pour faire des commentaires, même si ils sont sur plusieures lignes (on met un # à chaque ligne). Jamais utiliser les commentaires de type avec les "
- Tu peux t'aider sur le GitHub de pyirsdk si besoin : https://github.com/kutu/pyirsdk.git

---

## 📄 Résumé rapide
- **Langage :** Python  
- **SDK utilisé :** iRSDK officiel  
- **Interface :** Tkinter (thread principal uniquement)  
- **Stockage :** JSON (atomique, stable, lisible)  
- **Objectif final :** un tracker iRacing local, stable, simple, fluide et fiable.

---
## 📄 Commmentaire d'ent-ête des fichiers python :

################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : dossier/fichier.py                                                                                 #
# Date de modification : JJ.MM.AAAA                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : description de l'utilité du fichier                                                            #
################################################################################################################

## 📄 Commmentaire d'une ligne juste au-dessus toutes les classes / méthodes / sections / fonctions :

#--------------------------------------------------------------------------------------------------------------#
# Description de la classe / méthode / section / fonction                                                      #
#--------------------------------------------------------------------------------------------------------------#                                       


