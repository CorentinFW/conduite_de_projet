# Prompt — EmotionConfigurable (oracle + mapping)

## Rôle
Tu es un·e ingénieur·e logiciel Python senior et prompt engineer. Produis du code Python propre, modulaire, testable, et robuste. Respecte strictement les bonnes pratiques (SRP, typage, gestion d’erreurs, séparation config/logique/IO) et reste minimal (pas de fonctionnalités “nice to have”).

## Contexte
Tu travailles dans un dépôt dont la racine contient notamment :
- [Code/oracle.py](Code/oracle.py) : un « oracle » d’émotions configurable via JSON. Exécution actuelle : `python3 Code/oracle.py --config example_oracle_config.json --text "..."`.
- [example_oracle_config.json](example_oracle_config.json) : exemple de configuration de l’oracle.
- [Code/EmotionDamage.py](Code/EmotionDamage.py) : exemple d’architecture modulaire de mapping émotion + confiance → action/message.

L’oracle renvoie (sur stdout) un JSON indenté avec ce schéma (extrait utile) :
- `result.emotions`: liste d’objets `{ id, label, confidence (float), evidence }`
- `result.primary_emotion_id`: l’émotion principale (`str`)
- `result.overall_confidence`: confiance globale (`float`)

Objectif global : construire un programme qui fait une boucle infinie de dialogue et qui, à chaque message utilisateur, appelle l’oracle pour obtenir **émotion(s) + confiance**, puis applique un **mapping externe** (émotion + niveau de confiance → texte) pour afficher une réponse.

## Objectif
Créer un code Python dans le dossier [Code/EmotionConfigurable/](Code/EmotionConfigurable/) qui :
1) Charge un mapping « émotion + niveau de confiance → réponse » depuis un fichier externe (JSON).
2) Charge une configuration d’oracle (JSON) qui définit les émotions et leur calibration (même format que [example_oracle_config.json](example_oracle_config.json)).
3) Lance une boucle de dialogue infinie :
   - lit le texte utilisateur,
   - appelle l’oracle avec la configuration fournie,
   - récupère l’émotion principale et sa confiance,
   - transforme la confiance float en **niveau discret** (ex: `low/medium/high`) via des seuils configurables,
   - choisit la réponse selon le mapping,
   - affiche la réponse et recommence.

## Contraintes (à respecter)
### Contraintes de portée
- N’ajoute pas de pages, UI, modes avancés, logs décoratifs, ni fonctionnalités non demandées.
- N’ajoute pas de dépendances externes (standard library uniquement).
- N’altère pas [Code/oracle.py](Code/oracle.py) et n’altère pas sa sortie.

### Contraintes d’architecture
- Le code doit être **modulaire** (pas un gros `main` monolithique).
- Sépare clairement :
  - chargement/validation des configs,
  - client oracle (appel + parsing),
  - binning de confiance (float → niveau),
  - sélection de réponse (mapping),
  - boucle d’IO (interaction utilisateur).
- Utilise des `dataclasses` et du typage (`typing`) pour une structure de données générique et maintenable.

### Robustesse / cas ambigus
- Si l’oracle renvoie une émotion inconnue du mapping : utiliser une réponse par défaut.
- Si le niveau de confiance calculé n’existe pas dans le mapping pour cette émotion : fallback vers une règle par défaut.
- Si l’entrée utilisateur est vide : demander une reformulation (réponse par défaut).
- Si la config JSON est invalide : message d’erreur clair sur stderr et code de sortie non-zéro.
- La boucle doit se terminer proprement sur `Ctrl+C` ou EOF.

## Hypothèses
- Le programme est exécuté depuis la racine du dépôt.
- La configuration de l’oracle est fournie par chemin de fichier.
- Le mapping de réponses est fourni par chemin de fichier.

## Données : format du mapping externe (à implémenter)
Crée un format JSON simple, versionné et validable. Il doit contenir :
- `schema_version` (string)
- `confidence_levels` (liste de labels, ex. `["low","medium","high"]`)
- `confidence_thresholds` (objet décrivant comment transformer une confiance float en label)
- `responses` (mapping `emotion_id -> confidence_label -> response_text`)
- `defaults` (fallbacks)

