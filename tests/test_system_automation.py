from assistant.system_automation import system_action

def test_open_app():
    command = "open Spotify"
    response = system_action(command)
    assert response == "Opening Spotify."

def test_close_app():
    command = "close Spotify"
    response = system_action(command)
    assert response == "Closing Spotify."

def test_invalid_system_action():
    command = "random system command"
    response = system_action(command)
    assert response == "System command not recognized."
