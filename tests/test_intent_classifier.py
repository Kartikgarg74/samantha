#!/usr/bin/env python3
"""
Unit tests for the Intent Classifier.
Tests intent detection, confidence scoring, and context awareness.
"""

import os
import sys
import unittest
import pytest
import json
import numpy as np
from unittest.mock import patch, MagicMock, PropertyMock

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from assistant.intent_classifier import IntentClassifier

# Sample test cases for intents
TEST_CASES = [
    {"text": "play some music", "expected_intent": "spotify"},
    {"text": "open google", "expected_intent": "browser"},
    {"text": "send a message to john", "expected_intent": "whatsapp"},
    {"text": "what time is it", "expected_intent": "system"},
    {"text": "tell me a joke", "expected_intent": "general"},
    {"text": "what's the weather like today", "expected_intent": "weather"},
    {"text": "set a timer for 5 minutes", "expected_intent": "timer"},
]

# Test multi-step commands
MULTI_STEP_TEST_CASES = [
    {
        "text": "open google and search for pizza recipes",
        "expected_steps": ["open google", "search for pizza recipes"]
    },
    {
        "text": "first play some music, then send a message to John",
        "expected_steps": ["play some music", "send a message to John"]
    },
    {
        "text": "1. check the weather 2. set a timer for 10 minutes",
        "expected_steps": ["check the weather", "set a timer for 10 minutes"]
    },
]

class MockModel:
    """Mock model for testing the intent classifier."""

    def __init__(self, device="cpu"):
        self.device = device

    def __call__(self, texts):
        """Simulate model prediction based on keywords."""
        results = []

        for text in texts:
            text = text.lower()
            probs = {
                "spotify": 0.1,
                "browser": 0.1,
                "whatsapp": 0.1,
                "system": 0.1,
                "timer": 0.1,
                "weather": 0.1,
                "general": 0.1
            }

            # Keyword-based mock predictions
            if any(word in text for word in ["play", "music", "song", "spotify"]):
                probs["spotify"] = 0.9
            elif any(word in text for word in ["open", "browser", "google", "search", "website"]):
                probs["browser"] = 0.9
            elif any(word in text for word in ["message", "send", "whatsapp", "text"]):
                probs["whatsapp"] = 0.9
            elif any(word in text for word in ["time", "date", "what day"]):
                probs["system"] = 0.9
            elif any(word in text for word in ["timer", "alarm", "remind"]):
                probs["timer"] = 0.9
            elif any(word in text for word in ["weather", "temperature", "forecast"]):
                probs["weather"] = 0.9
            else:
                probs["general"] = 0.7

            results.append(probs)

        return results


