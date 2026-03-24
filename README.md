# EmotionConfigurable (point d’entrée)

## Description
Ce projet fournit une petite application en ligne de commande centrée sur **EmotionConfigurable**.
Elle lance une boucle de dialogue interactive : vous tapez du texte, l’outil appelle un **oracle d’émotions** et affiche une réponse.

L’oracle est le script [Code/oracle.py](Code/oracle.py) : il reçoit un texte, renvoie un **JSON** avec (au minimum) une émotion primaire et une confiance.
EmotionConfigurable parse ce JSON, convertit la confiance en niveau (`low`/`medium`/`high`), puis applique un **mapping JSON** pour choisir le texte de réponse.

## Commande de lancement du script
```bash
python3 Code/EmotionConfigurable/EmotionConfigurable.py \
  --oracle-config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json \
  --response-mapping Emotion/EmotionProjetBase/response_mapping_emotiondamage.json
```

### Flux principal
`texte saisi` → [Code/oracle.py](Code/oracle.py) → `JSON` → [Code/EmotionConfigurable/EmotionConfigurable.py](Code/EmotionConfigurable/EmotionConfigurable.py) → `mapping JSON` → `réponse affichée`

## Fonctionnalités principales
- Boucle de dialogue interactive (prompt `Vous: `).
- Appel de l’oracle via `subprocess` (même interpréteur Python).
- Parsing du JSON oracle et extraction de `primary_emotion_id` + confiance.
- Conversion confiance → niveau (`low`/`medium`/`high`) via seuils configurés.
- Mapping configurable : réponse par émotion et par niveau de confiance.

## Technologies utilisées
- Python 3.10+ recommandé (le fichier [Code/oracle.py](Code/oracle.py) utilise des annotations de types modernes).
- Bibliothèque standard uniquement (`argparse`, `json`, `subprocess`, `pathlib`, …).
- JSON pour les configurations.

## Installation
Prérequis : Python 3.

Optionnel (environnement virtuel) :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Aucun `requirements.txt` n’est fourni : exécution directe avec la stdlib.

## Utilisation
### Lancement
```bash
python3 Code/EmotionConfigurable/EmotionConfigurable.py \
  --oracle-config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json \
  --response-mapping Emotion/EmotionProjetBase/response_mapping_emotiondamage.json
```

Arguments CLI (observés dans le code) :
- `--oracle-config` : chemin vers la config JSON de l’oracle (passée à `oracle.py --config`).
- `--response-mapping` : chemin vers le mapping JSON des réponses.

Entrées/sorties :
- Entrée : saisie utilisateur via `input()` (boucle).
- Sortie : réponse sur stdout.
- Erreurs : sur stderr.
- Codes retour : `0` (EOF/Ctrl+C), `2` (erreur de config ou oracle).

## Structure du projet
- [Code/EmotionConfigurable/EmotionConfigurable.py](Code/EmotionConfigurable/EmotionConfigurable.py) : point d’entrée (boucle + mapping).
- [Code/oracle.py](Code/oracle.py) : oracle heuristique (sortie JSON).
- [Emotion/EmotionProjetBase/](Emotion/EmotionProjetBase/) : exemples de config JSON (oracle + mapping).
- [test/](test/) : scripts/fixtures (principalement liés à un autre script du dépôt).
- [Documentation/](Documentation/) : documents complémentaires.

## Exemples d’utilisation
### 1) Lancement standard (depuis la racine)
```bash
python3 Code/EmotionConfigurable/EmotionConfigurable.py \
  --oracle-config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json \
  --response-mapping Emotion/EmotionProjetBase/response_mapping_emotiondamage.json
```

### 2) Diagnostic oracle (exécution directe)
```bash
python3 Code/oracle.py \
  --config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json \
  --text "I feel anxious today"
```

### 3) Erreur fréquente : mapping introuvable
```bash
python3 Code/EmotionConfigurable/EmotionConfigurable.py \
  --oracle-config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json \
  --response-mapping does/not/exist.json
```

### 4) Erreur fréquente : config oracle introuvable
```bash
python3 Code/EmotionConfigurable/EmotionConfigurable.py \
  --oracle-config does/not/exist.json \
  --response-mapping Emotion/EmotionProjetBase/response_mapping_emotiondamage.json
```
