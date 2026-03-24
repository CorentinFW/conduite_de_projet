#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emotion-Reaction Dialogue Engine
Moteur de Dialogue Émotion-Réaction

Week 2 - Multi-turn dialogue with state management
Semaine 2 - Dialogue multi-tours avec gestion d'état

This module implements an emotion-based reaction system that maps emotions
and confidence levels to appropriate actions and messages.
Ce module implémente un système de réaction basé sur les émotions qui associe
les émotions et niveaux de confiance à des actions et messages appropriés.
"""

from json import loads, dumps
from sys import argv
from typing import Dict, Optional, Tuple
from enum import Enum


# ============================================================================
# CONSTANTS AND ENUMERATIONS / CONSTANTES ET ÉNUMÉRATIONS
# ============================================================================

class Emotion(str, Enum):
    """
    Valid emotion types / Types d'émotions valides
    """
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    DISGUST = "disgust"
    SURPRISE = "surprise"


class ConfidenceLevel(str, Enum):
    """
    Valid confidence levels / Niveaux de confiance valides
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Action(str, Enum):
    """
    Valid action responses / Actions de réponse valides
    """
    CONTINUE = "continue"
    SLOW_DOWN = "slow_down"
    ASK_CLARIFICATION = "ask_clarification"
    OFFER_SUPPORT = "offer_support"
    DE_ESCALATE = "de_escalate"
    SUGGEST_PAUSE = "suggest_pause"


class DialogueState(str, Enum):
    """
    Dialogue state values / Valeurs d'état du dialogue
    """
    START = "START"
    SUPPORT = "SUPPORT"
    DEESCALATE = "DEESCALATE"
    END = "END"


# Predefined reaction messages / Messages de réaction prédéfinis
REACTION_MESSAGES: Dict[str, str] = {
    "ask_clarification": "Could you please clarify how you're feeling?",
    "offer_support": "I'm here to support you. Is there anything I can do to help?",
    "continue": "Thank you for sharing. Let's continue our conversation.",
    "slow_down": "I sense that you might be feeling overwhelmed. Let's take a moment to pause.",
    "de_escalate": "Let's pause and try to calm down, lower the tension.",
    "suggest_pause": "Perhaps we should take a break now.",
}

# Emotion-confidence mapping to actions / Mapping émotion-confiance vers actions
EMOTION_ACTION_RULES: Dict[str, Dict[str, str]] = {
    "joy": {
        "low": "ask_clarification",
        "medium": "continue",
        "high": "continue"
    },
    "sadness": {
        "low": "ask_clarification",
        "medium": "offer_support",
        "high": "offer_support"
    },
    "anger": {
        "low": "ask_clarification",
        "medium": "slow_down",
        "high": "de_escalate"
    },
    "fear": {
        "low": "ask_clarification",
        "medium": "slow_down",
        "high": "offer_support"
    },
    "disgust": {
        "low": "ask_clarification",
        "medium": "slow_down",
        "high": "de_escalate"
    },
    "surprise": {
        "low": "ask_clarification",
        "medium": "continue",
        "high": "continue"
    }
}


# ============================================================================
# EMOTION REACTION ENGINE / MOTEUR DE RÉACTION AUX ÉMOTIONS
# ============================================================================

