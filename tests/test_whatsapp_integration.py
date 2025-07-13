import unittest
from unittest.mock import patch, MagicMock, call
import pyautogui
import os
import subprocess
import time
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assistant.whatsapp_integration import (
    whatsapp_action,
    open_whatsapp,
    close_whatsapp,
    send_message,
    make_voice_call,
    make_video_call,
    share_file,
    open_chat,
    extract_contact_name,
    extract_file_path,
    send_message_applescript
)

class TestWhatsAppIntegration(unittest.TestCase):
    """Test WhatsApp integration functionality."""

    @patch('assistant.whatsapp_integration.open_whatsapp')
    def test_whatsapp_action_open(self, mock_open_whatsapp):
        """Test opening WhatsApp."""
        mock_open_whatsapp.return_value = "WhatsApp opened successfully"

        # Test with different command variations
        result1 = whatsapp_action("open whatsapp")
        result2 = whatsapp_action("launch whatsapp")

        self.assertEqual(result1, "WhatsApp opened successfully")
        self.assertEqual(result2, "WhatsApp opened successfully")
        self.assertEqual(mock_open_whatsapp.call_count, 2)

    @patch('assistant.whatsapp_integration.close_whatsapp')
    def test_whatsapp_action_close(self, mock_close_whatsapp):
        """Test closing WhatsApp."""
        mock_close_whatsapp.return_value = "WhatsApp closed successfully"

        # Test with different command variations
        result1 = whatsapp_action("close whatsapp")
        result2 = whatsapp_action("quit whatsapp")

        self.assertEqual(result1, "WhatsApp closed successfully")
        self.assertEqual(result2, "WhatsApp closed successfully")
        self.assertEqual(mock_close_whatsapp.call_count, 2)

    @patch('assistant.whatsapp_integration.send_message')
    def test_whatsapp_action_message(self, mock_send_message):
        """Test sending messages through WhatsApp action."""
        mock_send_message.return_value = "Message sent successfully"

        # Test with contact and message
        result = whatsapp_action("message John Hello")

        mock_send_message.assert_called_once_with("john", "hello")
        self.assertEqual(result, "Message sent successfully")

    @patch('assistant.whatsapp_integration.make_voice_call')
    def test_whatsapp_action_voice_call(self, mock_make_voice_call):
        """Test voice calling through WhatsApp action."""
        mock_make_voice_call.return_value = "Voice call initiated to John"

        result = whatsapp_action("call John")

        mock_make_voice_call.assert_called_once_with("john")
        self.assertEqual(result, "Voice call initiated to John")

    @patch('assistant.whatsapp_integration.make_video_call')
    def test_whatsapp_action_video_call(self, mock_make_video_call):
        """Test video calling through WhatsApp action."""
        mock_make_video_call.return_value = "Video call initiated to John"

        result = whatsapp_action("video call John")

        mock_make_video_call.assert_called_once_with("john")
        self.assertEqual(result, "Video call initiated to John")

    @patch('assistant.whatsapp_integration.share_file')
    def test_whatsapp_action_share_file(self, mock_share_file):
        """Test file sharing through WhatsApp action."""
        mock_share_file.return_value = "File sharing dialog opened"

        # Test with file path
        result = whatsapp_action("share file with John /path/to/file.pdf")

        # The extract_contact_name and extract_file_path are being called inside whatsapp_action
        # So we need to check that share_file was called with their expected outputs
        mock_share_file.assert_called_once()
        self.assertEqual(result, "File sharing dialog opened")

    def test_whatsapp_action_unknown(self):
        """Test handling of unknown commands."""
        result = whatsapp_action("do something weird")

        self.assertTrue("WhatsApp command not recognized" in result)

    @patch('assistant.whatsapp_integration.os.system')
    @patch('assistant.whatsapp_integration.time.sleep')
    def test_open_whatsapp(self, mock_sleep, mock_system):
        """Test opening WhatsApp."""
        mock_system.return_value = 0  # Successful command execution

        result = open_whatsapp()

        mock_system.assert_called_once_with('open -a "WhatsApp"')
        mock_sleep.assert_called_once_with(3)
        self.assertEqual(result, "WhatsApp opened successfully")

    @patch('assistant.whatsapp_integration.os.system')
    def test_close_whatsapp(self, mock_system):
        """Test closing WhatsApp."""
        mock_system.return_value = 0  # Successful command execution

        result = close_whatsapp()

        mock_system.assert_called_once_with('osascript -e \'tell application "WhatsApp" to quit\'')
        self.assertEqual(result, "WhatsApp closed successfully")

    @patch('assistant.whatsapp_integration.open_whatsapp')
    @patch('assistant.whatsapp_integration.time.sleep')
    @patch('assistant.whatsapp_integration.pyautogui.click')
    @patch('assistant.whatsapp_integration.pyautogui.typewrite')
    @patch('assistant.whatsapp_integration.pyautogui.press')
    def test_send_message(self, mock_press, mock_typewrite, mock_click, mock_sleep, mock_open_whatsapp):
        """Test sending a message."""
        mock_open_whatsapp.return_value = "WhatsApp opened successfully"

        result = send_message("John", "Hello")

        # Verify WhatsApp was opened
        mock_open_whatsapp.assert_called_once()

        # Verify clicks at expected locations
        mock_click.assert_any_call(200, 150)  # Search box click
        mock_click.assert_any_call(600, 700)  # Message input click

        # Verify text was typed
        mock_typewrite.assert_any_call("John")  # Type contact name
        mock_typewrite.assert_any_call("Hello")  # Type message

        # Verify enter was pressed to send
        mock_press.assert_any_call('enter')

        self.assertEqual(result, "Message 'Hello' sent to John")

    @patch('assistant.whatsapp_integration.open_chat')
    @patch('assistant.whatsapp_integration.time.sleep')
    @patch('assistant.whatsapp_integration.pyautogui.click')
    def test_make_voice_call(self, mock_click, mock_sleep, mock_open_chat):
        """Test making a voice call."""
        result = make_voice_call("John")

        # Verify chat was opened with the contact
        mock_open_chat.assert_called_once_with("John")

        # Verify click on call button
        mock_click.assert_called_with(800, 150)

        self.assertEqual(result, "Voice call initiated to John")

    @patch('assistant.whatsapp_integration.open_chat')
    @patch('assistant.whatsapp_integration.time.sleep')
    @patch('assistant.whatsapp_integration.pyautogui.click')
    def test_make_video_call(self, mock_click, mock_sleep, mock_open_chat):
        """Test making a video call."""
        result = make_video_call("John")

        # Verify chat was opened with the contact
        mock_open_chat.assert_called_once_with("John")

        # Verify click on video call button
        mock_click.assert_called_with(850, 150)

        self.assertEqual(result, "Video call initiated to John")

    @patch('assistant.whatsapp_integration.open_chat')
    @patch('assistant.whatsapp_integration.time.sleep')
    @patch('assistant.whatsapp_integration.pyautogui.click')
    @patch('assistant.whatsapp_integration.pyautogui.hotkey')
    @patch('assistant.whatsapp_integration.pyautogui.typewrite')
    @patch('assistant.whatsapp_integration.pyautogui.press')
    def test_share_file_with_path(self, mock_press, mock_typewrite, mock_hotkey,
                                  mock_click, mock_sleep, mock_open_chat):
        """Test sharing a file with a specified path."""
        result = share_file("John", "/path/to/file.pdf")

        # Verify chat was opened
        mock_open_chat.assert_called_once_with("John")

        # Verify clicks for attachment
        mock_click.assert_any_call(550, 700)  # Attachment button
        mock_click.assert_any_call(580, 650)  # Document option

        # Verify file path was entered
        mock_hotkey.assert_called_with('cmd', 'shift', 'g')
        mock_typewrite.assert_called_with("/path/to/file.pdf")
        mock_press.assert_called_with('enter')

        self.assertTrue("File sharing dialog opened" in result)

    @patch('assistant.whatsapp_integration.open_chat')
    @patch('assistant.whatsapp_integration.time.sleep')
    @patch('assistant.whatsapp_integration.pyautogui.click')
    def test_share_file_without_path(self, mock_click, mock_sleep, mock_open_chat):
        """Test sharing a file without a specified path."""
        result = share_file("John")

        # Verify chat was opened
        mock_open_chat.assert_called_once_with("John")

        # Verify clicks for attachment
        mock_click.assert_any_call(550, 700)  # Attachment button
        mock_click.assert_any_call(580, 650)  # Document option

        self.assertTrue("File sharing dialog opened" in result)

    @patch('assistant.whatsapp_integration.open_whatsapp')
    @patch('assistant.whatsapp_integration.time.sleep')
    @patch('assistant.whatsapp_integration.pyautogui.click')
    @patch('assistant.whatsapp_integration.pyautogui.hotkey')
    @patch('assistant.whatsapp_integration.pyautogui.press')
    @patch('assistant.whatsapp_integration.pyautogui.typewrite')
    def test_open_chat(self, mock_typewrite, mock_press, mock_hotkey,
                       mock_click, mock_sleep, mock_open_whatsapp):
        """Test opening a chat with a contact."""
        open_chat("John")

        # Verify WhatsApp was opened
        mock_open_whatsapp.assert_called_once()

        # Verify search box was clicked
        mock_click.assert_called_with(200, 150)

        # Verify search box was cleared
        mock_hotkey.assert_called_with('cmd', 'a')
        mock_press.assert_any_call('delete')

        # Verify contact name was typed
        mock_typewrite.assert_called_with("John")

        # Verify enter was pressed to select contact
        mock_press.assert_any_call('enter')

    def test_extract_contact_name(self):
        """Test extracting contact name from command."""
        # Test basic extraction
        result1 = extract_contact_name("call John", "call")
        self.assertEqual(result1, "John")

        # Test with common words to filter
        result2 = extract_contact_name("call to John Doe", "call")
        self.assertEqual(result2, "John Doe")

        # Test with no contact name
        result3 = extract_contact_name("call", "call")
        self.assertEqual(result3, "Unknown")

    def test_extract_file_path(self):
        """Test extracting file path from command."""
        # Test with file path
        result1 = extract_file_path("share file with John /path/to/file.pdf")
        self.assertEqual(result1, "/path/to/file.pdf")

        # Test with different file extension
        result2 = extract_file_path("share file document.doc")
        self.assertEqual(result2, "document.doc")

        # Test without file path
        result3 = extract_file_path("share file with John")
        self.assertIsNone(result3)

    @patch('assistant.whatsapp_integration.subprocess.run')
    def test_send_message_applescript(self, mock_run):
        """Test sending a message using AppleScript."""
        # Configure mock for successful execution
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        result = send_message_applescript("John", "Hello")

        # Verify subprocess was called with AppleScript
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], 'osascript')
        self.assertEqual(args[1], '-e')
        # Script content check (just verify it contains the key elements)
        self.assertTrue("John" in args[2])
        self.assertTrue("Hello" in args[2])

        self.assertEqual(result, "Message sent to John via AppleScript")

    @patch('assistant.whatsapp_integration.subprocess.run')
    def test_send_message_applescript_error(self, mock_run):
        """Test error handling in AppleScript message sending."""
        # Configure mock for failed execution
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "AppleScript error"
        mock_run.return_value = mock_process

        result = send_message_applescript("John", "Hello")

        self.assertEqual(result, "AppleScript error: AppleScript error")


if __name__ == '__main__':
    unittest.main()
