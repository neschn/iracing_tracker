# 🧭 Dev Cheatsheet — Git, Bash & Bonnes pratiques (usage solo VS Code + GitHub)

Ce document sert d’aide-mémoire pour utiliser **Git**, **GitHub** et **les commandes Bash courantes** dans ton environnement de développement.

---

## ⚙️ Commandes Bash utiles pour ton projet

```bash
cd C:\iracing_tracker                                   
.venv310\Scripts\python.exe -m iracing_tracker.main     
```
## ⚙️ Dossiers
%LOCALAPPDATA%\iRacingTracker                           # Données
---

## 🚀 Principes de base

- **Git** enregistre l’historique de ton code sous forme de *commits* (sauvegardes locales).  
- **GitHub** sert à héberger ton dépôt Git en ligne (sauvegarde cloud).  
- Tu peux travailler **hors ligne** et pousser (`push`) quand tu veux.  
- La branche **main** doit toujours rester stable (elle compile et fonctionne).

---

## 💾 Démarrer un projet

```bash
git init                                                # Initialise Git dans le dossier courant (crée le dossier caché .git)
git add .                                               # Ajoute tous les fichiers actuels à la zone de préparation (stage)
git commit -m "chore: initial commit"                   # Crée ton premier commit avec un message descriptif
git branch -M main                                      # Renomme la branche actuelle en "main" (branche principale standard)
git remote add origin <url>                             # Lie ton dépôt local au dépôt distant sur GitHub (SSH ou HTTPS)
git push -u origin main                                 # Envoie la branche "main" sur GitHub et établit le lien de suivi (-u = une seule fois)
```

---

## 🔁 Workflow simple (usage solo)

```bash
git status                                              # Affiche l’état des fichiers modifiés ou non suivis
git add .                                               # Prépare tous les changements pour le prochain commit
git commit -m "feat: add new feature"                   # Crée un commit local avec un message clair
git push                                                # Envoie les commits sur GitHub (optionnel, quand tu veux)
```

💡 Tu peux faire plusieurs commits dans la journée et ne pousser qu’une fois le soir :  
tout ton historique sera alors synchronisé d’un coup.

---

## 🌿 Gérer les branches

### Créer et basculer sur une nouvelle branche
```bash
git checkout main                                       # Se place sur la branche principale "main"
git checkout -b feat/lap-validator                      # Crée et bascule sur une branche "feat/lap-validator"
```

### Commits et push sur ta branche
```bash
git add .                                               # Prépare les fichiers modifiés
git commit -m "feat: implement lap validator"           # Crée un commit avec un message clair
git push -u origin feat/lap-validator                   # Pousse la nouvelle branche sur GitHub et établit le suivi
```

### Fusionner ta branche vers main
```bash
git checkout main                                       # Revient sur "main"
git merge feat/lap-validator                            # Fusionne les changements de ta branche dans "main"
git push                                                # Pousse la version mise à jour de "main" sur GitHub
```

### Nettoyer ensuite
```bash
git branch -d feat/lap-validator                        # Supprime la branche localement
git push origin --delete feat/lap-validator             # Supprime la même branche sur GitHub
```

---

## 🧩 Types de branches (convention)

| Préfixe | Signification |
|----------|---------------|
| feat/     | Nouvelle fonctionnalité |
| fix/      | Correction de bug |
| refactor/ | Réécriture sans changement de comportement |
| chore/    | Maintenance, dépendances, configuration |
| docs/     | Documentation |
| test/     | Tests |
| perf/     | Optimisation |

---

## ✍️ Rédiger des commits (Conventional Commits)

**Format général :**
```
<type>: <description claire à l’infinitif>
```

**Exemples :**
```
feat: add telemetry parser
fix: prevent crash when data missing
refactor: simplify lap validator
chore: update dependencies
```

**Commit plus détaillé :**
```
feat: add telemetry parsing for new cars

- added data model
- integrated into main loop
- updated docs accordingly
```

---

## 🔥 Hotfix (corriger un bug critique sur main)

```bash
git checkout main                                       # Se place sur "main"
git checkout -b hotfix/crash-on-start                   # Crée une branche hotfix pour corriger le bug
# corrige le bug dans le code
git add .                                               # Ajoute les fichiers corrigés
git commit -m "fix: prevent crash on start"             # Crée le commit de correction
git push -u origin hotfix/crash-on-start                # Pousse la branche hotfix sur GitHub
git checkout main                                       # Retourne sur main
git merge hotfix/crash-on-start                         # Fusionne la correction dans main
git push                                                # Pousse main mise à jour sur GitHub
git branch -d hotfix/crash-on-start                     # Supprime la branche locale
git push origin --delete hotfix/crash-on-start          # Supprime la branche sur GitHub
```

---

## 🧰 Mettre son travail de côté (stash)

```bash
git stash -u                                            # Sauvegarde temporairement les changements en cours (y compris les fichiers non suivis)
git checkout main                                       # Change de branche pour corriger un bug ailleurs
git checkout feat/ma-branche                            # Reviens sur ta branche de travail
git stash pop                                           # Restaure les changements sauvegardés
```

---

## 🧹 Annuler ou corriger rapidement

```bash
git restore <fichier>                                   # Annule les modifications non stagées (non ajoutées)
git restore --staged <fichier>                          # Retire un fichier de la zone de préparation
git reset --soft HEAD~1                                 # Annule le dernier commit mais garde les fichiers modifiés
git reset --hard HEAD~1                                 # Annule complètement le dernier commit + les changements
git commit --amend --no-edit                            # Modifie le dernier commit sans changer le message
```

---

## 🔎 Commandes utiles à retenir

```bash
git status                                              # Affiche l’état actuel du dépôt
git log --oneline --graph --all                         # Montre un historique graphique compact
git branch                                              # Liste toutes les branches locales
git remote -v                                           # Montre les dépôts distants configurés
git diff                                                # Compare les fichiers modifiés avec le dernier commit
```

---

## 🧠 Commandes essentielles à retenir par cœur

```bash
git add .                                               # Ajoute tous les fichiers modifiés à la zone de préparation
git commit -m "message"                                 # Crée un commit local avec un message descriptif
git push                                                # Pousse tes commits sur GitHub
git checkout -b feat/ma-branche                         # Crée et bascule sur une nouvelle branche
git checkout main                                       # Revient sur la branche principale
git merge feat/ma-branche                               # Fusionne la branche de travail dans main
git branch -d feat/ma-branche                           # Supprime la branche locale une fois fusionnée
```

---

## 📘 Structure recommandée du README

- **Description courte** du projet  
- **Installation et lancement** (environnement virtuel, dépendances)  
- **Structure rapide** du dossier (src, data, doc, etc.)  
- **Configuration** (.env, chemins, ports éventuels)  
- **Roadmap / TODO**  
- **Licence** (optionnelle)

---
