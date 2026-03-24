===============================================================================
EMOTION-REACTION DIALOGUE ENGINE / MOTEUR DE DIALOGUE ÉMOTION-RÉACTION
===============================================================================

Week 2 - Multi-turn Dialogue with State Management
Semaine 2 - Dialogue Multi-tours avec Gestion d'État

===============================================================================
INSTALLATION / INSTALLATION
===============================================================================

Prérequis / Prerequisites:
- Python 3.5+ (with typing support / avec support du typage)

Aucune dépendance externe requise.
No external dependencies required.

===============================================================================
UTILISATION / USAGE
===============================================================================

MODE STANDARD (STDIN - Recommandé / Recommended):
-------------------------------------------------

1. Avec fichier JSON Lines / With JSON Lines file:
   
   Windows PowerShell:
   Get-Content input.jsonl | python EmotionDamage.py
   
   Linux/Mac:
   python EmotionDamage.py < input.jsonl
   cat input.jsonl | python EmotionDamage.py

2. Entrée interactive / Interactive input:
   
   python EmotionDamage.py
   (Tapez chaque ligne JSON et appuyez sur Entrée)
   (Type each JSON line and press Enter)
   (Ctrl+C pour quitter / to quit)

MODE LEGACY (FICHIER - Rétrocompatibilité / Backward Compatibility):
--------------------------------------------------------------------

python EmotionDamage.py <fichier.json>

Exemple / Example:
python EmotionDamage.py test.json
python EmotionDamage.py case.json

===============================================================================
FORMAT D'ENTRÉE / INPUT FORMAT
===============================================================================

Chaque ligne doit être un objet JSON avec les champs suivants:
Each line must be a JSON object with the following fields:

{
  "user_text": "I failed again.",
  "emotion": "sadness",
  "confidence": "high"
}

CHAMPS OBLIGATOIRES / REQUIRED FIELDS:
- user_text (string): Le texte de l'utilisateur / The user's text
- emotion (string): Une des émotions valides / One of the valid emotions
- confidence (string): Un des niveaux de confiance / One of the confidence levels

ÉMOTIONS VALIDES / VALID EMOTIONS:
- joy (joie)
- sadness (tristesse)
- anger (colère)
- fear (peur)
- disgust (dégoût)
- surprise (surprise)

NIVEAUX DE CONFIANCE / CONFIDENCE LEVELS:
- low (bas)
- medium (moyen)
- high (élevé)

===============================================================================
FORMAT DE SORTIE / OUTPUT FORMAT
===============================================================================

Chaque sortie est un objet JSON avec:
Each output is a JSON object with:

{
  "action": "offer_support",
  "message": "I'm here to support you. Is there anything I can do to help?",
  "next_state": "SUPPORT"
}

CHAMPS / FIELDS:
- action (string): L'action à effectuer / The action to take
- message (string): Le message de réponse / The response message
- next_state (string): Le prochain état du dialogue / The next dialogue state

ACTIONS POSSIBLES / POSSIBLE ACTIONS:
- continue: Continuer la conversation / Continue the conversation
- slow_down: Ralentir, prendre un moment / Slow down, take a moment
- ask_clarification: Demander clarification / Ask for clarification
- offer_support: Offrir du support / Offer support
- de_escalate: Désescalader la tension / De-escalate the tension
- suggest_pause: Suggérer une pause / Suggest a pause

ÉTATS DU DIALOGUE / DIALOGUE STATES:
- START: État initial / Initial state
- SUPPORT: Mode support / Support mode
- DEESCALATE: Mode désescalade / De-escalation mode
- END: Dialogue terminé / Dialogue ended

===============================================================================
MACHINE À ÉTATS / STATE MACHINE
===============================================================================

Règles de transition / Transition rules:

START ──[offer_support]──> SUPPORT
SUPPORT ──[de_escalate]──> DEESCALATE
DEESCALATE ──[suggest_pause]──> END
END ──[any action]──> END (persiste / persists)

Toute autre action préserve l'état actuel.
Any other action preserves the current state.

===============================================================================
EXEMPLES / EXAMPLES
===============================================================================

EXEMPLE 1: Fichier JSON Lines / JSON Lines File
-----------------------------------------------

Fichier input.jsonl:
{"user_text":"I failed again.","emotion":"sadness","confidence":"high"}
{"user_text":"Whatever.","emotion":"anger","confidence":"medium"}

Commande:
Get-Content input.jsonl | python EmotionDamage.py

Sortie:
{"action": "offer_support", "message": "I'm here to support you. Is there anything I can do to help?", "next_state": "SUPPORT"}
{"action": "slow_down", "message": "I sense that you might be feeling overwhelmed. Let's take a moment to pause.", "next_state": "SUPPORT"}


EXEMPLE 2: Mode Legacy (Fichier JSON) / Legacy Mode (JSON File)
---------------------------------------------------------------

Fichier test.json:
{ "emotion" : "disgust", "confidence": "high" }

Commande:
python EmotionDamage.py test.json

Sortie:
{"action": "de_escalate", "message": "Let's pause and try to calm down, lower the tension.", "next_state": "DEESCALATE"}


EXEMPLE 3: Entrée Interactive / Interactive Input
-------------------------------------------------

Commande:
python EmotionDamage.py

Entrée (tapez ligne par ligne):
{"user_text":"I'm happy!","emotion":"joy","confidence":"high"}
{"user_text":"I'm sad","emotion":"sadness","confidence":"high"}

Sortie:
{"action": "continue", "message": "Thank you for sharing. Let's continue our conversation.", "next_state": "START"}
{"action": "offer_support", "message": "I'm here to support you. Is there anything I can do to help?", "next_state": "SUPPORT"}

(Ctrl+C pour quitter / to quit)

===============================================================================
FICHIERS DE TEST INCLUS / INCLUDED TEST FILES
===============================================================================

- test.json: Test simple avec une entrée (legacy mode)
- case.json: Test avec plusieurs entrées (legacy mode)
- test_invalid.json: Test avec entrées invalides
- test_stdin.jsonl: Test basique STDIN (4 entrées)
- test_states.jsonl: Test des transitions d'état (5 entrées)
- test_end_state.jsonl: Test de la persistance de l'état END (3 entrées)

===============================================================================
GESTION D'ERREURS / ERROR HANDLING
===============================================================================

En cas d'entrée invalide (émotion inconnue, confiance inconnue, JSON invalide):
In case of invalid input (unknown emotion, unknown confidence, invalid JSON):

Sortie:
{"action": "ask_clarification", "message": "Could you please clarify how you're feeling?", "next_state": "<current_state>"}

===============================================================================
ARCHITECTURE DU CODE / CODE ARCHITECTURE
===============================================================================

Classes principales / Main classes:
- EmotionReactionEngine: Logique de mapping émotion→action
- DialogueStateManager: Gestion de la machine à états
- MessageValidator: Validation des contraintes de messages
- DialogueProcessor: Orchestration principale

Voir Etape1.md et Etape2.md pour documentation détaillée.
See Etape1.md and Etape2.md for detailed documentation.

===============================================================================
AUTEUR / AUTHOR
===============================================================================

Week 2 Practical Session - AI Dialogue Extension
Conduite de Projet - Master 1

===============================================================================
