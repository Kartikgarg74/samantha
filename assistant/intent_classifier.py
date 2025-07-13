"""
Intent Classifier Module

This module classifies user intents to determine appropriate responses
and actions for the assistant.
"""

import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Optional imports for machine learning models
try:
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from assistant.config_manager import config_manager


logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifies user intents using rule-based patterns or ML models.
    """

    def __init__(self):
        """
        Initialize the intent classifier.
        """
        # Load configuration
        self.config = config_manager.get_section("intent_classifier")
        self.model_name = self.config.get("model", "microsoft/DialoGPT-small")

        # Set up device
        self.device = "cpu"
        if ML_AVAILABLE and torch.cuda.is_available() and self.config.get("use_gpu", False):
            self.device = "cuda"
        elif ML_AVAILABLE and hasattr(torch.backends, 'mps') and torch.backends.mps.is_built() and self.config.get("use_mps", True):
            self.device = "mps"

        logger.info(f"Using {self.device} for intent classification")

        # Load intents from file
        self.intents = self._load_intents()

        # Initialize model
        self.model = None
        self.tokenizer = None
        if self.config.get("use_ml_model", True) and ML_AVAILABLE:
            self._load_model()

    def _load_intents(self) -> Dict[str, Any]:
        """
        Load intent definitions from file.

        Returns:
            Dictionary of intent definitions
        """
        intents_path = self.config.get("intents_file")

        # If no file specified, use default path
        if not intents_path:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            intents_path = os.path.join(base_dir, "data", "intents.json")

        intents = {
            "default": {
                "patterns": [],
                "responses": ["I'm not sure I understand. Can you rephrase that?"]
            },
            "greeting": {
                "patterns": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
                "responses": ["Hello! How can I help you today?"]
            },
            "farewell": {
                "patterns": ["goodbye", "bye", "see you", "exit", "quit"],
                "responses": ["Goodbye! Have a great day!"]
            }
        }

        try:
            if os.path.exists(intents_path):
                with open(intents_path, "r", encoding="utf-8") as f:
                    loaded_intents = json.load(f)
                    intents.update(loaded_intents)
        except Exception as e:
            logger.error(f"Error loading intents file: {e}")

        return intents

    def _load_model(self) -> None:
        """
        Load the ML model for intent classification.
        """
        if not ML_AVAILABLE:
            logger.warning("Machine learning libraries not available. Using rule-based classification only.")
            return

        try:
            print(f"Loading intent classifier model: {self.model_name}")
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

            # Move model to appropriate device
            self.model.to(self.device)
            logger.info(f"Loaded intent classifier model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error loading intent classifier model: {e}")
            self.model = None
            self.tokenizer = None

    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify the intent of the user's text.

        Args:
            text: User's input text

        Returns:
            Tuple of (intent_name, confidence_score)
        """
        text = text.lower().strip()

        # Rule-based matching first
        for intent_name, intent_data in self.intents.items():
            patterns = intent_data.get("patterns", [])
            for pattern in patterns:
                if pattern.lower() in text:
                    return intent_name, 0.9  # High confidence for exact matches

        # Use ML model if available
        if self.model and self.tokenizer:
            try:
                return self._classify_with_model(text)
            except Exception as e:
                logger.error(f"Error in ML classification: {e}")

        # Fall back to simple keyword matching
        intent_scores = self._simple_keyword_match(text)
        best_intent = max(intent_scores.items(), key=lambda x: x[1])

        # If the best intent has a very low score, use default intent
        if best_intent[0] != "default" and best_intent[1] < 0.3:
            return "default", 0.5

        return best_intent[0], best_intent[1]

    def _classify_with_model(self, text: str) -> Tuple[str, float]:
        """
        Use the ML model to classify intent.

        Args:
            text: User's input text

        Returns:
            Tuple of (intent_name, confidence_score)
        """
        # Encode the input text
        inputs = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            return_tensors="pt"
        ).to(self.device)

        # Get model output
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Process the outputs to get intent and confidence
        # This is a simplified approach - actual implementation depends on model
        logits = outputs.logits

        # Convert logits to probabilities
        probs = torch.softmax(logits[:, -1], dim=-1)

        # Map to intents (simplified approach)
        intent_scores = {}
        for intent_name in self.intents.keys():
            # This is a placeholder approach - would need to be customized based on the model
            intent_tokens = self.tokenizer.encode(intent_name)
            score = sum(probs[0, token].item() for token in intent_tokens) / len(intent_tokens)
            intent_scores[intent_name] = score

        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], best_intent[1]

    def _simple_keyword_match(self, text: str) -> Dict[str, float]:
        """
        Perform simple keyword matching for intent classification.

        Args:
            text: User's input text

        Returns:
            Dictionary of intent names and confidence scores
        """
        words = text.split()
        scores = {intent: 0.0 for intent in self.intents}

        for intent_name, intent_data in self.intents.items():
            patterns = intent_data.get("patterns", [])
            max_score = 0.0

            for pattern in patterns:
                pattern_words = pattern.lower().split()
                matches = sum(1 for word in words if word in pattern_words)

                if pattern_words:  # Avoid division by zero
                    score = matches / len(pattern_words)
                    max_score = max(max_score, score)

            scores[intent_name] = max_score

        # If no good matches found, assign higher score to default intent
        # This helps ensure the default intent is selected when no good matches exist
        max_score = max(scores.values())
        if max_score < 0.3:  # Threshold for confidence
            scores["default"] = 0.5  # Default confidence

        return scores

    def get_response(self, intent: str) -> str:
        """
        Get a response based on the classified intent.

        Args:
            intent: Intent name

        Returns:
            Response text
        """
        # Get responses for this intent
        intent_data = self.intents.get(intent, self.intents.get("default"))
        responses = intent_data.get("responses", ["I don't know how to respond to that."])

        # For now, just return the first response
        # In a more sophisticated version, we could randomly select one
        return responses[0]

    def add_intent(self, name: str, patterns: List[str], responses: List[str]) -> None:
        """
        Add a new intent to the classifier.

        Args:
            name: Intent name
            patterns: List of pattern strings
            responses: List of response strings
        """
        self.intents[name] = {
            "patterns": patterns,
            "responses": responses
        }

        # Save updated intents to file
        self._save_intents()

    def _save_intents(self) -> None:
        """Save intent definitions to file."""
        intents_path = self.config.get("intents_file")

        # If no file specified, use default path
        if not intents_path:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            intents_path = os.path.join(base_dir, "data", "intents.json")

        # Ensure directory exists
        os.makedirs(os.path.dirname(intents_path), exist_ok=True)

        try:
            with open(intents_path, "w", encoding="utf-8") as f:
                json.dump(self.intents, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving intents file: {e}")


# Create an instance for easy importing
intent_classifier = IntentClassifier()


if __name__ == "__main__":
    # Example usage
    classifier = IntentClassifier()

    # Test classification
    test_texts = [
        "Hello there!",
        "What's the weather like today?",
        "Play some music",
        "Goodbye",
    ]

    for text in test_texts:
        intent, confidence = classifier.classify(text)
        response = classifier.get_response(intent)
        print(f"Text: {text}")
        print(f"Intent: {intent} (confidence: {confidence:.2f})")
        print(f"Response: {response}")
        print("---")