class TestIntentClassifier(unittest.TestCase):
    """Test cases for the intent classifier."""

    @patch('assistant.intent_classifier.IntentClassifier._load_model')
    def setUp(self, mock_load_model):
        """Set up the test fixture before each test method."""
        # Create a mock model
        mock_model = MockModel()
        mock_load_model.return_value = mock_model

        # Initialize the classifier with the mock model
        self.classifier = IntentClassifier(device="cpu", threshold=0.6)
        self.classifier.model = mock_model

    def test_classify_basic_intents(self):
        """Test classification of basic intents without context."""
        for case in TEST_CASES:
            text = case["text"]
            expected_intent = case["expected_intent"]

            # Classify without context
            result = self.classifier.classify_intent(text)

            # Check the result
            self.assertEqual(result["intent"], expected_intent,
                            f"Failed for '{text}': expected '{expected_intent}', got '{result['intent']}'")
            self.assertGreaterEqual(result["confidence"], 0.6,
                                  f"Low confidence for '{text}': {result['confidence']}")

    def test_classify_with_context(self):
        """Test classification with conversation context."""
        # Create context that suggests a Spotify-related conversation
        context = {
            "recent_exchanges": [
                {"user": "play some rock music", "assistant": "Playing rock music", "action": "spotify_playback"},
                {"user": "turn up the volume", "assistant": "Volume increased", "action": "spotify_volume"}
            ],
            "current_app": "spotify"
        }

        # Test with ambiguous command that could be interpreted differently with context
        result = self.classifier.classify_with_context("turn it up", context)

        # With Spotify context, this should be classified as Spotify intent
        self.assertEqual(result["intent"], "spotify")

    def test_confidence_threshold(self):
        """Test that confidence threshold is respected."""
        # Create a classifier with a very high threshold
        with patch('assistant.intent_classifier.IntentClassifier._load_model') as mock_load:
            mock_load.return_value = MockModel()
            high_threshold_classifier = IntentClassifier(threshold=0.95)

        # Test with a clear Spotify command
        result = high_threshold_classifier.classify_intent("play some music")

        # Even though the mock would return 0.9 confidence, this should fall back to general
        # since it's below the 0.95 threshold
        self.assertEqual(result["intent"], "general")

    def test_can_handle_multi_step(self):
        """Test detection of multi-step commands."""
        for case in MULTI_STEP_TEST_CASES:
            text = case["text"]
            self.assertTrue(self.classifier.can_handle_multi_step(text),
                           f"Failed to detect multi-step command: '{text}'")

        # Test with single-step commands
        for case in TEST_CASES:
            text = case["text"]
            self.assertFalse(self.classifier.can_handle_multi_step(text),
                            f"Incorrectly detected multi-step for: '{text}'")

    def test_extract_steps(self):
        """Test extraction of individual steps from multi-step commands."""
        for case in MULTI_STEP_TEST_CASES:
            text = case["text"]
            expected_steps = case["expected_steps"]

            # Extract steps
            steps = self.classifier.extract_steps(text)

            # Check results
            self.assertEqual(len(steps), len(expected_steps),
                            f"Wrong number of steps for '{text}': expected {len(expected_steps)}, got {len(steps)}")

            for i, (expected, actual) in enumerate(zip(expected_steps, steps)):
                self.assertTrue(expected.lower() in actual.lower(),
                               f"Step {i+1} mismatch: expected '{expected}' in '{actual}'")


# Additional tests with pytest

@pytest.fixture
def mock_classifier():
    """Create a classifier with mocked model."""
    with patch('assistant.intent_classifier.IntentClassifier._load_model') as mock_load:
        mock_load.return_value = MockModel()
        classifier = IntentClassifier(device="cpu")
        yield classifier

def test_device_selection():
    """Test proper device selection logic."""
    # Test CPU fallback when GPU/MPS not available
    with patch('torch.cuda.is_available', return_value=False):
        with patch('hasattr', return_value=False):  # No MPS
            with patch('assistant.intent_classifier.IntentClassifier._load_model') as mock_load:
                classifier = IntentClassifier(device="auto")
                # Should default to CPU
                assert classifier.device == "cpu"

@pytest.mark.parametrize("text,expected_intent", [
    ("play my favorite playlist", "spotify"),
    ("search for pizza restaurants", "browser"),
    ("text mom I'll be late", "whatsapp"),
])
def test_specific_intent_cases(mock_classifier, text, expected_intent):
    """Test specific intent cases."""
    result = mock_classifier.classify_intent(text)
    assert result["intent"] == expected_intent

def test_context_precedence(mock_classifier):
    """Test that context can override weak classifications."""
    # Create a context with a strong browser history
    context = {
        "recent_exchanges": [
            {"user": "open github", "assistant": "Opening GitHub", "action": "browser_open"},
            {"user": "search for python tutorials", "assistant": "Searching...", "action": "browser_search"}
        ],
        "current_app": "browser"
    }

    # Use an ambiguous command
    result = mock_classifier.classify_with_context("go to the next one", context)

    # Should use browser intent based on context
    assert result["intent"] == "browser"
    assert result["method"] == "context_enhanced"

def test_empty_or_short_input(mock_classifier):
    """Test handling of empty or very short inputs."""
    # Empty string
    result = mock_classifier.classify_intent("")
    assert result["intent"] == "general"
    assert result["confidence"] < 0.5

    # Very short input
    result = mock_classifier.classify_intent("hi")
    assert result["intent"] == "general"

def test_classification_with_noise(mock_classifier):
    """Test classification with noisy input."""
    # Command with filler words and typos
    result = mock_classifier.classify_intent("umm can you like playyy some musc please")
    assert result["intent"] == "spotify"  # Should still detect music intent

if __name__ == '__main__':
    unittest.main()
