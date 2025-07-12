import re

def detect_intent(command: str) -> str:
    command = command.lower()
    # Prioritize browserautomation for commands about browsers
    if re.search(r'\b(search|open)\b.*\b(brave|chromium|chrome)\b', command):
        return "browserautomation"
    elif re.search(r'\b(open|launch)\b', command):
        return "openapp"
    elif re.search(r'\b(close|quit)\b', command):
        return "closeapp"
    elif re.search(r'\b(search|google|find)\b', command):
        return "websearch"
    elif re.search(r'\b(scrape|extract|get info from)\b', command):
        return "webscraping"
    elif re.search(r'\b(write|story|poem|code|script)\b', command):
        return "creative"
    else:
        return "general"
