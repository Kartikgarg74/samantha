"""
Intent Classification Module
Determines the intent of user commands to route them to appropriate handlers.
"""

import re
from typing import Dict, List

class IntentClassifier:
    def __init__(self):
        """Initialize the intent classifier with keyword patterns"""
        self.intent_patterns = {
            "spotify": {
                "keywords": [
                    "play", "pause", "stop music", "next", "previous", "skip", "back",
                    "volume", "louder", "quieter", "music", "song", "track", "album",
                    "playlist", "spotify", "like song", "unlike", "current song",
                    "what's playing", "now playing", "search music", "add to playlist",
                    "remove from playlist", "liked songs", "my music", "resume"
                ],
                "phrases": [
                    "play music", "pause music", "next song", "previous song",
                    "volume up", "volume down", "like this song", "unlike this song",
                    "what song is this", "add to playlist", "create playlist",
                    "search for", "play spotify"
                ]
            },

            "browser": {
                "keywords": [
                    "open", "browse", "website", "search", "google", "youtube",
                    "facebook", "twitter", "instagram", "reddit", "github",
                    "close tab", "new tab", "refresh", "back", "forward",
                    "bookmark", "history", "download"
                ],
                "phrases": [
                    "open website", "go to", "search for", "browse to",
                    "open google", "search google", "youtube search",
                    "close browser", "new window", "incognito mode"
                ]
            },

            "whatsapp": {
                "keywords": [
                    "whatsapp", "message", "text", "call", "video call",
                    "send", "share", "file", "contact", "chat", "voice message"
                ],
                "phrases": [
                    "send message", "whatsapp message", "call someone",
                    "video call", "share file", "open whatsapp", "close whatsapp",
                    "message to", "send to", "call mom", "call dad"
                ]
            },

            "greeting": {
                "keywords": [
                    "hello", "hi", "hey", "good morning", "good afternoon",
                    "good evening", "how are you", "what's up", "greetings"
                ],
                "phrases": [
                    "hello samantha", "hi there", "good morning samantha",
                    "how are you doing", "what's up"
                ]
            },

            "goodbye": {
                "keywords": [
                    "goodbye", "bye", "see you", "farewell", "exit", "quit",
                    "stop", "turn off", "shutdown"
                ],
                "phrases": [
                    "goodbye samantha", "see you later", "bye bye",
                    "turn off", "shut down", "stop listening permanently"
                ]
            },

            "assistant_control": {
                "keywords": [
                    "help", "what can you do", "capabilities", "commands",
                    "stop listening", "wake up", "volume", "speak louder",
                    "speak quieter", "settings", "configure"
                ],
                "phrases": [
                    "what can you do", "show me commands", "help me",
                    "stop listening", "speak louder", "speak quieter",
                    "assistant volume", "samantha settings"
                ]
            },

            "time_date": {
                "keywords": [
                    "time", "date", "today", "now", "current time",
                    "what time", "what date", "clock", "calendar"
                ],
                "phrases": [
                    "what time is it", "what's the time", "what date is it",
                    "what's today's date", "current time", "tell me the time"
                ]
            },

            "weather": {
                "keywords": [
                    "weather", "temperature", "forecast", "rain", "sunny",
                    "cloudy", "hot", "cold", "humidity", "wind"
                ],
                "phrases": [
                    "what's the weather", "weather forecast", "is it raining",
                    "temperature today", "how's the weather"
                ]
            },

            "general": {
                "keywords": [
                    "what", "how", "why", "when", "where", "who", "tell me",
                    "explain", "define", "calculate", "convert"
                ],
                "phrases": [
                    "tell me about", "what is", "how do", "explain this",
                    "calculate this", "convert this"
                ]
            }
        }

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
