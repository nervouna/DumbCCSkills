from {{project_name_snake}} import greet


def test_greet_default():
    assert greet() == "Hello, World!"


def test_greet_custom():
    assert greet("Claude") == "Hello, Claude!"