class EmotionReactionEngine:
    """
    Maps emotions and confidence levels to appropriate actions and messages.
    Associe les émotions et niveaux de confiance aux actions et messages appropriés.
    
    This class encapsulates the core logic of emotion-to-action mapping.
    Cette classe encapsule la logique principale de l'association émotion-action.
    """
    
    def __init__(
        self, 
        action_rules: Dict[str, Dict[str, str]], 
        messages: Dict[str, str]
    ):
        """
        Initialize the emotion reaction engine.
        Initialise le moteur de réaction aux émotions.
        
        Args:
            action_rules: Mapping of emotion->confidence->action
                         Association émotion->confiance->action
            messages: Predefined messages for each action
                     Messages prédéfinis pour chaque action
        """
        self.action_rules = action_rules
        self.messages = messages
    
    def react(self, emotion: str, confidence: str) -> Tuple[str, str]:
        """
        Determine the appropriate action and message for given emotion and confidence.
        Détermine l'action et le message appropriés pour l'émotion et la confiance données.
        
        Args:
            emotion: The detected emotion (e.g., "joy", "sadness")
                    L'émotion détectée (ex: "joy", "sadness")
            confidence: The confidence level ("low", "medium", "high")
                       Le niveau de confiance ("low", "medium", "high")
        
        Returns:
            Tuple of (action, message)
            Tuple (action, message)
        
        Examples:
            >>> engine = EmotionReactionEngine(EMOTION_ACTION_RULES, REACTION_MESSAGES)
            >>> action, msg = engine.react("sadness", "high")
            >>> action
            'offer_support'
        """
        # Validate emotion / Valider l'émotion
        if emotion not in self.action_rules:
            return (
                Action.ASK_CLARIFICATION.value,
                self.messages[Action.ASK_CLARIFICATION.value]
            )
        
        # Get confidence mapping for this emotion / Obtenir le mapping de confiance pour cette émotion
        confidence_mapping = self.action_rules[emotion]
        
        # Validate confidence level / Valider le niveau de confiance
        if confidence not in confidence_mapping:
            return (
                Action.ASK_CLARIFICATION.value,
                self.messages[Action.ASK_CLARIFICATION.value]
            )
        
        # Get the action / Obtenir l'action
        action = confidence_mapping[confidence]
        message = self.messages[action]
        
        return (action, message)


# ============================================================================
# DIALOGUE STATE MANAGER / GESTIONNAIRE D'ÉTAT DU DIALOGUE
# ============================================================================

class DialogueStateManager:
    """
    Manages the dialogue state transitions.
    Gère les transitions d'état du dialogue.
    
    The state machine tracks the current dialogue state and updates it
    based on the actions taken.
    La machine à états suit l'état actuel du dialogue et le met à jour
    en fonction des actions effectuées.
    """
    
    def __init__(self):
        """
        Initialize with START state.
        Initialiser avec l'état START.
        """
        self.current_state: str = DialogueState.START.value
    
    def update_state(self, action: str) -> str:
        """
        Update the dialogue state based on the action taken.
        Met à jour l'état du dialogue en fonction de l'action effectuée.
        
        State transition rules / Règles de transition d'état:
        - offer_support → SUPPORT
        - de_escalate → DEESCALATE
        - suggest_pause → END
        - If current state is END, it stays END
          Si l'état actuel est END, il reste END
        
        Args:
            action: The action that was taken
                   L'action qui a été effectuée
        
        Returns:
            The new dialogue state
            Le nouvel état du dialogue
        """
        # Once in END state, stay there / Une fois dans l'état END, y rester
        if self.current_state == DialogueState.END.value:
            return self.current_state
        
        # Update state based on action / Mettre à jour l'état selon l'action
        if action == Action.OFFER_SUPPORT.value:
            self.current_state = DialogueState.SUPPORT.value
        elif action == Action.DE_ESCALATE.value:
            self.current_state = DialogueState.DEESCALATE.value
        elif action == Action.SUGGEST_PAUSE.value:
            self.current_state = DialogueState.END.value
        # Otherwise state remains unchanged / Sinon l'état reste inchangé
        
        return self.current_state


# ============================================================================
# MESSAGE VALIDATOR / VALIDATEUR DE MESSAGES
# ============================================================================

