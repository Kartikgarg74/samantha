import os
import time
import pyautogui
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def whatsapp_action(command: str):
    """
    Handle WhatsApp Desktop automation commands
    """
    command_lower = command.lower()

    try:
        # Open WhatsApp Desktop
        if "open whatsapp" in command_lower or "launch whatsapp" in command_lower:
            return open_whatsapp()

        # Close WhatsApp Desktop
        elif "close whatsapp" in command_lower or "quit whatsapp" in command_lower:
            return close_whatsapp()

        # Message someone
        elif "message" in command_lower or "send message" in command_lower:
            # Extract contact name and message
            if "message" in command_lower:
                parts = command_lower.split("message", 1)[1].strip()
                if " " in parts:
                    # Try to find contact and message
                    words = parts.split()
                    # Last word is likely the message, everything before is contact
                    if len(words) >= 2:
                        message = words[-1]
                        contact = " ".join(words[:-1])
                    else:
                        contact = words[0] if words else ""
                        message = "Hello"
                else:
                    contact = ""
                    message = parts
            return send_message(contact, message)

        # Voice call someone
        elif "call" in command_lower and "video" not in command_lower:
            contact = extract_contact_name(command_lower, "call")
            return make_voice_call(contact)

        # Video call someone
        elif "video call" in command_lower:
            contact = extract_contact_name(command_lower, "video call")
            return make_video_call(contact)

        # Share file
        elif "share file" in command_lower or "send file" in command_lower:
            contact = extract_contact_name(command_lower, "share file")
            file_path = extract_file_path(command_lower)
            return share_file(contact, file_path)

        else:
            return "WhatsApp command not recognized. Available: open, close, message [contact] [text], call [contact], video call [contact], share file [contact] [path]"

    except Exception as e:
        return f"WhatsApp automation error: {str(e)}"

def open_whatsapp():
    """Open WhatsApp Desktop application"""
    try:
        # Try opening WhatsApp Desktop
        os.system('open -a "WhatsApp"')
        time.sleep(3)  # Wait for app to load
        return "WhatsApp opened successfully"
    except Exception as e:
        return f"Failed to open WhatsApp: {str(e)}"

def close_whatsapp():
    """Close WhatsApp Desktop application"""
    try:
        os.system('osascript -e \'tell application "WhatsApp" to quit\'')
        return "WhatsApp closed successfully"
    except Exception as e:
        return f"Failed to close WhatsApp: {str(e)}"

def send_message(contact_name: str, message: str):
    """Send a message to a specific contact"""
    try:
        # Ensure WhatsApp is open
        open_whatsapp()
        time.sleep(2)

        # Click on search box (approximate coordinates - may need adjustment)
        pyautogui.click(200, 150)  # Search box location
        time.sleep(1)

        # Type contact name
        pyautogui.typewrite(contact_name)
        time.sleep(2)

        # Press Enter to select first result
        pyautogui.press('enter')
        time.sleep(1)

        # Click on message input area
        pyautogui.click(600, 700)  # Message input location
        time.sleep(1)

        # Type message
        pyautogui.typewrite(message)
        time.sleep(1)

        # Press Enter to send
        pyautogui.press('enter')

        return f"Message '{message}' sent to {contact_name}"

    except Exception as e:
        return f"Failed to send message: {str(e)}"

def make_voice_call(contact_name: str):
    """Make a voice call to a contact"""
    try:
        # Open chat with contact
        open_chat(contact_name)
        time.sleep(2)

        # Click on call button (phone icon)
        # You may need to adjust coordinates based on your screen resolution
        pyautogui.click(800, 150)  # Call button location
        time.sleep(1)

        return f"Voice call initiated to {contact_name}"

    except Exception as e:
        return f"Failed to make voice call: {str(e)}"

def make_video_call(contact_name: str):
    """Make a video call to a contact"""
    try:
        # Open chat with contact
        open_chat(contact_name)
        time.sleep(2)

        # Click on video call button
        pyautogui.click(850, 150)  # Video call button location
        time.sleep(1)

        return f"Video call initiated to {contact_name}"

    except Exception as e:
        return f"Failed to make video call: {str(e)}"

def share_file(contact_name: str, file_path: str = None):
    """Share a file with a contact"""
    try:
        # Open chat with contact
        open_chat(contact_name)
        time.sleep(2)

        # Click on attachment button (paperclip icon)
        pyautogui.click(550, 700)  # Attachment button location
        time.sleep(1)

        # Click on document option
        pyautogui.click(580, 650)  # Document option
        time.sleep(2)

        if file_path:
            # Type file path in finder
            pyautogui.hotkey('cmd', 'shift', 'g')  # Go to folder
            time.sleep(1)
            pyautogui.typewrite(file_path)
            pyautogui.press('enter')
            time.sleep(2)

        # If no specific file path, user will need to select manually
        return f"File sharing dialog opened for {contact_name}. Please select the file to share."

    except Exception as e:
        return f"Failed to share file: {str(e)}"

def open_chat(contact_name: str):
    """Helper function to open a chat with a specific contact"""
    # Ensure WhatsApp is open
    open_whatsapp()
    time.sleep(2)

    # Click on search box
    pyautogui.click(200, 150)
    time.sleep(1)

    # Clear search box
    pyautogui.hotkey('cmd', 'a')
    pyautogui.press('delete')
    time.sleep(0.5)

    # Type contact name
    pyautogui.typewrite(contact_name)
    time.sleep(2)

    # Press Enter to select first result
    pyautogui.press('enter')
    time.sleep(1)

def extract_contact_name(command: str, action: str):
    """Extract contact name from command"""
    try:
        parts = command.split(action, 1)[1].strip()
        # Remove common words and get the contact name
        words = parts.split()
        # Filter out common words
        contact_words = [word for word in words if word not in ['to', 'with', 'the', 'a', 'an']]
        return " ".join(contact_words) if contact_words else "Unknown"
    except:
        return "Unknown"

def extract_file_path(command: str):
    """Extract file path from command if provided"""
    try:
        if "file" in command:
            parts = command.split("file", 1)[1].strip()
            # Look for path-like strings
            words = parts.split()
            for word in words:
                if "/" in word or "\\" in word or word.endswith(('.pdf', '.doc', '.jpg', '.png', '.txt')):
                    return word
        return None
    except:
        return None

# Alternative approach using AppleScript for more reliable automation
def send_message_applescript(contact_name: str, message: str):
    """Send message using AppleScript (more reliable)"""
    try:
        script = f'''
        tell application "WhatsApp"
            activate
            delay 2
        end tell

        tell application "System Events"
            tell process "WhatsApp"
                -- Click search box
                click text field 1 of group 1 of group 1 of group 1 of window 1
                delay 1

                -- Type contact name
                keystroke "{contact_name}"
                delay 2

                -- Press enter to select contact
                key code 36
                delay 1

                -- Type message
                keystroke "{message}"
                delay 1

                -- Send message
                key code 36
            end tell
        end tell
        '''

        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        if result.returncode == 0:
            return f"Message sent to {contact_name} via AppleScript"
        else:
            return f"AppleScript error: {result.stderr}"

    except Exception as e:
        return f"AppleScript message failed: {str(e)}"
