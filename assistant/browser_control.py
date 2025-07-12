import webbrowser
def perform_browser_action(command: str) -> str:
    command = command.lower()
    if "search" in command:
        query = command.split("search", 1)[1].strip()
        # Clean up the query string (remove unnecessary words like "for")
        query = query.replace("for", "").strip()
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching for '{query}' on Google."
    elif "open brave" in command:
        webbrowser.open("https://brave.com")
        return "Opening Brave Browser."
    else:
        return "Browser command not recognized."
