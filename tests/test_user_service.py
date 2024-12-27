"""
A test for the user service.
"""

from configuration.container import ServerContainer
from auth.auth import UserCredential

container = ServerContainer()
config_service = container.config_service()
config_service.load_yaml_config("tests/test-config.yaml")


def test_create_user():
    """
    Create a user
    """
    user_service = container.user_service()
    user_service.reset()
    user = UserCredential(username="test", password="password")
    user_service.create_user(user.username, user.password)
    user_service.write()

    user_service.read()
    assert user_service.find_user("test") == user
    assert user_service.find_user("test").password == "password"
    assert user_service.find_user("test").username == "test"


def test_update_user():
    """
    Update a user
    """
    user_service = container.user_service()
    user_service.reset()
    user_service.create_user("test", "password")
    user = user_service.find_user("test")
    user.password = "newpassword"
    user_service.update_user(user)

    user_service.read()
    assert user_service.find_user("test") == user
    assert user_service.find_user("test").password == "newpassword"
    assert user_service.find_user("test").username == "test"


def test_random_password():
    """
    Test that the random password generator works
    """
    user_service = container.user_service()
    user_service.reset()
    user_service.create_user("test", "password")

    user_service.read()
    assert user_service.find_user("test").password == "password"
    assert user_service.find_user("test").username == "test"
    user_service.random_password("test")
    assert user_service.find_user("test").password != "password"


def test_delete_user():
    """
    Test that the user can be removed
    """
    user_service = container.user_service()
    user_service.reset()
    user_service.create_user("test", "password")

    user_service.read()
    assert user_service.find_user("test").password == "password"
    assert user_service.find_user("test").username == "test"
    user_service.delete_user("test")
    assert user_service.find_user("test") is None
