# Oracle d’émotions heuristique (oracle.py)

## Description
Ce dépôt contient un petit « oracle » d’émotions basé sur des heuristiques (mots-clés / alias) et entièrement configurable via JSON.
Le cœur de l’outil est [Code/oracle.py](../../Code/oracle.py) : il lit une configuration, analyse un texte en entrée, puis produit une sortie JSON structurée décrivant l’émotion principale détectée, une liste d’émotions candidates, et un score de confiance.

L’oracle n’utilise pas de modèle ML : il repose sur la présence de termes (mots-clés, alias) et applique des pénalités simples (ambiguïté, négation).
Il peut être utilisé seul en ligne de commande (argument texte ou STDIN), ou intégré dans une boucle de dialogue via [Code/EmotionConfigurable/EmotionConfigurable.py](../../Code/EmotionConfigurable/EmotionConfigurable.py) (oracle + mapping de réponses).

## Fonctionnalités principales
- Inférence d’émotions à partir d’un texte, via un score heuristique configurable.
- Configuration JSON des émotions (id, label, alias, mots-clés, négations, poids).
- Calibration de la confiance (base, incréments par match, pénalités, limite du nombre d’émotions retournées).
- Détection naïve de négations (pénalise la confiance si un marqueur de négation est détecté).
- Gestion de l’ambiguïté (pénalise si plusieurs émotions ont une confiance > min).
- Entrée via argument CLI (--text) ou via STDIN (si --text est omis).
- Sortie JSON lisible (indentation) sur stdout et codes de retour explicites (0 succès, 2 erreur de configuration).

## Technologies utilisées
- Python 3.10+ (utilisation des unions de types avec l’opérateur | et de dataclasses).
- Bibliothèque standard uniquement (argparse, json, re, dataclasses, datetime, pathlib/subprocess côté intégration).
- Formats : JSON (config oracle, mappings), Markdown (documentation).

## Installation
### Prérequis
- Python 3.10 ou plus récent.

### Mise en place (sans dépendances externes)
Depuis la racine du dépôt :

    python3 -m venv .venv
    . .venv/bin/activate

Aucun fichier requirements.txt n’est présent : l’oracle s’exécute avec la bibliothèque standard.

## Utilisation
### Lancer l’oracle
L’interface CLI est définie dans [Code/oracle.py](../../Code/oracle.py).

Arguments observables :
- --config (obligatoire) : chemin vers un fichier JSON de configuration.
- --text (optionnel) : texte à analyser. Si absent, le texte est lu depuis STDIN (sys.stdin.read()).
- --seed (optionnel) : accepté « pour compatibilité », mais n’a pas d’effet (valeur ignorée).

Exécution (texte fourni via argument) :

    python3 Code/oracle.py --config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json --text "I feel really anxious today"

Exécution (texte fourni via STDIN) :

    echo "I feel really anxious today" | python3 Code/oracle.py --config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json

### Sortie (stdout)
L’oracle imprime un JSON (indenté) avec la structure suivante :
- input.text : texte d’entrée original.
- input.normalized_text : texte normalisé (lowercase + espaces normalisés).
- result.emotions : liste triée d’émotions candidates, chacune avec id, label, confidence et un bloc evidence.
- result.primary_emotion_id : l’émotion principale (premier élément de result.emotions).
- result.overall_confidence : maximum des confiances des émotions retournées (borné min/max).
- result.notes : notes heuristiques, par ex. empty_input, no_emotion_detected, ambiguous_emotions, negation_detected.
- meta : informations (schema_version, config_path, timestamp_utc, engine).

Codes de retour :
- 0 : succès.
- 2 : erreur de configuration (fichier introuvable, JSON invalide, champs manquants, etc.).

### Configuration
Deux configurations d’exemple sont présentes dans le dépôt :
- Config « émotion » (anglais) : [Emotion/EmotionProjetBase/oracle_config_emotiondamage.json](../../Emotion/EmotionProjetBase/oracle_config_emotiondamage.json)
- Config « émotion » (français) : [Previous/example_oracle_config.json](../../Previous/example_oracle_config.json)

