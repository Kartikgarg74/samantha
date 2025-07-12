from assistant.browser_control import perform_browser_action

def test_browser_action_search():
    command = "search for Brave browser"
    response = perform_browser_action(command)
    assert "Searching for 'Brave browser' on Google." in response

def test_browser_action_open():
    command = "open brave"
    response = perform_browser_action(command)
    assert "Opening Brave Browser." in response

def test_invalid_browser_action():
    command = "random browser command"
    response = perform_browser_action(command)
    assert "Browser command not recognized." in response
