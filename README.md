# 🎤 Samantha Voice Assistant

A lightweight, modular voice assistant built specifically for macOS (including Apple Silicon). Control browsers, play music, send messages, and automate tasks through natural voice commands.

## ✨ Features

- 🗣️ **Advanced Speech Recognition** using Whisper (tiny model)
- 🔊 **Natural Text-to-Speech** with multiple fallback options
- 🌐 **Browser Control** for any website with intelligent search handling
- 🤖 **Intent Classification** to understand natural language commands
- 🎵 **Media Control** for Spotify and other music players
- 💬 **WhatsApp Integration** for messaging
- ⚙️ **System Automation** for macOS
- 🧩 **Modular & Extensible Architecture**

## 📋 Requirements

- macOS (tested on Apple Silicon)
- Python 3.8+
- Microphone access
- Internet connection (for model download)

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/samantha.git
   cd samantha
   ```

2. Create a virtual environment:
   ```bash
   python -m venv samantha_env
   source samantha_env/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the assistant:
   ```bash
   python main.py
   ```

## 📁 Project Structure

```
samantha/
├── main.py                            # Main entry point
├── requirements.txt                   # Dependencies
├── user_preferences.json              # User settings (created automatically)
├── conversation_history.json          # Log of interactions (created automatically)
└── assistant/
    ├── __init__.py                    # Assistant package initialization
    ├── speech_recognition_service.py  # Speech recognition using Whisper
    ├── tts_service.py                 # Text-to-speech with multiple backends
    ├── browser_control.py             # Browser control implementation
    ├── commands/                      # Command modules
        ├── __init__.py                # Commands package initialization
        └── browser_commands.py        # Browser command handlers
```

## 🧰 Tech Stack

| Component | Technology |
|-----------|------------|
| Speech Recognition | Faster-Whisper (tiny model) |
| Text-to-Speech | Custom service with pyttsx3 & system fallbacks |
| Intent Processing | Custom NLP pipeline |
| Browser Automation | Custom implementation using webbrowser |
| OS Integration | Native macOS commands |

## 🗣️ Voice Commands

Activate Samantha by saying "Hey Samantha" or "Hello Samantha," then try commands like:

- "Open Chrome and search for weather in New York"
- "Play music on Spotify"
- "Send a WhatsApp message to Mom"
- "What's the time?"
- "Set a timer for 5 minutes"
- "Tell me a joke"

## ⚙️ macOS Configuration

For full functionality, grant permissions:

1. **System Settings → Privacy & Security → Accessibility**
   - Grant access to Terminal/iTerm and Python

2. **System Settings → Privacy & Security → Microphone**
   - Grant access to Terminal/iTerm and Python

## 🔧 Troubleshooting

- **Microphone not working?** Check system permissions and try `pip install miniaudio`
- **Text-to-speech issues?** Try `pip install pyobjc` or use system TTS
- **Model download failing?** Try manual download from https://huggingface.co/models

## 🔮 Future Enhancements

- [ ] Integration with calendar and reminders
- [ ] Smart home device control
- [ ] Expanded knowledge base
- [ ] Context-aware conversations
- [ ] Custom voice and personality options

## 👤 Author

**Kartik Garg**
📧 [gargkartik74@gmail.com](mailto:gargkartik74@gmail.com)

## 📜 License

MIT License — See `LICENSE` file for details.
```

This README provides a comprehensive overview of your Samantha voice assistant project, including:

- Clear feature description
- Installation instructions
- Project structure
- Tech stack breakdown
- Voice command examples
- macOS configuration guidance
- Troubleshooting tips
- Future enhancement roadmap

The structure is clean and professional, making it easy for anyone to understand what Samantha does and how to get started with it. The formatting includes appropriate emojis and markdown formatting for improved readability.