class MessageValidator:
    """
    Validates that messages meet the requirements for each state.
    Valide que les messages respectent les exigences pour chaque état.
    
    State-specific message requirements / Exigences de messages spécifiques à l'état:
    - SUPPORT: must contain "help", "support", or "here"
              doit contenir "help", "support", ou "here"
    - DEESCALATE: must contain "calm", "pause", or "slow"
                  doit contenir "calm", "pause", ou "slow"
    """
    
    @staticmethod
    def validate(message: str, state: str) -> bool:
        """
        Check if a message meets the requirements for a given state.
        Vérifie si un message respecte les exigences pour un état donné.
        
        Args:
            message: The message to validate / Le message à valider
            state: The dialogue state / L'état du dialogue
        
        Returns:
            True if valid, False otherwise / True si valide, False sinon
        """
        message_lower = message.lower()
        
        if state == DialogueState.SUPPORT.value:
            # Must contain at least one of these words / Doit contenir au moins un de ces mots
            return any(word in message_lower for word in ["help", "support", "here"])
        
        elif state == DialogueState.DEESCALATE.value:
            # Must contain at least one of these words / Doit contenir au moins un de ces mots
            return any(word in message_lower for word in ["calm", "pause", "slow"])
        
        # No validation required for other states / Pas de validation requise pour les autres états
        return True


# ============================================================================
# DIALOGUE PROCESSOR / PROCESSEUR DE DIALOGUE
# ============================================================================

