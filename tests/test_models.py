from tests.models import User


def test_abstract_user_str():
    user = User(username="username")
    assert str(user) == user.username
