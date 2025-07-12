import webbrowser
import time
import re
from urllib.parse import quote_plus

def browser_action(command: str) -> str:
    """
    Enhanced browser control function that can handle complex commands
    for any website and search query.

    Args:
        command: The user's voice command

    Returns:
        Response message describing what was done
    """
    command = command.lower()

    # Handle opening specific browsers
    browser_match = re.search(r"open (brave|chrome|firefox|safari|edge|opera) browser", command)
    browser_type = browser_match.group(1) if browser_match else None

    # Extract website names - look for "open" + website or "go to" + website
    website_pattern = r'(?:open|go to|visit|navigate to)\s+(?:the\s+)?([a-z0-9]+(?:\.[a-z0-9]+)+)(?:\s+|$|\.)'
    website_match = re.search(website_pattern, command)
    website = website_match.group(1) if website_match else None

    # Extract search terms
    search_terms = []
    if "search" in command:
        # Extract all search phrases following "search" or "search for"
        search_parts = re.findall(r'search(?:\s+for)?\s+([^.]+?)(?:\s+in\s+it|$|\s+and\s+|\s+then\s+)', command)
        search_terms = [term.strip() for term in search_parts if term.strip()]

    # Process command based on content
    if browser_type:
        # Map of browser names to their homepage URLs
        browser_urls = {
            "brave": "https://brave.com",
            "chrome": "https://www.google.com",
            "firefox": "https://www.mozilla.org/firefox",
            "safari": "https://www.apple.com/safari",
            "edge": "https://www.microsoft.com/edge",
            "opera": "https://www.opera.com"
        }

        # Open specified browser
        browser_url = browser_urls.get(browser_type, "https://www.google.com")
        webbrowser.open(browser_url)
        response = f"Opening {browser_type.capitalize()} browser."

        # If we have a website specified in the command, open it after browser launch
        if website:
            time.sleep(1.2)  # Give browser time to open
            if not website.startswith(('http://', 'https://')):
                website_url = f"https://{website}"
            else:
                website_url = website

            webbrowser.open(website_url)
            response += f" Navigating to {website}."

            # If search terms are also specified for the website
            if search_terms:
                time.sleep(1)  # Give page time to load
                search_query = search_terms[0]  # Use the first search term

                # Try to construct a reasonable search URL for common sites
                if "google" in website:
                    search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
                elif "youtube" in website:
                    search_url = f"https://www.youtube.com/results?search_query={quote_plus(search_query)}"
                elif "amazon" in website:
                    search_url = f"https://www.amazon.com/s?k={quote_plus(search_query)}"
                elif "bing" in website:
                    search_url = f"https://www.bing.com/search?q={quote_plus(search_query)}"
                elif "yahoo" in website:
                    search_url = f"https://search.yahoo.com/search?p={quote_plus(search_query)}"
                else:
                    # Generic approach for other sites
                    search_url = f"https://www.google.com/search?q={quote_plus(search_query)}+site:{website}"

                webbrowser.open(search_url)
                response += f" Searching for '{search_query}'."

        return response

    # Handle direct website opening without specifying browser
    elif website:
        if not website.startswith(('http://', 'https://')):
            website_url = f"https://{website}"
        else:
            website_url = website

        webbrowser.open(website_url)
        return f"Opening {website}."

    # Handle direct searches without specifying a website
    elif "search" in command and search_terms:
        search_query = search_terms[0]  # Use the first search term
        url = f"https://www.google.com/search?q={quote_plus(search_query)}"
        webbrowser.open(url)
        return f"Searching for '{search_query}' on Google."

    # Fallback for unrecognized commands
    return "I couldn't understand that browser command. Try saying 'open brave browser', 'go to youtube.com', or 'search for cute cats'."

# For backward compatibility
perform_browser_action = browser_action
