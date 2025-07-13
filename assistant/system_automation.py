import os
import subprocess

def system_action(command: str, system_prompt: str = "") -> tuple:
    """
    Execute system actions based on natural language commands.

    Args:
        command: The natural language command to interpret and execute
        system_prompt: Optional system prompt to provide context

    Returns:
        tuple: (response message, action identifier)
    """
    command = command.lower()

    # Opening applications
    if "open" in command:
        app_name = command.replace("open", "").strip().title()
        try:
            # Use subprocess.Popen and check if it raises an exception
            process = subprocess.Popen(['open', '-a', app_name])
            # Check if the process started successfully
            if process.poll() is not None and process.returncode != 0:
                return f"Error opening {app_name}. The application might not exist.", "system_error"
            return f"Opening {app_name}.", "system_open_app"
        except Exception as e:
            return f"Error opening {app_name}: {str(e)}", "system_error"

    # Closing applications
    elif "close" in command:
        app_name = command.replace("close", "").strip().title()
        try:
            # Use subprocess.run with check=True to raise an exception on non-zero exit codes
            result = subprocess.run(['osascript', '-e', f'tell application "{app_name}" to quit'], check=False)
            if result.returncode != 0:
                return f"Error closing {app_name}. The application might not be running.", "system_error"
            return f"Closing {app_name}.", "system_close_app"
        except Exception as e:
            return f"Error closing {app_name}: {str(e)}", "system_error"

    # Volume control
    elif "volume" in command:
        try:
            volume_level = None
            # Extract volume percentage if present
            if "percent" in command:
                parts = command.split()
                for i, part in enumerate(parts):
                    if part.isdigit() and i+1 < len(parts) and "percent" in parts[i+1]:
                        volume_level = int(part)
                        break

            if volume_level is not None:
                # Volume level should be between 0 and 100
                volume_level = max(0, min(100, volume_level))
                # macOS volume ranges from 0 to 10
                macos_volume = volume_level / 10.0
                result = subprocess.run(['osascript', '-e', f'set volume output volume {macos_volume}'], check=False)
                if result.returncode != 0:
                    return f"Failed to set volume to {volume_level}%.", "system_error"
                return f"Volume set to {volume_level}%.", "system_volume"
            else:
                return "Could not determine volume level.", "system_error"
        except Exception as e:
            return f"Error setting volume: {str(e)}", "system_error"

    # Brightness control
    elif "brightness" in command:
        try:
            brightness_level = None
            # Extract brightness percentage if present
            if "percent" in command:
                parts = command.split()
                for i, part in enumerate(parts):
                    if part.isdigit() and i+1 < len(parts) and "percent" in parts[i+1]:
                        brightness_level = int(part)
                        break

            if brightness_level is not None:
                # Brightness level should be between 0 and 100
                brightness_level = max(0, min(100, brightness_level))
                result = subprocess.run(['osascript', '-e',
                    f'tell application "System Events" to tell appearance preferences to set properties to {{brightness:{brightness_level/100.0}}}'],
                    check=False)
                if result.returncode != 0:
                    return f"Failed to set brightness to {brightness_level}%.", "system_error"
                return f"Brightness set to {brightness_level}%.", "system_brightness"
            else:
                return "Could not determine brightness level.", "system_error"
        except Exception as e:
            return f"Error setting brightness: {str(e)}", "system_error"

    # System information
    elif "system information" in command or "system info" in command:
        try:
            # Get system info using system_profiler
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return "Failed to retrieve system information.", "system_error"
            return f"System information:\n{result.stdout}", "system_info"
        except Exception as e:
            return f"Error retrieving system information: {str(e)}", "system_error"

    # System sleep
    elif "sleep" in command and ("computer" in command or "system" in command):
        try:
            result = subprocess.run(['osascript', '-e', 'tell application "System Events" to sleep'], check=False)
            if result.returncode != 0:
                return "Failed to put computer to sleep.", "system_error"
            return "Putting the computer to sleep.", "system_sleep"
        except Exception as e:
            return f"Error putting computer to sleep: {str(e)}", "system_error"

    # System restart
    elif "restart" in command and ("computer" in command or "system" in command):
        try:
            result = subprocess.run(['osascript', '-e', 'tell application "System Events" to restart'], check=False)
            if result.returncode != 0:
                return "Failed to restart the computer.", "system_error"
            return "Restarting the computer.", "system_restart"
        except Exception as e:
            return f"Error restarting the computer: {str(e)}", "system_error"

    # Unknown or unsupported command
    else:
        return "System command not recognized.", "system_unknown"
