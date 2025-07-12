import os

def whatsapp_action(command: str) -> str:
    command = command.lower()
    if "open whatsapp" in command:
        os.system('open -a "WhatsApp"')
        return "Opening WhatsApp."
    elif "send message" in command:
        # Extract contact and message
        contact = "contact_name_here"
        message = "message_here"
        return f"Sending '{message}' to {contact}."
    else:
        return "WhatsApp command not recognized."
