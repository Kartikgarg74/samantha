"""
Intent Classification Module
Determines the intent of user commands to route them to appropriate handlers.
"""

import re
from typing import Dict, List

import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class IntentClassifier:
    """Advanced intent classification using DialoGPT with improved prompting"""

    def __init__(self, model_name="microsoft/DialoGPT-small"):
        print(f"Loading intent classifier model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

        # Intent categories
        self.intents = {
            "browser": ["open website", "search for", "browse", "google", "brave", "firefox", "chrome", "safari", "internet"],
            "spotify": ["play music", "pause music", "next song", "previous song", "volume", "spotify"],
            "whatsapp": ["send message", "text", "whatsapp", "call"],
            "system": ["shutdown", "restart", "sleep", "volume", "brightness"],
            "timer": ["set timer", "set alarm", "remind me"],
            "weather": ["weather", "temperature", "forecast"],
            "general": ["who are you", "your name", "tell me", "what is", "how to"]
        }

        # Load system prompt for better intent understanding
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self):
        """Load a system prompt to guide intent classification"""
        # This could be expanded to load from your leaked prompts collection
        return """
        You are an intent classification system. Your job is to accurately determine what the user wants to do
        based on their message. Analyze the entire meaning of the request, not just keywords.

        For multi-step intentions, identify the primary intent and any secondary actions.
        """

    def classify_with_context(self, text, conversation_context=None):
        """Classify intent using the LLM with conversation context"""

        # Create prompt with context and current request
        context_text = ""
        if conversation_context:
            for msg in conversation_context:
                role = msg['role']
                content = msg['content']
                context_text += f"{role}: {content}\n"

        # Build the complete prompt
        prompt = f"{self.system_prompt}\n\nConversation History:\n{context_text}\n\nUser: {text}\n\nIntent:"

        # Prepare input for the model
        inputs = self.tokenizer.encode(prompt, return_tensors="pt")

        # Generate response
        outputs = self.model.generate(
            inputs,
            max_length=150,
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id,
            do_sample=True,
            temperature=0.7
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract the model's classification
        intent_prediction = response.split("Intent:")[-1].strip()

        # Map to our intent categories using a more sophisticated approach
        detected_intent = self._map_to_intent_category(text, intent_prediction)
        confidence = self._calculate_confidence(text, detected_intent)

        return {
            "intent": detected_intent,
            "confidence": confidence,
            "original_text": text,
            "model_prediction": intent_prediction
        }

    def _map_to_intent_category(self, text, prediction):
        """Map the model prediction to one of our intent categories"""
        text = text.lower()

        # First check for direct intent matches in the prediction
        for intent, keywords in self.intents.items():
            for keyword in keywords:
                if keyword.lower() in prediction.lower():
                    return intent

        # Fall back to checking the original text
        matches = {}
        for intent, keywords in self.intents.items():
            matches[intent] = sum(1 for keyword in keywords if keyword.lower() in text)

        # Find the intent with most matches
        if any(matches.values()):
            return max(matches, key=matches.get)

        # Default to general if no matches
        return "general"

    def _calculate_confidence(self, text, detected_intent):
        """Calculate a confidence score for the detected intent"""
        text = text.lower()
        keyword_count = 0
        total_keywords = 0

        for intent, keywords in self.intents.items():
            for keyword in keywords:
                total_keywords += 1
                if keyword.lower() in text:
                    keyword_count += 2 if intent == detected_intent else 1

        # Basic confidence calculation
        confidence = min(0.5 + (keyword_count / total_keywords), 0.95)
        return confidence

    def classify(self, text: str) -> str:
        """
        Classify the intent of the given text.

        Args:
            text (str): Input text to classify

        Returns:
            str: Predicted intent
        """
        text_lower = text.lower().strip()
        intent_scores = {}

        # Calculate scores for each intent
        for intent, patterns in self.intent_patterns.items():
            score = 0

            # Check exact phrase matches (higher weight)
            for phrase in patterns["phrases"]:
                if phrase in text_lower:
                    score += 3

            # Check keyword matches
            for keyword in patterns["keywords"]:
                if keyword in text_lower:
                    score += 1

            # Special handling for compound phrases
            score += self._check_compound_phrases(text_lower, intent)

            intent_scores[intent] = score

        # Return intent with highest score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            max_score = intent_scores[best_intent]

            # Only return intent if score is above threshold
            if max_score > 0:
                return best_intent

        # Default to general if no clear intent
        return "general"

    def _check_compound_phrases(self, text: str, intent: str) -> int:
        """
        Check for compound phrases that strongly indicate specific intents.

        Args:
            text (str): Input text
            intent (str): Intent to check

        Returns:
            int: Additional score for compound phrases
        """
        compound_patterns = {
            "spotify": [
                r"play .*? (song|music|track)",
                r"(volume|turn) (up|down)",
                r"(like|unlike) (this|current) song",
                r"add .* to playlist",
                r"what('s| is) (playing|this song)",
                r"search (for )?.*? (music|song)",
                r"(pause|stop) (music|song|spotify)",
                r"(next|previous|skip) (song|track)"
            ],

            "browser": [
                r"open .*?\.(com|org|net|edu)",
                r"go to .*?\.(com|org|net|edu)",
                r"search (for )?.*? (on )?(google|youtube)",
                r"(close|open) (tab|browser|window)",
                r"browse to .*"
            ],

            "whatsapp": [
                r"(message|text|send) .* (to )?.*",
                r"(call|video call) .*",
                r"send .* to .*",
                r"share .* with .*",
                r"whatsapp .*"
            ],

            "assistant_control": [
                r"(stop|start) listening",
                r"(speak|talk) (louder|quieter|faster|slower)",
                r"what can you do",
                r"show me (commands|help)",
                r"(assistant|samantha) (help|settings)"
            ],

            "time_date": [
                r"what (time|date) is it",
                r"what('s| is) the (time|date)",
                r"tell me the (time|date)",
                r"current (time|date)"
            ]
        }

        if intent in compound_patterns:
            for pattern in compound_patterns[intent]:
                if re.search(pattern, text):
                    return 2

        return 0

    def get_confidence(self, text: str) -> Dict[str, float]:
        """
        Get confidence scores for all intents.

        Args:
            text (str): Input text

        Returns:
            Dict[str, float]: Dictionary of intent confidences
        """
        text_lower = text.lower().strip()
        intent_scores = {}
        total_score = 0

        # Calculate raw scores
        for intent, patterns in self.intent_patterns.items():
            score = 0

            for phrase in patterns["phrases"]:
                if phrase in text_lower:
                    score += 3

            for keyword in patterns["keywords"]:
                if keyword in text_lower:
                    score += 1

            score += self._check_compound_phrases(text_lower, intent)
            intent_scores[intent] = score
            total_score += score

        # Convert to confidence percentages
        if total_score > 0:
            confidences = {intent: score / total_score for intent, score in intent_scores.items()}
        else:
            confidences = {intent: 0.0 for intent in self.intent_patterns.keys()}

        return confidences

# Global classifier instance
_classifier = IntentClassifier()

def classify_intent(text: str) -> str:
    """
    Main function to classify intent from text.

    Args:
        text (str): Input text to classify

    Returns:
        str: Predicted intent
    """
    return _classifier.classify(text)

def get_intent_confidence(text: str) -> Dict[str, float]:
    """
    Get confidence scores for all intents.

    Args:
        text (str): Input text

    Returns:
        Dict[str, float]: Dictionary of intent confidences
    """
    return _classifier.get_confidence(text)

# Example usage and testing
if __name__ == "__main__":
    test_commands = [
        "play some music",
        "pause spotify",
        "next song please",
        "volume up",
        "open google",
        "search for cats on youtube",
        "message mom hello",
        "call dad",
        "what time is it",
        "hello samantha",
        "goodbye",
        "what can you do",
        "like this song",
        "add this to my playlist"
    ]

    print("🧠 Testing Intent Classification:")
    print("-" * 50)

    for command in test_commands:
        intent = classify_intent(command)
        confidence = get_intent_confidence(command)
        max_confidence = max(confidence.values()) if confidence else 0

        print(f"Command: '{command}'")
        print(f"Intent: {intent} (confidence: {max_confidence:.2%})")
        print()
