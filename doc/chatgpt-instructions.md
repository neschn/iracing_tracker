# 🧠 Fichier d’instructions et de mise en contexte pour ChatGPT  
*(Projet : iRacing Tracker)*

---

## 🏎️ Contexte général

Je développe un **logiciel personnel** permettant d’enregistrer et d’afficher en temps réel les temps et records réalisés sur **iRacing** avec mes amis.  
iRacing ne proposant pas nativement l’enregistrement local des temps, j’utilise le **SDK officiel d’iRacing (`irsdk`)** pour récupérer la télémétrie en direct.

Le programme est destiné à être lancé **en même temps qu’iRacing**, sur un **écran secondaire**, et détecte automatiquement :
- le **circuit actuel** (et son identifiant unique),
- la **voiture utilisée**,
- les **joueurs enregistrés** dans le fichier `players.json`.

Les données sont stockées dans deux fichiers JSON :
- `players.json` → liste des joueurs enregistrés,  
- `best_laps.json` → meilleurs temps pour chaque joueur, par circuit et par voiture.

La **météo** n’est pas prise en compte pour l’instant.

---

## 🎯 Objectif principal

Créer un **tableau de suivi des performances locales** sur iRacing, capable de :
- Enregistrer automatiquement les **meilleurs tours personnels** pour chaque joueur, circuit et voiture.  
  > Exemple : le temps de “Nico” sur un circuit en F3 ne doit pas écraser son record avec une F1.
- Afficher en temps réel (pour le combo *circuit + voiture*):
  - le **temps du tour actuel**,  
  - le **meilleur temps personnel**,  
  - le **record absolu**,  
  - le **classement global** entre les joueurs.
- Ne valider que des tours **propres (0x)** : sans sortie de piste, contact, ni incident.  
  Le **premier tour** n’est jamais pris en compte (il sert de tour de lancement).
- Gérer dynamiquement les **joueurs** (ajout, suppression, sélection).
- Afficher une zone de logs avec tout ce qui se passe d'important et des message pour les utilisateurs
- Afficher une **bannière de messages importants** (record battu, session terminée, attente, etc.).
- Mettre en évidence les événements par **animations et couleurs** (record battu personnel ou absolu).
- Fournir une **zone de debug** affichant les variables IRSDK utiles en temps réel.
- Rester léger, fluide et utilisable en course, sans bloquer l’interface.

---

## ⚙️ Aspects techniques clés

- Le logiciel est écrit en **Python**.  
- L’interface graphique utilise **Tkinter**, avec une architecture thread-safe :
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
