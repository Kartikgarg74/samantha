from assistant.intent_classifier import detect_intent

def test_detect_browser_automation_intent():
    command = "search Brave browser"
    intent = detect_intent(command)
    assert intent == "browserautomation"

def test_detect_open_app_intent():
    command = "open Spotify"
    intent = detect_intent(command)
    assert intent == "openapp"

def test_detect_close_app_intent():
    command = "close Spotify"
    intent = detect_intent(command)
    assert intent == "closeapp"

def test_detect_general_intent():
    command = "random command"
    intent = detect_intent(command)
    assert intent == "general"