class DialogueProcessor:
    """
    Main orchestrator for processing dialogue interactions.
    Orchestrateur principal pour le traitement des interactions de dialogue.
    
    This class coordinates the emotion engine, state manager, and message validator
    to process dialogue inputs and generate appropriate responses.
    Cette classe coordonne le moteur d'émotions, le gestionnaire d'état et le validateur
    de messages pour traiter les entrées de dialogue et générer des réponses appropriées.
    """
    
    def __init__(self):
        """
        Initialize the dialogue processor with all necessary components.
        Initialise le processeur de dialogue avec tous les composants nécessaires.
        """
        self.emotion_engine = EmotionReactionEngine(
            EMOTION_ACTION_RULES,
            REACTION_MESSAGES
        )
        self.state_manager = DialogueStateManager()
        self.message_validator = MessageValidator()
    
    def process_input(self, emotion_data: Dict[str, str]) -> Dict[str, str]:
        """
        Process a single emotion input and return the reaction.
        Traite une seule entrée d'émotion et retourne la réaction.
        
        Args:
            emotion_data: Dictionary with "user_text", "emotion" and "confidence" keys
                         Dictionnaire avec les clés "user_text", "emotion" et "confidence"
        
        Returns:
            Dictionary with "action", "message", and "next_state" keys
            Dictionnaire avec les clés "action", "message" et "next_state"
        """
        # Extract user_text (for future use), emotion and confidence
        # Extraire user_text (pour usage futur), émotion et confiance
        user_text = emotion_data.get("user_text", "")
        emotion = emotion_data.get("emotion", "")
        confidence = emotion_data.get("confidence", "")
        
        # Get the appropriate action and message / Obtenir l'action et le message appropriés
        action, message = self.emotion_engine.react(emotion, confidence)
        
        # Update dialogue state based on action / Mettre à jour l'état du dialogue selon l'action
        next_state = self.state_manager.update_state(action)
        
        # Validate message meets state requirements / Valider que le message respecte les exigences d'état
        if not self.message_validator.validate(message, next_state):
            # Log warning but continue (messages are pre-validated in REACTION_MESSAGES)
            # Logger un avertissement mais continuer (messages pré-validés dans REACTION_MESSAGES)
            pass
        
        return {
            "action": action,
            "message": message,
            "next_state": next_state
        }
    
    def run_from_stdin(self) -> None:
        """
        Read emotion data from STDIN (JSON Lines format) and process each line.
        Lit les données d'émotions depuis STDIN (format JSON Lines) et traite chaque ligne.
        
        Input format / Format d'entrée:
            Each line must be a valid JSON object with keys:
            Chaque ligne doit être un objet JSON valide avec les clés:
            - "user_text": The user's text input / Le texte saisi par l'utilisateur
            - "emotion": The detected emotion / L'émotion détectée
            - "confidence": The confidence level / Le niveau de confiance
        
        Output format / Format de sortie:
            Each output line is a JSON object with keys:
            Chaque ligne de sortie est un objet JSON avec les clés:
            - "action": The action to take / L'action à effectuer
            - "message": The response message / Le message de réponse
            - "next_state": The next dialogue state / Le prochain état du dialogue
        """
        import sys
        
        try:
            # Read from STDIN line by line / Lire depuis STDIN ligne par ligne
            for line in sys.stdin:
                line = line.strip()
                
                # Skip empty lines / Ignorer les lignes vides
                if not line:
                    continue
                
                try:
                    # Parse JSON from this line / Parser le JSON de cette ligne
                    emotion_data = loads(line)
                    
                    # Process the input / Traiter l'entrée
                    result = self.process_input(emotion_data)
                    
                    # Output as JSON (one line) / Sortie en JSON (une ligne)
                    print(dumps(result))
                    
                except Exception as parse_error:
                    # Invalid JSON or processing error / JSON invalide ou erreur de traitement
                    print(dumps({
                        "action": "ask_clarification",
                        "message": "Could you please clarify how you're feeling?",
                        "next_state": self.state_manager.current_state
                    }))
                    
        except KeyboardInterrupt:
            # User interrupted (Ctrl+C) / Utilisateur a interrompu (Ctrl+C)
            pass
    
    def run_from_file(self, filename: str) -> None:
        """
        Read emotion data from a JSON file and process each entry.
        Lit les données d'émotions depuis un fichier JSON et traite chaque entrée.
        
        Args:
            filename: Path to the JSON file / Chemin vers le fichier JSON
        
        Note: This is legacy mode for backward compatibility.
              Use run_from_stdin() for the standard JSON Lines format.
              Ceci est le mode hérité pour la compatibilité.
              Utilisez run_from_stdin() pour le format JSON Lines standard.
        """
        try:
            # Open and read the JSON file / Ouvrir et lire le fichier JSON
            with open(filename, 'r', encoding='utf-8') as json_file:
                emotion_data = loads(json_file.read())
                
                # Ensure data is a list / S'assurer que les données sont une liste
                if not isinstance(emotion_data, list):
                    emotion_data = [emotion_data]
                
                # Process each emotion entry / Traiter chaque entrée d'émotion
                for entry in emotion_data:
                    result = self.process_input(entry)
                    # Output as JSON / Sortie en JSON
                    print(dumps(result))
                    
        except FileNotFoundError:
            print(dumps({
                "action": "ask_clarification",
                "message": "Error: File not found / Erreur: Fichier introuvable",
                "next_state": self.state_manager.current_state
            }))
        except Exception as error:
            print(dumps({
                "action": "ask_clarification",
                "message": f"Error processing input / Erreur de traitement: {str(error)}",
                "next_state": self.state_manager.current_state
            }))


# ============================================================================
# MAIN ENTRY POINT / POINT D'ENTRÉE PRINCIPAL
# ============================================================================

def main():
    """
    Main entry point of the program.
    Point d'entrée principal du programme.
    
    Usage / Utilisation:
        Standard mode (STDIN) / Mode standard (STDIN):
            python EmotionDamage.py < input.jsonl
            echo '{"user_text":"...","emotion":"...","confidence":"..."}' | python EmotionDamage.py
        
        Legacy mode (file) / Mode hérité (fichier):
            python EmotionDamage.py <json_file>
    """
    processor = DialogueProcessor()
    
    # Check if a filename was provided (legacy mode)
    # Vérifier si un nom de fichier a été fourni (mode hérité)
    if len(argv) >= 2:
        # Legacy mode: read from file / Mode hérité: lire depuis un fichier
        processor.run_from_file(argv[1])
    else:
        # Standard mode: read from STDIN / Mode standard: lire depuis STDIN
        processor.run_from_stdin()


if __name__ == "__main__":
    main()