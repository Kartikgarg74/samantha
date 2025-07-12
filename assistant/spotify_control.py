
def control_spotify(command: str) -> str:
    command = command.lower()
    if "play" in command:
        return "Playing Spotify track."
    elif "pause" in command:
        return "Pausing Spotify track."
    elif "next" in command:
        return "Skipping to next track."
    elif "previous" in command:
        return "Going back to previous track."
    elif "stop" in command:
        return "Stopping Spotify playback."
    elif "volume up" in command:
        return "Increasing Spotify volume."
    elif "volume down" in command:
        return "Decreasing Spotify volume."
    elif "search for" in command:
        query = command.split("search for", 1)[1].strip()
        return f"Searching for '{query}' on Spotify."
    elif "add to playlist" in command:
        track = command.split("add to playlist", 1)[1].strip()
        return f"Adding '{track}' to your Spotify playlist."
    else:
        return "Spotify command not recognized."
