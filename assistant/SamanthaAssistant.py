import os
import time
import sys
import threading
import random
import json
import signal
import traceback
from datetime import datetime
from typing import List, Dict, Tuple, Any, Optional
import uuid

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import assistant modules
from assistant.memory_manager import MemoryManager, memory_manager
from assistant.speech_recognition_service import SpeechRecognitionService, speech_recognition_service
from assistant.tts_service import TTSService, tts_service
from assistant.intent_classifier import IntentClassifier, intent_classifier
from assistant.spotify_control import control_spotify
from assistant.browser_control import browser_action
from assistant.whatsapp_integration import whatsapp_action
from assistant.system_prompts import prompt_manager
from assistant.command_processor import CommandProcessor
from assistant.config_manager import config_manager
from assistant.StatusIndicator import StatusIndicator
from assistant.SessionManager import SessionManager
from assistant.SamanthaAssistant import SamanthaAssistant
# Configure logging based on config
import logging
logging_level = config_manager.get('logging.level', 'INFO')
logging_format = config_manager.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(
    level=getattr(logging, logging_level),
    format=logging_format,
    filename=config_manager.get('logging.file_path'),
    filemode='a'
)
logger = logging.getLogger("Samantha")

class SamanthaAssistant:

    def __init__(self):
        """Initialize the voice assistant with configurable settings and improved user experience"""
        print("\n" + "=" * 50)
        logger.info("🤖 Initializing Samantha...")
        print("🤖 Initializing Samantha...")

        # Create session manager for persistence
        self.session_manager = SessionManager()

        # Display initialization spinner for better UX
        self._show_initialization_progress("Starting up")

        # Get configuration values
        self.assistant_name = config_manager.get('assistant.name', 'Samantha')
        self.wake_words = config_manager.get('assistant.wake_words', ["samantha", "hey samantha"])
        self.startup_message = config_manager.get('assistant.startup_message', "Hello! I'm Samantha, your AI assistant.")

        # Initialize speech recognition with configured settings
        self._show_initialization_progress("Loading speech recognition")
        try:
            # Use the singleton instance instead of creating a new one
            self.recognizer = speech_recognition_service
            logger.info("Speech recognition service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize speech recognition: {e}")
            StatusIndicator.show_error(f"Speech recognition initialization failed: {str(e)[:50]}...")
            # Fall back to minimal recognizer
            self.recognizer = self._create_fallback_recognizer()

        # Initialize text-to-speech with configured settings
        self._show_initialization_progress("Setting up text-to-speech")
        try:
            # Use the singleton instance instead of creating a new one
            self.tts_engine = tts_service
            self._configure_tts()
        except Exception as e:
            logger.error(f"Failed to initialize text-to-speech: {e}")
            StatusIndicator.show_error(f"Text-to-speech initialization failed: {str(e)[:50]}...")
            # Fall back to simple print output
            self.tts_engine = None

        # Initialize memory manager with configured settings
        self._show_initialization_progress("Setting up memory")
        try:
            # Use the singleton instance instead of creating a new one
            self.memory = memory_manager
        except Exception as e:
            logger.error(f"Failed to initialize memory manager: {e}")
            StatusIndicator.show_error(f"Memory initialization failed: {str(e)[:50]}...")
            # Create a simple memory object
            self.memory = self._create_fallback_memory()

        # Initialize intent classifier
        self._show_initialization_progress("Loading intent classifier")
        try:
            # Use the singleton instance instead of creating a new one
            # IntentClassifier takes no parameters, so we use the pre-initialized instance
            self.intent_classifier = intent_classifier
        except Exception as e:
            logger.error(f"Failed to initialize intent classifier: {e}")
            StatusIndicator.show_error(f"Intent classifier initialization failed: {str(e)[:50]}...")
            # Fall back to simple intent classifier
            self.intent_classifier = self._create_fallback_classifier()

        # Initialize system prompts with configured directory
        self._show_initialization_progress("Loading system prompts")
        prompts_dir = config_manager.get('system_prompts.directory')
        if prompts_dir:
            prompt_manager.prompts_dir = prompts_dir

        self._init_system_prompts()

        # Initialize the command processor with handlers
        self._show_initialization_progress("Setting up command processor")
        self.command_processor = CommandProcessor()
        self._register_command_handlers()

        # Other initializations...
        self.listening = False
        self.running = True
        self.continuous_mode = self.session_manager.get_setting('continuous_mode', False)
        self.conversation_history = []

        # Load conversation history if available and configured
        if config_manager.get('memory.load_conversation_history', True):
            self._load_conversation_history()

        # Debug mode
        self.debug_mode = config_manager.get('development.debug_mode', False)
        if self.debug_mode:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")

        # Error tracking
        self.error_count = 0
        self.max_consecutive_errors = config_manager.get('error_handling.max_consecutive_errors', 3)

        # Clear the progress indicator
        StatusIndicator.clear_line()
        StatusIndicator.show_success("Initialization complete!")
        print("=" * 50 + "\n")

    def _show_initialization_progress(self, step_message):
        """Show initialization progress with spinners"""
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        for _ in range(3):  # Short animation for each step
            for char in spinner_chars:
                sys.stdout.write(f"\r{char} {step_message}..." + " " * 30)
                sys.stdout.flush()
                time.sleep(0.05)
        print()  # Move to next line for next step

    def _create_fallback_recognizer(self):
        """Create a minimal fallback speech recognizer"""
        class FallbackRecognizer:
            def recognize_speech(self, audio_data=None, timeout=None):
                print("\nFallback speech recognition active (speech recognition unavailable)")
                try:
                    text = input("Type your command: ")
                    return {
                        "success": True,
                        "error": None,
                        "text": text,
                        "confidence": 1.0,
                        "engine": "fallback"
                    }
                except:
                    return {
                        "success": False,
                        "error": "Input error",
                        "text": "",
                        "confidence": 0.0,
                        "engine": "fallback"
                    }

            def _listen(self, timeout: Optional[int] = None):
                """Listen for audio input with configurable timeout and visual feedback"""
                if timeout is None:
                    timeout = config_manager.get('speech_recognition.timeout.default', 5)

                try:
                    listening_thread = threading.Thread(target=StatusIndicator.show_listening, args=(timeout,))
                    listening_thread.daemon = True
                    listening_thread.start()
                    logger.info(f"Listening...")

                    original_timeout=self.recognizer.timeout
                    self.recognizer.timeout = timeout
                    audio_data = self.recognizer._listen()
                    self.recognizer.timeout = original_timeout
                    if audio_data is not None:
                        result = self.recognizer.recognize_speech(audio_data)
                        text = result["text"] if result["success"] else ""
                    else :
                        text = ""
                    StatusIndicator.clear_line()
                    if text:
                        text = text.lower()
                        logger.info(f"User said: {text}")
                        print (f"heard:{text}")
                        self.conversation_history.append({
                            "role": "user",
                            "content": text,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        return text
                    else:
                        print("No audio input detected.")
                    return ""
                except Exception as e:
                    logger.error(f"Error during listening: {e}")
                    StatusIndicator.show_error(f"Listening error: {str(e)[:50]}...")
                    print("Listening failed. Please try again.")
                    return ""

            def start_continuous_listening(self, callback):
                print("Continuous listening not available in fallback mode")
                return False

            def stop_continuous_listening(self):
                return True

        return FallbackRecognizer()

    def _create_fallback_memory(self):
        """Create a minimal fallback memory manager"""
        class FallbackMemory:
            def __init__(self):
                self.user_messages = []
                self.assistant_messages = []

            def add_user_message(self, text):
                self.user_messages.append(text)
                if len(self.user_messages) > 10:
                    self.user_messages.pop(0)

            def add_assistant_message(self, text, action=None):
                self.assistant_messages.append(text)
                if len(self.assistant_messages) > 10:
                    self.assistant_messages.pop(0)

            def add_conversation_entry(self, speaker, text, timestamp=None):
                if speaker == "user":
                    self.add_user_message(text)
                elif speaker == "assistant":
                    self.add_assistant_message(text)

            def get_conversation_context(self):
                return {"recent_exchanges": []}

            def set_context(self, key, value):
                pass

            def get_context(self, key, default=None):
                return default

            def get_user_preferences(self):
                return {}

            def set_user_preference(self, category, key, value):
                pass
        return FallbackMemory()

    def cleanup(self):
        """Clean up resources before exit with user feedback"""
        print("\n" + "=" * 50)
        print("🧹 Cleaning up resources...")

        try:
            # Save session data
            print("📊 Saving session data...")
            self.session_manager.save()

                    # Memory manager doesn't have a cleanup method - remove or replace this
            print("💾 Saving memory...")
                    # Stop speech recognition
            if hasattr(self, 'recognizer') and hasattr(self.recognizer, 'stop_continuous_listening'):
                print("🎤 Stopping speech recognition...")
                self.recognizer.stop_continuous_listening()

            # Save conversation history
            print("📝 Saving conversation history...")
            self._save_conversation_history()

            # Cancel any pending commands call removed - method doesn't exist

            print("✅ Cleanup complete!")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            print(f"❌ Error during cleanup: {str(e)[:100]}")

        print("=" * 50)

    def _create_fallback_classifier(self):
        """Create a minimal fallback intent classifier"""
        class FallbackClassifier:
            def classify(self, text):
                # Very basic keyword matching
                text_lower = text.lower()

                if any(word in text_lower for word in ["spotify", "play", "music", "song"]):
                    return "spotify", 0.8

                elif any(word in text_lower for word in ["browser", "open", "web", "search", "google"]):
                    return "browser", 0.8

                elif any(word in text_lower for word in ["message", "whatsapp", "text", "call"]):
                    return "whatsapp", 0.8

                elif any(word in text_lower for word in ["weather", "temperature", "forecast"]):
                    return "weather", 0.8

                else:
                    return "general", 0.5

            def classify_with_context(self, text, context):
                intent, confidence = self.classify(text)
                return {
                    "intent": intent,
                    "confidence": confidence,
                    "method": "fallback"
                }

        return FallbackClassifier()

    def _init_system_prompts(self):
        """Initialize system prompts for different contexts"""
        try:
            # Default prompts are already set up by the prompt_manager during import
            # But we can add or customize specific prompts here if needed

            # Example: Add custom prompts for specific assistant tasks
            prompt_manager.add_prompt("assistant.greeting", f"You are {self.assistant_name}, a helpful and friendly voice assistant. Respond to greetings warmly and professionally.")
            prompt_manager.add_prompt("assistant.farewell", f"You are {self.assistant_name}, an assistant who cares about the user. Say goodbye in a friendly, warm way.")
            prompt_manager.add_prompt("assistant.multi_step", f"You are processing a multi-step command. Guide the user through each step clearly.")
            prompt_manager.add_prompt("assistant.error", f"You are {self.assistant_name}. Something went wrong. Apologize to the user and suggest alternatives.")
        except Exception as e:
            logger.error(f"Failed to initialize system prompts: {e}")
            StatusIndicator.show_error("Failed to initialize some system prompts")

    def _register_command_handlers(self):
        """Register handlers for different intents with the command processor"""
        # Map intents to categories used in CommandProcessor
        self.command_processor.register_command_handler("Browsing", self.handle_browser_command)
        self.command_processor.register_command_handler("Media", self.handle_spotify_command)
        self.command_processor.register_command_handler("Communication", self.handle_whatsapp_command)
        self.command_processor.register_command_handler("System", self.handle_system_command)
        self.command_processor.register_command_handler("Timer", self.handle_timer_command)
        self.command_processor.register_command_handler("Weather", self.handle_weather_command)
        self.command_processor.register_command_handler("General", self.handle_general_command)
    def process_command(self, text: str):
        """Process user command with enhanced feedback and error handling"""
        if not text:
            return "I didn't catch that.", "no_input"
        # Show thinking indicator
        thinking_thread = threading.Thread(target=StatusIndicator.show_thinking)
        thinking_thread.daemon = True
        thinking_thread.start()
        # Update session activity and metrics
        self.session_manager.update_activity()
        try:
            # Add to memory
            self.memory.add_conversation_entry("user", text)
            # Get conversation context for better understanding
            conversation_context = self.memory.get_conversation_context()
            # Reset consecutive error count on successful command start
            self.error_count = 0
            # Check if we're waiting for confirmation on a multi-step command
            if self.command_processor.is_awaiting_confirmation():
                is_confirm_response, confirmed = CommandProcessor.is_confirmation(text)
                if is_confirm_response:
                    success, message = self.command_processor.handle_confirmation(confirmed)
                    if confirmed:
                        self._speak(message)
                        # Process the next command in the sequence
                        response, result = self.command_processor.process_current_command()
                        self._speak(response)

                        # Check if we need another confirmation
                        if self.command_processor.active_sequence and self.command_processor.active_sequence.requires_confirmation():
                            self._request_next_step_confirmation()
                    else:
                        self._speak(message)
                    return message, "confirmation_handled"

            # Detect intent using the classifier
            # Using the classify method from IntentClassifier instead of classify_with_context
            intent, confidence = self.intent_classifier.classify(text)

            intent_data = {
                "intent": intent,
                "confidence": confidence,
                "method": "classifier"
            }

            # Store current intent in context
            self.memory.set_context("current_intent", intent)
            self.memory.set_context("intent_confidence", confidence)

            # Log the detected intent with method
            method = intent_data.get("method", "unknown")
            logger.info(f"🧠 Detected intent: {intent} (confidence: {confidence:.2f}, method: {method})")

            # Stop the thinking indicator now that we have detected intent
            thinking_thread.join(timeout=0.5)
            StatusIndicator.clear_line()
            command_processor = CommandProcessor()
            steps = command_processor.extract_steps_from_text(text)
            if len(steps) > 1:
                logger.info(f"📋 Multi-step command detected with {len(steps)} steps")
                return self._handle_multi_step_command(steps)

            # For single commands, process directly
            # Get appropriate system prompt for the detected intent
            system_prompt = prompt_manager.get_prompt(f"{intent}.general", {"user_context": conversation_context})
            if not system_prompt:
                system_prompt = prompt_manager.get_prompt("default")

            # Process based on intent
            logger.debug(f"Processing intent: {intent}")
            response = None
            action = None

            # Show feedback about detected intent for better UX
            intent_feedback = self._get_intent_feedback(intent)
            print(f"{intent_feedback}")

            if intent == "browser":
                self.memory.set_context("current_app", "browser")
                response, action = self.handle_browser_command(text, system_prompt)

            elif intent == "spotify":
                self.memory.set_context("current_app", "spotify")
                response, action = self.handle_spotify_command(text, system_prompt)

            elif intent == "whatsapp":
                self.memory.set_context("current_app", "whatsapp")
                response, action = self.handle_whatsapp_command(text, system_prompt)

            elif intent == "system":
                self.memory.set_context("current_app", "system")
                response, action = self.handle_system_command(text, system_prompt)

            elif intent == "timer":
                self.memory.set_context("current_app", "timer")
                response, action = self.handle_timer_command(text, system_prompt)

            elif intent == "weather":
                response, action = self.handle_weather_command(text, system_prompt)

            else:  # general or unknown
                # Handle general conversation
                response = self.generate_conversation_response(text, conversation_context, system_prompt)
                action = "conversation"

            # Add assistant response to memory
            self.memory.add_conversation_entry("assistant", response)

            # Track successful command
            self.session_manager.increment_command_count(success=True)

            # Save session data periodically
            if self.session_manager.command_count % 5 == 0:
                self.session_manager.save()

            # Speak the response
            self._speak(response)

            return response, action

        except Exception as e:
            # Handle errors gracefully
            self.error_count += 1
            self.session_manager.increment_command_count(success=False)

            # Log the error
            logger.error(f"Error processing command: {e}")
            logger.error(traceback.format_exc())

            # Get appropriate error message
            error_prompt = prompt_manager.get_prompt("assistant.error")
            error_message = f"I'm sorry, I encountered an error while processing your request."

            if self.debug_mode:
                error_message += f" Error: {str(e)}"

            # Show error to user
            StatusIndicator.show_error(f"Command processing error: {str(e)[:50]}...")

            # For repeated errors, suggest restart
            if self.error_count >= self.max_consecutive_errors:
                error_message += " I'm having trouble processing commands. You might want to restart me if this continues."

            # Speak the error message
            self._speak(error_message)

            return error_message, "error"

    def _get_intent_feedback(self, intent: str) -> str:
        """Get user-friendly feedback based on intent"""
        intent_icons = {
            "browser": "🌐",
            "spotify": "🎵",
            "whatsapp": "💬",
            "system": "⚙️",
            "timer": "⏲️",
            "weather": "🌤️",
            "general": "💡"
        }

        icon = intent_icons.get(intent, "🔍")
        return f"{icon} Processing {intent} request..."

    def _handle_multi_step_command(self, steps: List[str]):
        """
        Handle multi-step commands using the command processor with enhanced feedback

        Args:
            steps: List of individual command steps
        """
        logger.info(f"🔄 Processing multi-step command with {len(steps)} steps")

        # Print steps for user feedback
        print(f"📋 I'll help you with these {len(steps)} steps:")
        for i, step in enumerate(steps):
            print(f"   {i+1}. {step}")

        # Create a descriptive name for the sequence
        sequence_name = f"Multi-step command ({len(steps)} steps)"

        # Create a command sequence with the steps
        sequence = self.command_processor.create_sequence(
            sequence_name,
            steps,
            require_confirmation=True
        )

        # Queue the sequence for processing
        self.command_processor.queue_sequence(sequence)

        # Announce the multi-step process
        intro_message = f"I'll help you with this {len(steps)}-step task."
        self._speak(intro_message)

        # Process the first command in the sequence with progress indicator
        StatusIndicator.show_thinking(f"Processing step 1 of {len(steps)}", end="\n")
        response, result = self.command_processor.process_current_command()

        # Show completion of first step
        StatusIndicator.show_success(f"Completed step 1 of {len(steps)}")
        self._speak(response)

        # Request confirmation for the next step if needed
        self._request_next_step_confirmation()

        return intro_message, "multi_step_started"

    def _request_next_step_confirmation(self):
        """Request confirmation for the next step if available"""
        # Check if we have an active sequence that requires confirmation
        if (self.command_processor.active_sequence and
            self.command_processor.active_sequence.requires_confirmation()):

            # Get confirmation message
            success, message, next_info = self.command_processor.request_confirmation()

            if success:
                # Format the confirmation request more clearly
                step_num = next_info.get("step_number", "?")
                total_steps = next_info.get("total_steps", "?")
                next_step_text = next_info.get("text", "next step")

                confirmation_message = (
                    f"Ready for step {step_num} of {total_steps}: {next_step_text}\n"
                    f"Should I proceed? (say yes or no)"
                )

                # Show confirmation request with distinct styling
                print("\n" + "-" * 50)
                print(f"❓ {confirmation_message}")
                print("-" * 50)

                self._speak(confirmation_message)

    def handle_browser_command(self, text: str, system_prompt=None) -> Tuple[str, str]:
        """Handle browser-related commands using context-specific system prompts"""
        if system_prompt is None:
            # Determine specific browser task
            if "search" in text.lower():
                task_specific_prompt = prompt_manager.get_prompt("browser.search")
                if task_specific_prompt:
                    system_prompt = task_specific_prompt
            elif "open" in text.lower():
                task_specific_prompt = prompt_manager.get_prompt("browser.navigate")
                if task_specific_prompt:
                    system_prompt = task_specific_prompt
            else:
                system_prompt = prompt_manager.get_prompt("browser.general")

        try:
            # Show feedback during processing
            print("🌐 Working with browser...")

            # Call browser action with the system prompt
            response, action = browser_action(text, system_prompt)

            # Show success feedback
            StatusIndicator.show_success("Browser action completed")
            return response, action
        except Exception as e:
            # Handle errors specific to browser operations
            logger.error(f"Browser action error: {e}")

            # Show error feedback
            StatusIndicator.show_error(f"Browser action failed: {str(e)[:50]}...")

            # Return graceful error message
            error_msg = f"I had trouble with that browser request. {str(e)[:100] if self.debug_mode else 'Please try again.'}"
            return error_msg, "browser_error"

    def handle_spotify_command(self, text: str, system_prompt=None) -> Tuple[str, str]:
        """Handle Spotify commands using context-specific system prompts"""
        # Get user music preferences for personalized recommendations
        user_preferences = self.memory.get_user_preferences().get("music", {})

        if system_prompt is None:
            # Determine specific Spotify task
            if "play" in text.lower() or "start" in text.lower():
                task_type = "playback"
            elif "recommend" in text.lower() or "suggestion" in text.lower():
                task_type = "recommend"
            else:
                task_type = "general"

            # Get context-specific prompt if available
            task_specific_prompt = prompt_manager.get_prompt(f"spotify.{task_type}")
            if task_specific_prompt:
                system_prompt = task_specific_prompt
            else:
                system_prompt = prompt_manager.get_prompt("spotify.general")

        try:
            # Show feedback during processing
            print("🎵 Working with Spotify...")

            # Call Spotify control with the system prompt and user preferences
            response, action = control_spotify(text, system_prompt, user_preferences=user_preferences)

            # Show success feedback
            StatusIndicator.show_success("Spotify action completed")
            return response, action
        except Exception as e:
            # Handle errors specific to Spotify operations
            logger.error(f"Spotify action error: {e}")

            # Show error feedback
            StatusIndicator.show_error(f"Spotify action failed: {str(e)[:50]}...")

            # Return graceful error message
            error_msg = f"I had trouble with that Spotify request. {str(e)[:100] if self.debug_mode else 'Please try again.'}"
            return error_msg, "spotify_error"

    def handle_whatsapp_command(self, text: str, system_prompt=None) -> Tuple[str, str]:
        """Handle WhatsApp commands using context-specific system prompts"""
        if system_prompt is None:
            # Determine specific WhatsApp task
            if "send" in text.lower() or "message" in text.lower():
                task_specific_prompt = prompt_manager.get_prompt("whatsapp.message")
                if task_specific_prompt:
                    system_prompt = task_specific_prompt
            elif "call" in text.lower():
                task_specific_prompt = prompt_manager.get_prompt("whatsapp.call")
                if task_specific_prompt:
                    system_prompt = task_specific_prompt
            else:
                system_prompt = prompt_manager.get_prompt("whatsapp.general")

        try:
            # Show feedback during processing
            print("💬 Working with WhatsApp...")

            # Call WhatsApp action with the system prompt
            response, action = whatsapp_action(text, system_prompt)

            # Show success feedback
            StatusIndicator.show_success("WhatsApp action completed")
            return response, action
        except Exception as e:
            # Handle errors specific to WhatsApp operations
            logger.error(f"WhatsApp action error: {e}")

            # Show error feedback
            StatusIndicator.show_error(f"WhatsApp action failed: {str(e)[:50]}...")

            # Return graceful error message
            error_msg = f"I had trouble with that WhatsApp request. {str(e)[:100] if self.debug_mode else 'Please try again.'}"
            return error_msg, "whatsapp_error"

    def handle_system_command(self, text: str, system_prompt=None) -> Tuple[str, str]:
        """Handle system commands"""
        # Get system-specific prompt based on command content
        if system_prompt is None:
            if any(word in text.lower() for word in ["stop", "quit", "exit", "goodbye"]):
                system_prompt = prompt_manager.get_prompt("assistant.farewell")
                action = "system_exit"
                self.running = False
                response = "Goodbye! Have a great day!"
            else:
                system_prompt = prompt_manager.get_prompt("system.general")
                action = "system_command"
                response = self._handle_assistant_control(text)
        else:
            action = "system_command"
            response = self._handle_assistant_control(text)

        return response, action

    def handle_timer_command(self, text: str, system_prompt=None) -> Tuple[str, str]:
        """Handle timer commands"""
        # Implementation for timer commands
        # This is a placeholder - you would implement the actual timer functionality
        response = "I've set a timer for you."
        action = "timer_set"
        return response, action

    def handle_weather_command(self, text: str, system_prompt=None) -> Tuple[str, str]:
        """Handle weather commands"""
        # Implementation for weather commands
        # This is a placeholder - you would implement the actual weather functionality
        response = "Here's the current weather forecast."
        action = "weather_info"
        return response, action

    def handle_general_command(self, text: str, system_prompt=None) -> Tuple[str, str]:
        """Handle general conversation commands"""
        # Get conversation context
        conversation_context = self.memory.get_conversation_context()

        # Generate response using conversation context
        response = self.generate_conversation_response(text, conversation_context, system_prompt)
        action = "conversation"
        return response, action

    def generate_conversation_response(self, text: str, context: Dict[str, Any], system_prompt: str) -> str:
        """Generate conversational responses using the appropriate system prompt"""
        # This is a placeholder - you would implement the actual LLM response generation
        # Use system_prompt to guide the response generation

        if "name" in text.lower():
            return self._handle_name_setting(text)
        elif any(greeting in text.lower() for greeting in ["hello", "hi", "hey"]):
            return self._handle_greeting(text)
        elif any(word in text.lower() for word in ["time", "date", "day"]):
            return self._handle_time_date(text)
        else:
            return self._handle_general_query(text)

    def _speak(self, text: str):
        """Convert text to speech and add to memory with visual feedback"""
        try:
            # Add to memory
            self.memory.add_conversation_entry("assistant", text)

            # Add to conversation history
            self.conversation_history.append({
                "speaker": "assistant",
                "text": text,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # Show visual speaking indicator
            print(f"\n🗣️ {self.assistant_name}: {text}")

            # Use TTS service to speak if available
            if hasattr(self, 'tts_engine') and self.tts_engine:
                speaking_thread = threading.Thread(target=StatusIndicator.show_speaking)
                speaking_thread.daemon = True
                speaking_thread.start()

                self.tts_engine.speak(text)

                # Small pause after speaking for better interaction rhythm
                time.sleep(0.3)
                StatusIndicator.clear_line()
            else:
                # No TTS engine available - already printed text
                pass

        except Exception as e:
            logger.error(f"❌ Speech error: {e}")
            StatusIndicator.show_error(f"Speech error: {str(e)[:50]}...")

    def listen_for_command(self):
        """Listen for a user command with dynamic VAD and visual feedback"""
        try:
            # Start listening animation
            listening_thread = threading.Thread(target=StatusIndicator.show_listening, args=(5,))
            listening_thread.daemon = True
            listening_thread.start()

            # Start listening with dynamic VAD
            # Modified to use SpeechRecognitionService's _listen and recognize_speech methods
            audio_data = self.recognizer._listen()
            if audio_data is not None:
                result = self.recognizer.recognize_speech(audio_data)
                text = result["text"] if result["success"] else ""
            else:
                text = ""

            # Clear listening indicator
            StatusIndicator.clear_line()

            # Process the recognized text
            if text:
                # Log what was heard
                print(f"👂 Heard: {text}")

                # Check for wake word in continuous mode
                if not self.continuous_mode and not self._is_wake_word(text.lower()):
                    print(f"🔹 Wake word not detected")
                    return False

                # Remove wake word from command if present
                command = self._remove_wake_word(text)

                # Process the command if not empty
                if command:
                    self.process_command(command)
                    return True
                else:
                    print("🔸 No command after wake word")

            else:
                print("🔸 No speech detected")

            return False

        except Exception as e:
            logger.error(f"❌ Error in listen_for_command: {e}")
            StatusIndicator.show_error(f"Listening error: {str(e)[:50]}...")
            return False

    def _is_wake_word(self, text: str) -> bool:
        """Check if wake word is in the text"""
        for wake_word in self.wake_words:
            if wake_word in text:
                return True
        return False

    def _remove_wake_word(self, text: str) -> str:
        """Remove wake word from the text"""
        text_lower = text.lower()
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                # Remove wake word and trim whitespace
                return text_lower.replace(wake_word, "").strip()
        return text

    def start_continuous_mode(self):
        """Start continuous listening mode with the enhanced VAD"""
        if self.continuous_mode:
            return

        self.continuous_mode = True
        # Save in session settings
        self.session_manager.set_setting('continuous_mode', True)
        self._speak("Continuous listening mode activated. You can speak directly without using my wake word.")

        def command_callback(text_result):
            if text_result["success"] and text_result["text"]:
                # Show what was heard
                text = text_result["text"]
                print(f"👂 Heard: {text}")

                # Process the command directly
                self.process_command(text)

        # Start continuous listening with enhanced VAD
        try:
            self.recognizer.start_continuous_listening(command_callback)
            StatusIndicator.show_success("Continuous listening started")
        except Exception as e:
            logger.error(f"Failed to start continuous mode: {e}")
            StatusIndicator.show_error(f"Failed to start continuous mode: {str(e)[:50]}...")
            self.continuous_mode = False
            self.session_manager.set_setting('continuous_mode', False)

    def _configure_tts(self):
        """Configure text-to-speech settings from config"""
        try:
            # Get TTS configuration
            tts_config = config_manager.get_section('tts')
            voice_config = tts_config.get('voice', {})
            preferred_gender = voice_config.get('gender', 'female')
            preferred_names = voice_config.get('preferred_names', ['zira', 'susan', 'samantha'])

            # Set voice properties
            voices = self.tts_engine.get_available_voices()
            if voices:
                # First try to match both gender and name
                voice_set = False
                for voice in voices:
                    voice_name = voice.get('name', '').lower()
                    if (preferred_gender in voice_name and
                        any(name in voice_name for name in preferred_names)):
                        self.tts_engine.set_voice(voice.get('id'))
                        voice_set = True
                        break

                # Then try to match just gender
                if not voice_set:
                    for voice in voices:
                        if preferred_gender in voice.get('name', '').lower():
                            self.tts_engine.set_voice(voice.get('id'))
                            voice_set = True
                            break

                # Use first available voice as fallback
                if not voice_set and voices:
                    self.tts_engine.set_voice(voices[0].get('id'))

            # Set speech rate and volume
            self.tts_engine.set_rate(tts_config.get('rate', 180))
            self.tts_engine.set_volume(tts_config.get('volume', 0.8))

        except Exception as e:
            logger.warning(f"⚠️ TTS configuration warning: {e}")

    def _listen(self, timeout: Optional[int] = None):
        """Listen for audio input with configurable timeout and visual feedback"""
        if timeout is None:
            timeout = config_manager.get('speech_recognition.timeout.default', 5)

        try:
            # Show listening animation
            listening_thread = threading.Thread(target=StatusIndicator.show_listening, args=(timeout,))
            listening_thread.daemon = True
            listening_thread.start()

            logger.info("🎤 Listening...")

            # Modified to use SpeechRecognitionService methods
            audio_data = self.recognizer._listen()
            if audio_data is not None:
                result = self.recognizer.recognize_speech(audio_data)
                text = result["text"] if result["success"] else ""
            else:
                text = ""

            # Clear listening indicator
            StatusIndicator.clear_line()

            if text:
                text = text.lower()
                logger.info(f"👤 User said: {text}")
                print(f"👂 Heard: {text}")

                # Add to conversation history
                self.conversation_history.append({
                    "speaker": "user",
                    "text": text,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                return text
            else:
                print("🔸 No speech detected")
            return ""

        except Exception as e:
            logger.error(f"❌ Listening error: {e}")
            StatusIndicator.show_error(f"Listening error: {str(e)[:50]}...")
            return ""

    def _check_wake_word(self, text: str) -> bool:
        """Check if the text contains a wake word"""
        text_lower = text.lower().strip()
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                return True
        return False

    def _handle_name_setting(self, text: str):
        """Extract and store user's name"""
        name = ""

        if "my name is" in text.lower():
            name = text.lower().split("my name is", 1)[1].strip()
        elif "call me" in text.lower():
            name = text.lower().split("call me", 1)[1].strip()

        if name:
            # Store in user preferences
            self.memory.set_user_preference("personal", "name", name)
            # Also save in session data
            self.session_manager.set_state("user_name", name)
            return f"Nice to meet you, {name}. I'll remember that."

        return "I didn't catch your name. Could you please repeat it?"

    def _handle_greeting(self, command: str) -> str:
        """Handle greeting commands"""
        # Use the greeting-specific system prompt
        greeting_prompt = prompt_manager.get_prompt("assistant.greeting")

        # Get user name if available for personalized greeting
        user_name = self.session_manager.get_state("user_name") or self.memory.get_context("user_name")

        greetings = [
            f"Hello{' ' + user_name if user_name else ''}! How can I help you today?",
            f"Hi there{' ' + user_name if user_name else ''}! What can I do for you?",
            f"Hey{' ' + user_name if user_name else ''}! I'm here to assist you.",
            f"Hello{' ' + user_name if user_name else ''}! Ready to help with Spotify, browser, or WhatsApp tasks!"
        ]
        return random.choice(greetings)

    def _handle_goodbye(self, command: str) -> str:
        """Handle goodbye commands"""
        # Use the farewell-specific system prompt
        farewell_prompt = prompt_manager.get_prompt("assistant.farewell")

        # Get user name if available for personalized farewell
        user_name = self.session_manager.get_state("user_name") or self.memory.get_context("user_name")

        self.running = False

        farewells = [
            f"Goodbye{' ' + user_name if user_name else ''}! Have a great day!",
            f"See you later{' ' + user_name if user_name else ''}!",
            f"Take care{' ' + user_name if user_name else ''}! Call me if you need anything.",
            f"Bye{' ' + user_name if user_name else ''}! It was nice talking to you."
        ]

        return random.choice(farewells)

    def _handle_assistant_control(self, command: str) -> str:
        """Handle assistant control commands with improved feedback"""
        command_lower = command.lower()

        if any(word in command_lower for word in ["stop listening", "stop", "quiet", "shut up"]):
            self.listening = False
            if self.continuous_mode:
                self.continuous_mode = False
                self.session_manager.set_setting('continuous_mode', False)
                if hasattr(self.recognizer, 'stop_continuous_listening'):
                    self.recognizer.stop_continuous_listening()
                StatusIndicator.show_success("Continuous listening mode deactivated")
            return "I'll stop listening now. Say 'Hey Samantha' to wake me up again."

        elif any(word in command_lower for word in ["what can you do", "help", "capabilities"]):
            help_text = """I can help you with:
            🎵 Spotify: Play, pause, next, previous, volume control, playlists, liked songs
            🌐 Browser: Open websites, search, navigate
            💬 WhatsApp: Send messages, make calls, share files
            ⏰ Time and date queries
            📋 Multi-step commands: Perform sequences of actions
            Just say 'Hey Samantha' followed by your request!"""

            # Print help text with better formatting
            print("\n" + "=" * 50)
            print("🤖 CAPABILITIES:")
            print(help_text)
            print("=" * 50 + "\n")

            return "I can help with music control, web browsing, messaging, and more. You can also ask me to perform multi-step tasks."

        elif any(word in command_lower for word in ["volume up", "speak louder"]):
            current_volume = self.tts_engine.volume
            new_volume = min(1.0, current_volume + 0.1)
            self.tts_engine.set_volume(new_volume)

            # Save volume setting in session
            self.session_manager.set_setting('tts_volume', new_volume)

            StatusIndicator.show_success(f"Volume increased to {new_volume:.1f}")
            return "I'll speak louder now."

        elif any(word in command_lower for word in ["volume down", "speak quieter"]):
            current_volume = self.tts_engine.volume
            new_volume = max(0.1, current_volume - 0.1)
            self.tts_engine.set_volume(new_volume)

            # Save volume setting in session
            self.session_manager.set_setting('tts_volume', new_volume)

            StatusIndicator.show_success(f"Volume decreased to {new_volume:.1f}")
            return "I'll speak more quietly now."

        elif any(word in command_lower for word in ["listen continuously", "continuous mode"]):
            self.continuous_mode = True
            self.session_manager.set_setting('continuous_mode', True)

            self.start_continuous_mode()
            StatusIndicator.show_success("Continuous listening mode activated")
            return "I'm now in continuous listening mode. You can speak commands without saying my wake word first."

        elif any(word in command_lower for word in ["cancel task", "stop task", "cancel command"]):
            # Cancel the active command sequence
            message = self.command_processor.cancel_all()

            StatusIndicator.show_success("Tasks cancelled")
            return message

        elif "status" in command_lower or "how are you" in command_lower:
            # Return assistant status info
            uptime = datetime.now() - self.session_manager.start_time
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            status = f"I'm running well! Uptime: {hours}h {minutes}m. "
            status += f"I've processed {self.session_manager.command_count} commands "
            status += f"with {self.session_manager.session_data['metrics'].get('errors', 0)} errors."

            return status

        else:
            return "I'm here and listening! How can I help you?"

    def _handle_time_date(self, command: str) -> str:
        """Handle time and date queries"""
        now = datetime.now()
        command_lower = command.lower()

        if "time" in command_lower:
            current_time = now.strftime("%I:%M %p")
            return f"The current time is {current_time}"

        elif "date" in command_lower:
            current_date = now.strftime("%A, %B %d, %Y")
            return f"Today is {current_date}"

        else:
            current_datetime = now.strftime("%I:%M %p on %A, %B %d, %Y")
            return f"It's currently {current_datetime}"

    def _handle_general_query(self, command: str) -> str:
        """Handle general queries"""
        # Get a general-purpose system prompt
        general_prompt = prompt_manager.get_prompt("default")

        responses = [
            "That's an interesting question! I'm focused on helping with Spotify, browser, and WhatsApp tasks right now.",
            "I'm still learning about that topic. For now, I can help with music, web browsing, and messaging.",
            "I don't have information about that yet, but I can help you with Spotify controls, web browsing, or WhatsApp!"
        ]
        return random.choice(responses)

    def _save_conversation_history(self):
        """Save the conversation history to a JSON file with user feedback"""
        try:
            # Get history file path from config
            history_file = config_manager.get('memory.conversation_history_file', 'conversation_history.json')

            with open(history_file, "w") as f:
                json.dump(self.conversation_history, f, indent=2)

            logger.info(f"Conversation history saved to {history_file}")
        except Exception as e:
            logger.error(f"❌ Error saving conversation history: {e}")
            StatusIndicator.show_error(f"Failed to save conversation history: {str(e)[:50]}...")

    def _load_conversation_history(self):
        """Load conversation history from file if available"""
        try:
            # Get history file path from config
            history_file = config_manager.get('memory.conversation_history_file', 'conversation_history.json')

            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    self.conversation_history = json.load(f)

                # Limit the history size if needed
                max_history = config_manager.get('memory.max_conversation_length', 100)
                if len(self.conversation_history) > max_history:
                    self.conversation_history = self.conversation_history[-max_history:]

                logger.info(f"Loaded {len(self.conversation_history)} conversation entries from history")
        except Exception as e:
            logger.error(f"Failed to load conversation history: {e}")
            self.conversation_history = []

    def cleanup(self):
        """Clean up resources before exit with user feedback"""
        print("\n" + "=" * 50)
        print("🧹 Cleaning up resources...")

        try:
            # Save session data
            print("📊 Saving session data...")
            self.session_manager.save()

            # Stop speech recognition
            if hasattr(self, 'recognizer') and hasattr(self.recognizer, 'stop_continuous_listening'):
                print("🎤 Stopping speech recognition...")
                self.recognizer.stop_continuous_listening()

            # Save conversation history
            print("📝 Saving conversation history...")
            self._save_conversation_history()

            # Cancel any pending commands call removed - method doesn't exist

            print("✅ Cleanup complete!")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            print(f"❌ Error during cleanup: {str(e)[:100]}")

        print("=" * 50)

    def _signal_handler(self, sig, frame):
        """Handle program termination signals with feedback"""
        print("\n👋 Shutting down Samantha...")
        self.running = False
        self.cleanup()
        sys.exit(0)

    def run(self):
        """Main loop for the voice assistant with improved feedback"""
        # Set up signal handler for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Show start banner
        print("\n" + "=" * 50)
        print(f"🚀 {self.assistant_name} Voice Assistant v{config_manager.get('assistant.version', '1.0.0')}")
        print(f"🗓️  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 User: {os.getlogin()}")
        print("=" * 50 + "\n")

        # Greet with startup message
        startup_message = config_manager.get('assistant.startup_message', f"Hello! I'm {self.assistant_name}, your AI assistant.")

        # If voice is enabled at startup, speak the greeting
        if config_manager.get('assistant.speak_greeting', True):
            self._speak(startup_message)

        # Restore volume setting from session if available
        if hasattr(self, 'tts_engine') and self.tts_engine:
            saved_volume = self.session_manager.get_setting('tts_volume')
            if saved_volume is not None:
                self.tts_engine.set_volume(saved_volume)

        # Restore continuous mode if it was active
        if self.continuous_mode:
            print("🔄 Restoring continuous listening mode...")
            self.start_continuous_mode()

        print("💡 Available commands:")
        print("   🎵 Spotify: 'play music', 'pause', 'next song', 'volume up'")
        print("   🌐 Browser: 'open google', 'search for cats'")
        print("   💬 WhatsApp: 'message John hello', 'call Mom'")
        print("   📋 Multi-step: 'First open YouTube, then search for cooking videos'")
        print("   ⚙️ System: 'volume up/down', 'help', 'status'")
        print("   ❌ Exit: 'goodbye' or Ctrl+C")
        print("-" * 50)
        print(f"\n👂 Say '{self.wake_words[0]}' to begin...\n")

        try:
            while self.running:
                if self.continuous_mode:
                    # In continuous mode, listening happens in a background thread
                    # Just sleep a bit to avoid CPU hogging in the main thread
                    time.sleep(0.5)
                else:
                    # Regular mode - listen for wake word with shorter timeout
                    speech = self._listen(timeout=config_manager.get('speech_recognition.timeout.wake_word', 2))
                    if speech and self._check_wake_word(speech):
                        self.listening = True

                        # Visual feedback for wake word detection
                        StatusIndicator.show_success("Wake word detected!")

                        self._speak("Yes? How can I help you?")

                        # Listen for command with longer timeout
                        command_speech = self._listen(timeout=config_manager.get('speech_recognition.timeout.command', 10))
                        if command_speech:
                            response = self.process_command(command_speech)

                            # If goodbye command was given
                            if not self.running:
                                break
                        else:
                            self._speak("I didn't hear anything. Say 'Hey Samantha' to try again.")

                        self.listening = False

        except KeyboardInterrupt:
            logger.info("\n👋 Goodbye!")
            self._speak("Goodbye!")
        except Exception as e:
            logger.error(f"❌ Assistant error: {e}")
            logger.error(traceback.format_exc())

            StatusIndicator.show_error(f"Critical error: {str(e)[:100]}")
            self._speak("I encountered a critical error and need to shut down. Please check the logs.")
        finally:
            # Clean up resources
            self.cleanup()
