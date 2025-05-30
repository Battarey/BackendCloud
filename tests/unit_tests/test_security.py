import pytest
from app.core import security

@pytest.mark.parametrize("password", ["Test1234!", "anotherPass"])
def test_hash_and_verify_password(password):
    hashed = security.hash_password(password)
    assert hashed != password
    assert security.verify_password(password, hashed)
    assert not security.verify_password(password + "x", hashed)
