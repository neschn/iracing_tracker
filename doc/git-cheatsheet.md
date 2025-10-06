# 🧭 Git Cheatsheet — usage solo (VS Code + GitHub)

Ce document sert d’aide-mémoire pour utiliser Git et GitHub au quotidien, simplement et proprement.

---

## 🚀 Principes de base
- **Git** enregistre l’historique de ton code sous forme de *commits* (sauvegardes locales).  
- **GitHub** sert uniquement à stocker ces commits en ligne (sauvegarde cloud).  
- Tu peux travailler **hors ligne** et **pousser (`push`)** quand tu veux.  
- La branche **main** reste stable (elle compile et fonctionne).  

---



## 💾 Démarrer un projet
```bash
git init                                                # initialise Git dans ton dossier (crée le sous-dossier .git pour suivre les versions)
git add .                                               # ajoute tous les fichiers actuels du projet à la zone de préparation (stage)
git commit -m "chore: initial commit"                   # crée ton premier commit (point de départ du suivi Git) 
git branch -M main                                      # renomme la branche actuelle en "main" (branche principale standard) 
git remote add origin <url>                             # relie ton dépôt local à un dépôt distant sur GitHub (en SSH ou HTTPS)
git push -u origin main                                 # envoie la branche "main" et son contenu sur GitHub, et établit le lien de suivi (-u = lie la branche distante, a ne faire qu'une seule fois)

```

---

## 🔁 Workflow simple (solo)
```bash
git status                                              # Voir l’état du projet
git add .                                               # Sauvegarder ton travail localement
git commit -m "feat: add new feature"                   # Sauvegarder ton travail localement  
git push                                                # Envoyer sur GitHub (optionnel, quand tu veux)
```

💡 Tu peux faire plusieurs commits dans la journée et ne pousser qu’une fois le soir.  
Tout ton historique sera synchronisé sur GitHub d’un coup.

---

## 🌿 Gérer les branches
### Créer et travailler sur une branche
```bash
git checkout main                                      # se placer sur la branche principale "main"
git checkout -b feat/lap-validator                     # créer et basculer sur une nouvelle branche "feat/lap-validator"
```

### Commits et push sur ta branche
```bash
git add .                                              # ajouter tous les fichiers modifiés, créés ou supprimés à la zone de préparation
git commit -m "feat: implement lap validator"          # créer un commit local avec un message clair décrivant le changement 
git push -u origin feat/lap-validator                  # envoyer la branche sur GitHub et créer le lien de suivi (-u seulement la 1re fois)
```

### Fusionner ta branche vers main
```bash
git checkout main                                      # revenir sur la branche principale "main"
git merge feat/lap-validator                           # fusionner les changements de la branche dans "main"
git push                                               # pousser la version mise à jour de "main" sur GitHub
```

### Nettoyer ensuite
```bash
git branch -d feat/lap-validator                       # supprimer la branche localement après fusion 
git push origin --delete feat/lap-validator            # supprimer la même branche sur GitHub

```


## 🧩 Types de branches (convention)
| Préfixe | Signification |
|-----------|----------------|
| feat/     | nouvelle fonctionnalité |
| fix/      | correction de bug |
| refactor/ | réécriture du code sans changer le résultat |
| chore/    | maintenance, config, dépendances |
| docs/     | documentation |
| test/     | tests |
| perf/     | optimisation |

### Options / flags pour les commandes

| Commande | Signification du flag | Action                                 |
| -------- | --------------------- | -------------------------------------- |
| `-m`     | message               | Ajoute un message au commit            |
| `-M`     | move (force rename)   | Renomme la branche actuelle            |
| `-u`     | upstream              | Lie la branche locale à GitHub         |
| `-b`     | branch                | Crée une nouvelle branche et s’y place |
| `-d`     | delete                | Supprime une branche locale            |

Exemples :  
`feat/telemetry-parser`, `fix/lap-counter`, `refactor/data-structure`.

---

## ✍️ Rédiger des commits (Conventional Commits)
Format :
```
<type>: <description claire à l’infinitif>
```

Exemples :
```
feat: add telemetry parser
fix: prevent crash when data missing
refactor: simplify lap validator
chore: update dependencies
```

Commit plus détaillé :
```
feat: add telemetry parsing for new cars

- added data model
- integrated into main loop
- updated docs accordingly
```

---

## 🔥 Hotfix (corriger un bug critique sur main)
```bash
git checkout main                                      # se placer sur la branche principale "main"
git checkout -b hotfix/crash-on-start                  # créer et basculer sur une nouvelle branche "hotfix/crash-on-start" pour corriger un bug critique
# corrige le bug                                       # effectuer les modifications nécessaires dans le code
git add .                                              # ajouter les fichiers modifiés ou supprimés à la zone de préparation
git commit -m "fix: prevent crash on start"            # créer un commit local décrivant la correction du bug 
git push -u origin hotfix/crash-on-start               # envoyer la branche "hotfix" sur GitHub et créer le lien de suivi
git checkout main                                      # revenir sur la branche principale "main"
git merge hotfix/crash-on-start                        # fusionner la correction depuis la branche "hotfix" vers "main"
git push                                               # pousser la version mise à jour de "main" sur GitHub
git branch -d hotfix/crash-on-start                    # supprimer la branche locale "hotfix" après la fusion
git push origin --delete hotfix/crash-on-start         # supprimer la même branche "hotfix" sur GitHub
```

---

## 🧰 Mettre son travail de côté (stash)
```bash
git stash -u                                            # sauvegarde temporaire
git checkout main                                       # aller corriger un bug ailleurs
git checkout feat/ma-branche                            # aller corriger un bug ailleurs
git stash pop                                           # récupérer ton travail
```

---

## 🧹 Annuler / corriger rapidement
```bash
git restore <fichier>                                   # annule les modifs non stagées
git restore --staged <fichier>                          # retire du stage
git reset --soft HEAD~1                                 # annule le dernier commit (garde les modifs)
git reset --hard HEAD~1                                 # annule commit + modifs locales
git commit --amend --no-edit                            # modifie le dernier commit
```

---

## 🔎 Commandes utiles à retenir
```bash
git status                                              # état du projet
git log --oneline --graph --all                         # historique compact
git branch                                              # liste des branches
git remote -v                                           # voir le dépôt GitHub
git diff                                                # comparer les changements
```

---

## 🧠 Commandes essentielles à retenir par cœur
```bash
git add .                                               # ajoute tous les fichiers modifiés, nouveaux ou supprimés à la "zone de préparation" (stage)
git commit -m "message"                                 # crée un commit (une sauvegarde locale) avec ton message descriptif
git push                                                # envoie tes commits sur GitHub (sauvegarde en ligne)
git checkout -b feat/ma-branche                         # crée et bascule sur une nouvelle branche (ici "feat/ma-branche") à partir de ta branche actuelle
git checkout main                                       # revient sur la branche principale ("main")
git merge feat/ma-branche                               # fusionne les changements de ta branche de travail dans "main"
git branch -d feat/ma-branche                           # supprime la branche locale une fois qu’elle est fusionnée

```

---

## 📘 README — contenu recommandé
- Description courte du projet  
- Installation et lancement  
- Structure rapide du dossier  
- Configuration (.env, chemins, ports)  
- Roadmap / TODO  
- Licence (optionnel)

---


