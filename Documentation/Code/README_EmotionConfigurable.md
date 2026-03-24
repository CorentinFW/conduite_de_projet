# EmotionConfigurable — boucle de dialogue (oracle + mapping)

## Description
`EmotionConfigurable` est un petit outil CLI qui démarre une boucle de dialogue interactive : l’utilisateur saisit une phrase, le programme infère une émotion via un **oracle externe** et affiche une **réponse** choisie à partir d’un **mapping JSON**.

Le script principal est [Code/EmotionConfigurable/EmotionConfigurable.py](../../Code/EmotionConfigurable/EmotionConfigurable.py).
Il s’appuie sur :
- un client oracle qui exécute [Code/oracle.py](../../Code/oracle.py) via `subprocess` (même interpréteur Python que celui qui lance EmotionConfigurable)
- un fichier JSON de configuration de l’oracle (règles de détection / calibration)
- un fichier JSON de mapping de réponses (réponse par émotion et niveau de confiance)

Ce dépôt fournit des exemples prêts à l’emploi dans [Emotion/EmotionProjetBase/](../../Emotion/EmotionProjetBase/).

## Fonctionnalités principales
- Boucle interactive : saisie utilisateur en continu (prompt `Vous: `).
- Appel d’un oracle externe (script Python) via `subprocess` et parsing du JSON renvoyé.
- Sélection d’un niveau de confiance `low` / `medium` / `high` à partir de seuils configurés.
- Sélection d’une réponse textuelle selon : émotion primaire + niveau de confiance.
- Validation stricte des fichiers JSON (mapping) avec messages d’erreur explicites.
- Gestion des entrées vides (réponse par défaut `empty_input_response`).

## Technologies utilisées
- Python 3.10+ (utilisation de l’opérateur `|` dans les annotations de types, côté oracle).
- Bibliothèque standard uniquement : `argparse`, `json`, `subprocess`, `sys`, `pathlib`, `dataclasses`, `typing`.
- Formats : JSON (configs), Markdown (documentation).

## Installation
### Prérequis
- Python 3.10+ recommandé (le dépôt contient aussi [Code/oracle.py](../../Code/oracle.py) qui utilise des annotations modernes).

### Environnement virtuel (optionnel mais conseillé)
Depuis la racine du dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Aucun `requirements.txt` n’est présent : l’outil fonctionne avec la bibliothèque standard.

## Utilisation
### Commande
L’interface CLI est définie dans [Code/EmotionConfigurable/EmotionConfigurable.py](../../Code/EmotionConfigurable/EmotionConfigurable.py).

Arguments requis :
- `--oracle-config` : chemin vers le JSON de configuration de l’oracle (passé à `oracle.py --config`).
- `--response-mapping` : chemin vers le JSON de mapping de réponses.

Exécution (depuis la racine du dépôt) :

```bash
python3 Code/EmotionConfigurable/EmotionConfigurable.py \
  --oracle-config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json \
  --response-mapping Emotion/EmotionProjetBase/response_mapping_emotiondamage.json
```

Ensuite, saisissez du texte après le prompt `Vous:`.

### Flux d’exécution (résumé)
1. Chargement et validation du mapping de réponses (`--response-mapping`).
2. Création du client oracle avec `--oracle-config`.
   - Le script oracle appelé est résolu automatiquement comme `Code/oracle.py` (chemin relatif au fichier EmotionConfigurable).
   - Un appel de validation est effectué (`infer("")`) pour vérifier que l’oracle s’exécute et renvoie un JSON conforme.
3. Boucle interactive :
   - lecture d’une ligne utilisateur
   - appel de l’oracle : `python Code/oracle.py --config <oracle-config> --text <user_text>`
   - parsing du JSON renvoyé, extraction de `result.primary_emotion_id` et `result.overall_confidence`
   - conversion de la confiance en niveau (`low` / `medium` / `high`) via `confidence_thresholds`
   - sélection de la réponse dans `responses[emotion_id][confidence_level]` (avec fallback sur `defaults`)
   - affichage de la réponse sur stdout

### Entrées / sorties / codes de retour
- Entrée : saisie utilisateur interactive via `input()`.
- Sortie : réponses affichées sur stdout.
- Erreurs : messages sur stderr.
- Codes de retour observables :
  - `0` : arrêt normal (EOF / Ctrl+C).
  - `2` : erreur de configuration (mapping/oracle) ou échec d’appel oracle en cours de dialogue.

## Configuration
### 1) Configuration de l’oracle (`--oracle-config`)
Un exemple est fourni :
- [Emotion/EmotionProjetBase/oracle_config_emotiondamage.json](../../Emotion/EmotionProjetBase/oracle_config_emotiondamage.json)

