import os

def system_action(command: str) -> str:
    command = command.lower()
    if "open" in command:
        app_name = command.replace("open", "").strip().title()
        os.system(f'open -a "{app_name}"')
        return f"Opening {app_name}."
    elif "close" in command:
        app_name = command.replace("close", "").strip().title()
        os.system(f'osascript -e \'tell application "{app_name}" to quit\'')
        return f"Closing {app_name}."
    else:
        return "System command not recognized."
