Thanks for sharing your current `README.md` — it's already clean and well-structured. Based on your full project scope and updated directory structure, here’s a **refined and more complete version** of your README that adds:

* 📁 Folder structure for clarity
* 🧪 Testing guide
* ⚠️ macOS and Apple Silicon tips
* ✅ Environment variable and virtual environment tips
* 📋 Contribution section (optional if you're working solo now)

You can **copy-paste this directly** into your `README.md` file and adapt GitHub URL or any field later.

---

```markdown
# 🧠 AI Personal Assistant for macOS (Apple Silicon)

An AI-powered personal assistant built specifically for macOS with Apple Silicon. It automates tasks such as browser control, app switching, WhatsApp messaging, Spotify control, and deep web search — all through voice or text commands.

---

## 🚀 Key Features

- 🖥️ **System Automation**
  Open/close apps, simulate keystrokes and mouse clicks, switch between windows.

- 🌐 **Brave Browser Control**
  Tab management, web search, navigation, and incognito mode control.

- 💬 **WhatsApp Desktop Control**
  Open chats, send messages, and **(coming soon)** handle calls.

- 🎵 **Spotify Playback Control**
  Play, pause, skip, and search songs/playlists on the desktop app.

- 🔍 **Web Search Module**
  Deep contextual web scraping and summarization via natural language.

- 🧠 **Intent Classification**
  Uses `microsoft/dialogp-small` to parse and route user instructions.

- 🧩 **Modular & Extendable Architecture**

---

## 🧰 Tech Stack

| Category         | Tools Used                                         |
|------------------|----------------------------------------------------|
| Language         | Python 3.12+                                       |
| ML Model         | Microsoft/Dialogp-small (local, 500MB)             |
| Voice/Text Input | Pyttsx3, SoundDevice *(no PyAudio)*                |
| Automation       | PyAutoGUI, AppleScript, Selenium                   |
| Web Scraping     | Requests, BeautifulSoup                            |
| Testing          | Pytest                                             |
| OS               | macOS (Apple Silicon - M1/M2/M3)                   |

---

## 📁 Folder Structure

```

personal-assistant/
├── assistant/                    # Core logic modules
│   ├── browser\_control.py       # Brave browser control
│   ├── system\_automation.py     # macOS app & system control
│   ├── whatsapp\_integration.py  # WhatsApp Desktop automation
│   ├── spotify\_control.py       # Spotify automation
│   ├── web\_search.py            # Deep search and scraping
│   ├── intent\_classifier.py     # NLU model wrapper
│   └── gui\_interface.py         # (Optional) GUI elements
├── data/
│   └── interaction\_logs.json    # Log of assistant interactions
├── tests/
│   ├── test\_browser\_control.py
│   ├── test\_system\_automation.py
│   └── test\_intent\_classifier.py
├── Dockerfile
├── requirements.txt
├── main.py                      # Entry point
├── README.md

````

---

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-personal-assistant.git
   cd ai-personal-assistant
````

2. (Recommended) Create a virtual environment:

   ```bash
   python3 -m venv samantha_env
   source samantha_env/bin/activate
   ```

3. Install all dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the assistant:

   ```bash
   python main.py
   ```

---

## 🧪 Running Tests

```bash
pytest tests/
```

Make sure you have `pytest` installed:

```bash
pip install pytest
```

---

## 🐳 Docker Support (Optional)

Build the container:

```bash
docker build -t ai-personal-assistant .
```

Run it:

```bash
docker run -it ai-personal-assistant
```

> ⚠️ Note: macOS GUI apps (like WhatsApp, Brave) are not fully Docker-compatible. Docker support is best for headless testing or future API-based features.

---

## 📅 Future Enhancements

* [ ] Add Whisper STT for accurate voice control.
* [ ] Memory module for user-specific context.
* [ ] Email, calendar, and Zoom integrations.
* [ ] CLI & GUI hybrid interface.
* [ ] Scheduled task execution and smart reminders.

---

## ⚙️ macOS Notes

* Make sure **System Accessibility** is enabled for automation.
* Go to **System Settings → Privacy & Security → Accessibility**, and grant access to:

  * Terminal / iTerm / VSCode (if using)
  * Python interpreter
* If using `osascript`, ensure correct AppleScript syntax for launching and switching apps.

---

## 🤝 Contribution

Feel free to fork the repo and submit PRs if you'd like to contribute!
Open issues for bugs, feature suggestions, or questions.

---

## 👤 Author

**Kartik Garg**
📧 [gargkartik74@gmail.com](mailto:gargkartik74@gmail.com)

---

## 📜 License

MIT License — See `LICENSE` file for details.