Schéma (champs utilisés par l’oracle) :

| Champ | Type | Rôle |
|------|------|------|
| schema_version | string | Version de schéma (métadonnée reportée en sortie). |
| emotions | array<object> | Liste non vide d’émotions configurées. |
| emotions[].id | string | Identifiant stable de l’émotion (ex. joy, fear). |
| emotions[].label | string | Label lisible (facultatif, défaut = id). |
| emotions[].aliases | array<string> | Synonymes / expressions alternatives. |
| emotions[].keywords | array<string> | Mots-clés déclencheurs. |
| emotions[].negations | array<string> | Marqueurs de négation (pénalise si détectés). |
| emotions[].weight | number | Poids multiplicatif du score pour l’émotion. |
| confidence.scale | string | Étiquette de l’échelle (métadonnée). |
| confidence.min / confidence.max | number | Bornes de la confiance (clamp). |
| confidence.calibration | object | Paramètres de score (base, incréments, pénalités). |
| confidence.calibration.intensifiers | array<string> | Termes renforçateurs (optionnels) qui augmentent le score. |
| confidence.calibration.max_emotions | int | Nombre maximum d’émotions retournées. |
| behavior.allow_multiple_emotions | bool | Si false, ne retourne que l’émotion la mieux classée. |
| behavior.unknown_emotion_id | string | Identifiant de repli si rien n’est détecté. |

Remarque : behavior.language_hint est chargé depuis JSON mais n’est pas exploité par l’algorithme.

## Structure du projet
- [Code/oracle.py](../../Code/oracle.py) : oracle heuristique (chargement config, normalisation, scoring, sortie JSON).
- [Code/EmotionConfigurable/EmotionConfigurable.py](../../Code/EmotionConfigurable/EmotionConfigurable.py) : intégration « oracle + mapping de réponses » dans une boucle interactive (subprocess).
- [Emotion/EmotionProjetBase/oracle_config_emotiondamage.json](../../Emotion/EmotionProjetBase/oracle_config_emotiondamage.json) : configuration oracle (anglais).
- [Emotion/EmotionProjetBase/response_mapping_emotiondamage.json](../../Emotion/EmotionProjetBase/response_mapping_emotiondamage.json) : mapping réponses selon émotion + niveau de confiance (utilisé par EmotionConfigurable).
- [Previous/example_oracle_config.json](../../Previous/example_oracle_config.json) : configuration oracle alternative (français).
- [test/run_tests.py](../../test/run_tests.py) et fichiers .jsonl dans test/ : scripts et jeux de tests liés à EmotionDamage (pas directement à oracle.py ; certains appels sont PowerShell).
- documentation/ : notes et résumés de phases (hors oracle).

## Exemples d’utilisation
### 1) Cas minimum (texte + config)

    python3 Code/oracle.py --config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json --text "I am happy"

### 2) Cas avec configuration française

    python3 Code/oracle.py --config Previous/example_oracle_config.json --text "Merci pour ton aide, mais je suis un peu stressé"

### 3) Lecture depuis STDIN (utile en pipeline)

    echo "I feel anxious and under pressure" | python3 Code/oracle.py --config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json

### 4) Exemple « validation / erreur fréquente » : chemin de config invalide

    python3 Code/oracle.py --config does/not/exist.json --text "test"

Attendu : message d’erreur sur stderr du type "Configuration error: Config file not found: ..." et code de retour 2.

## Dépannage (si besoin)
- Erreur JSON invalide : vérifier que la config est un objet JSON valide (guillemets, virgules, etc.).
- Aucune émotion détectée : l’oracle renvoie unknown_emotion_id et ajoute la note no_emotion_detected. Ajouter des keywords/aliases dans la config.
- Négations : si une négation de emotions[].negations est détectée, une pénalité negation_penalty est appliquée.

## Contribuer
Issues et pull requests sont bienvenues. Pour rester cohérent avec le dépôt, privilégier des changements localisés (configs JSON, heuristiques) et ajouter un exemple reproductible.
