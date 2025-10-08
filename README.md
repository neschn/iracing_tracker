# 🏎️ iRacing Tracker

Un logiciel personnel permettant d’enregistrer, suivre et afficher en temps réel les **records de tours** sur *iRacing*, développé en **Python** à l’aide du SDK officiel **IRSDK**.

---

## 📖 Sommaire
1. [Contexte](#-contexte)
2. [Fonctionnalités principales](#-fonctionnalités-principales)
3. [Structure du projet](#-structure-du-projet)
4. [Installation et exécution](#-installation-et-exécution)
5. [Utilisation](#-utilisation)
6. [Aspects techniques](#-aspects-techniques)
7. [Fichiers de données](#-fichiers-de-données)
8. [Documentation complémentaire](#-documentation-complémentaire)
9. [Roadmap / TODO](#-roadmap--todo)

---

## 🧭 Contexte

*iRacing Tracker* a été conçu pour combler une limite du simulateur **iRacing** :  
> iRacing ne permet pas nativement d’enregistrer les temps réalisés localement.  

Le but de ce projet est de fournir un **outil local, simple et fluide**, affichant en temps réel :
- le **temps actuel** du joueur,
- son **record personnel** pour le combo *circuit + voiture*,
- le **record absolu** entre plusieurs joueurs,
- et diverses informations de session (piste, voiture, état, etc.).

Le logiciel tourne en **parallèle d’iRacing** sur un écran secondaire.

---

## 🚀 Fonctionnalités principales

- ✅ Enregistrement automatique des **records personnels** par joueur, circuit et voiture  
- ✅ Gestion multi-joueurs (ajout, suppression, sélection)  
- ✅ Détection automatique du **circuit** et de la **voiture actuelle**  
- ✅ Enregistrement uniquement des tours **propres (0x)** — sans sortie de piste ni contact  
- ✅ Affichage temps réel :
  - du **tour actuel**
  - du **record personnel**
  - du **record absolu**
- ✅ Interface claire et fluide via **Tkinter**
- ✅ Logs détaillés des événements (session, validation, erreurs, etc.)
- ✅ Zone debug avec les variables IRSDK en temps réel
- ✅ Système de bannière (messages dynamiques : records, attente, etc.)
- ✅ Sauvegarde des données au format JSON, de manière atomique (sécurisée)

---

## 🧱 Structure du projet

```
iracing_tracker/
│
├── iracing_tracker/
│   ├── main.py                # Boucle principale (lecture IRSDK, UI, logique)
│   ├── ui.py                  # Interface graphique (Tkinter)
│   ├── lap_validator.py       # Validation des tours (logique 0x, incidents, etc.)
│   ├── irsdk_client.py        # Gestion du client IRSDK
│   ├── data_store.py          # Lecture/écriture atomique des fichiers JSON
│   └── __init__.py
│
├── data/
│   ├── players.json           # Liste des joueurs enregistrés
│   └── best_laps.json         # Records enregistrés (clé = track_id|car_id)
│
├── doc/
│   ├── dev-cheatsheet.md      # Commandes Git/Bash utiles
│   ├── to-do-and-bugs.md      # Liste de tâches et bugs connus
│   └── chatgpt-instructions.md# Contexte complet pour relancer ChatGPT
│
└── README.md
```

---

## ⚙️ Installation et exécution

### 1️⃣ Cloner le dépôt

```bash
git clone https://github.com/neschn/iracing-tracker.git
cd iracing-tracker
```

### 2️⃣ Créer et activer un environnement virtuel

```bash
python -m venv .venv310
.venv310\Scripts\activate     
```

### 3️⃣ Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4️⃣ Lancer le programme

```bash
cd C:\iracing_tracker
.venv310\Scripts\python.exe -m iracing_tracker.main
```

> 💡 iRacing doit être **lancé** avant ou en même temps que le programme.

---

## 🖥️ Utilisation

- Lancer *iRacing Tracker* pendant qu’iRacing est en cours d’exécution.  
- Le logiciel détecte automatiquement le **circuit** et la **voiture**.  
- La fenêtre principale affiche :
  - le **nom du circuit et de la voiture**
  - le **record personnel du joueur sélectionné**
  - le **tour actuel** (en temps réel)
  - les **logs** en bas de l’écran
  - la **zone debug** à droite (activable via le menu *Affichage → Debug*)

Les joueurs peuvent être sélectionnés depuis le menu déroulant à gauche.

---

## 🧩 Aspects techniques

- **Langage :** Python  
- **Interface :** Tkinter  
- **Télémétrie :** iRSDK  
- **Thread principal :** Interface graphique  
- **Thread secondaire :** Lecture télémétrie et logique métier  
- **Communication inter-threads :** `queue.Queue()` et `.after()` Tkinter  
- **Persistance :** JSON (atomique : écriture temporaire `.tmp` puis `os.replace`)  
- **Gestion de sessions iRacing :**
  - Détection automatique de session active
  - Appel obligatoire à `ir_client.ir.shutdown()` lors d’un changement de session
  - Lecture différée du contexte (WeekendInfo / DriverInfo) toutes les 2 s

---

## 📂 Fichiers de données

| Fichier | Rôle |
|----------|------|
| `players.json` | Contient la liste des joueurs enregistrés |
| `best_laps.json` | Contient les records par joueur, circuit et voiture, au format :<br>`"trackID|carID": {"Nico": {"time": 34.694, "date": "2025-10-07T23:02:09"}}` |

---

## 📚 Documentation complémentaire

| Fichier | Description |
|----------|-------------|
| `doc/dev-cheatsheet.md` | Aide Git/Bash et bonnes pratiques |
| `doc/to-do-and-bugs.md` | Tâches et bugs connus |
| `doc/chatgpt-instructions.md` | Fiche de contexte complète pour ChatGPT |

---

## 🗺️ Roadmap / TODO

- [ ] Ajouter un classement global des joueurs par circuit  
- [ ] Finaliser la bannière de messages dynamiques  
- [ ] Ajouter les statistiques globales (moyennes, tours valides, etc.)  
- [ ] Mettre à jour le README pour la version stable

---

## 🧑‍💻 Auteur

**Nicolas Schneeberger**  
Développement, conception et intégration IRSDK.  
Projet personnel non commercial.

---

## ⚖️ Licence

Projet personnel, non distribué publiquement.  
Tous droits réservés.
