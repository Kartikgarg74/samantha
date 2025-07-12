from assistant.intent_classifier import detect_intent
from assistant.browser_control import perform_browser_action
from assistant.spotify_control import control_spotify
from assistant.whatsapp_integration import whatsapp_action
from assistant.system_automation import system_action

def handle_command(command: str):
    intent = detect_intent(command)
    if intent == "browserautomation":
        return perform_browser_action(command)
    elif intent == "openapp" or intent == "closeapp":
        return system_action(command)
    elif intent == "spotify":
        return control_spotify(command)
    elif intent == "whatsapp":
        return whatsapp_action(command)
    else:
        return "Command not recognized."

if __name__ == "__main__":
    while True:
        user_input = input("Enter your command: ")
        response = handle_command(user_input)
        print(response)