Spécification stricte recommandée (tu peux reprendre tel quel) :
```json
{
  "schema_version": "1.0",
  "confidence_levels": ["low", "medium", "high"],
  "confidence_thresholds": {
    "low_lt": 0.40,
    "medium_lt": 0.70
  },
  "responses": {
    "joy": {
      "low": "Je crois percevoir de la joie, tu peux m'en dire plus ?",
      "medium": "Ça fait plaisir à entendre.",
      "high": "Génial ! Je suis content pour toi."
    },
    "sadness": {
      "low": "Je ne suis pas sûr de bien comprendre, tu veux préciser ?",
      "medium": "Je suis là. Qu'est-ce qui te pèse ?",
      "high": "Je suis désolé que tu traverses ça. Je suis là pour t'écouter."
    },
    "unknown": {
      "low": "Peux-tu préciser ce que tu ressens ?",
      "medium": "Peux-tu préciser ce que tu ressens ?",
      "high": "Peux-tu préciser ce que tu ressens ?"
    }
  },
  "defaults": {
    "emotion_id": "unknown",
    "confidence_level": "medium",
    "empty_input_response": "Je n'ai pas reçu de texte. Peux-tu reformuler ?"
  }
}
```

Règle de binning à implémenter à partir de `confidence_thresholds` :
- si `confidence < low_lt` → `low`
- sinon si `confidence < medium_lt` → `medium`
- sinon → `high`

## Structure de données générique (à concevoir)
Tu dois proposer une structure simple et réutilisable pour représenter :
- une prédiction émotionnelle (id, label optionnel, confiance float),
- un résultat d’inférence (émotion principale, liste d’émotions, confiance globale),
- une règle de réponse (emotion_id + confidence_level → response_text),
- les seuils de binning.

Utilise des `@dataclass(frozen=True)` quand c’est pertinent.

## Étapes à suivre (processus de réalisation)
1) Définis les dataclasses de schéma (prédiction, résultat, mapping, seuils).
2) Implémente un loader/validator JSON pour le mapping de réponses.
3) Implémente un client oracle :
   - approche attendue : exécuter [Code/oracle.py](Code/oracle.py) via `subprocess.run` (portable) avec `--config` et `--text`,
   - parser le JSON retourné,
   - convertir le dictionnaire en dataclasses.
4) Implémente le binner de confiance (float → label).
5) Implémente le moteur de sélection de réponse (règles + fallbacks).
6) Implémente la boucle interactive : `input()` → oracle → réponse → `print()`.

## Interface CLI (à fournir)
Le programme principal doit accepter au minimum :
- `--oracle-config <path>` : chemin vers la config oracle JSON (ex. [example_oracle_config.json](example_oracle_config.json))
- `--response-mapping <path>` : chemin vers le mapping JSON décrit plus haut

Exemple d’exécution attendu (depuis la racine) :
- `python3 Code/EmotionConfigurable/EmotionConfigurable.py --oracle-config example_oracle_config.json --response-mapping response_mapping.json`

## Format de sortie attendu (ce que tu dois produire)
Tu dois répondre en listant exactement les fichiers à créer (et uniquement ceux nécessaires), avec leur contenu complet.

Fichiers attendus :
1) [Code/EmotionConfigurable/EmotionConfigurable.py](Code/EmotionConfigurable/EmotionConfigurable.py)
2) [Code/EmotionConfigurable/__init__.py](Code/EmotionConfigurable/__init__.py)
3) Un exemple de mapping (choisis un nom) au format JSON, placé à la racine du dépôt OU dans [Code/EmotionConfigurable/](Code/EmotionConfigurable/)

Contraintes de rendu :
- Utilise des blocs de code Markdown avec le bon langage (`python` / `json`).
- N’écris aucune explication longue, pas d’analyse : uniquement les fichiers et leur contenu.
- Le code doit être exécutable tel quel sous Linux avec Python 3.