Ce fichier est consommé par [Code/oracle.py](../../Code/oracle.py) et définit notamment :
- la liste des émotions (id/label/aliases/keywords/negations/weight)
- la calibration de la confiance (base, incréments par match, pénalités, etc.)

### 2) Mapping de réponses (`--response-mapping`)
Un exemple est fourni :
- [Emotion/EmotionProjetBase/response_mapping_emotiondamage.json](../../Emotion/EmotionProjetBase/response_mapping_emotiondamage.json)

Schéma attendu (champs importants) :

| Champ | Type | Contraintes / rôle |
|------|------|---------------------|
| schema_version | string | Obligatoire, non vide. |
| confidence_levels | array<string> | Doit contenir exactement : `low`, `medium`, `high` (uniques). |
| confidence_thresholds.low_lt | number | Seuil : si confidence < low_lt → `low`. |
| confidence_thresholds.medium_lt | number | Seuil : si confidence < medium_lt → `medium`, sinon `high`. Doit vérifier `low_lt < medium_lt`. |
| responses | object | Dictionnaire `emotion_id -> {low,medium,high}`. |
| responses.<emotion_id>.<level> | string | Tous les niveaux doivent être présents et non vides. |
| defaults.emotion_id | string | Doit exister dans `responses`. |
| defaults.confidence_level | string | Doit être dans `confidence_levels`. |
| defaults.empty_input_response | string | Réponse si l’utilisateur saisit une ligne vide. |

Erreurs de validation typiques (déduites du code) :
- JSON invalide (syntaxe) → erreur explicite.
- champs manquants / types incorrects (ex. `confidence_levels` non liste) → erreur explicite.
- `confidence_levels` différent de `low/medium/high` → rejet.
- seuils incohérents (`low_lt >= medium_lt`) → rejet.
- réponse manquante pour un niveau dans `responses` → rejet.

## Structure du projet
- [Code/EmotionConfigurable/EmotionConfigurable.py](../../Code/EmotionConfigurable/EmotionConfigurable.py) : **script principal** (boucle interactive, appel oracle, sélection de réponse).
- [Code/oracle.py](../../Code/oracle.py) : oracle heuristique exécuté via subprocess (retour JSON).
- [Emotion/EmotionProjetBase/oracle_config_emotiondamage.json](../../Emotion/EmotionProjetBase/oracle_config_emotiondamage.json) : exemple de config oracle.
- [Emotion/EmotionProjetBase/response_mapping_emotiondamage.json](../../Emotion/EmotionProjetBase/response_mapping_emotiondamage.json) : exemple de mapping de réponses.
- [documentation/](../) : documents de projet (phases, résumés).
- [test/](../../test/) : scripts/fichiers de tests liés à un autre composant (`EmotionDamage.py`) ; ils ne testent pas directement `EmotionConfigurable`.

## Exemples d’utilisation
### 1) Démarrage depuis la racine (configs fournies)
```bash
python3 Code/EmotionConfigurable/EmotionConfigurable.py \
  --oracle-config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json \
  --response-mapping Emotion/EmotionProjetBase/response_mapping_emotiondamage.json
```

### 2) Exemple d’échange (interaction manuelle)
```text
Vous: I feel really anxious today
I'm here to support you. Is there anything I can do to help?
```
(Remarque : le texte exact dépend du mapping et du niveau de confiance.)

### 3) Erreur fréquente : mapping introuvable
```bash
python3 Code/EmotionConfigurable/EmotionConfigurable.py \
  --oracle-config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json \
  --response-mapping does/not/exist.json
```
Attendu : message sur stderr du type `Erreur de configuration mapping: ...` et code retour `2`.

### 4) Erreur fréquente : oracle_config introuvable / oracle échoue
```bash
python3 Code/EmotionConfigurable/EmotionConfigurable.py \
  --oracle-config does/not/exist.json \
  --response-mapping Emotion/EmotionProjetBase/response_mapping_emotiondamage.json
```
Attendu : message sur stderr du type `Erreur de configuration oracle: ...` et code retour `2`.

## Dépannage
- **“Oracle output is not valid JSON …”** : l’oracle appelé n’a pas produit un JSON valide (ou un autre programme a été exécuté). Vérifier que [Code/oracle.py](../../Code/oracle.py) est présent et exécutable avec la config.
- **“Oracle failed …” / message d’erreur de l’oracle** : exécuter directement l’oracle pour diagnostiquer :
  ```bash
  python3 Code/oracle.py --config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json --text "test"
  ```
- **Aucune réponse pertinente** : vérifier que l’émotion primaire renvoyée par l’oracle existe dans `responses` (ou configurer `defaults.emotion_id` correctement).

## Contribuer
Issues et pull requests sont bienvenues (en particulier : nouveaux mappings, nouvelles configs oracle, ou ajustement des seuils).