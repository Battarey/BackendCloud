import pytest
from app.core import encryption

@pytest.mark.parametrize("data", [b"test data", b"1234567890", b"ascii text"])
def test_encrypt_decrypt(data):
    password = "testpass"
    encrypted, salt, iv = encryption.encrypt_file(data, password)
    assert encrypted != data
    decrypted = encryption.decrypt_file(encrypted, password, salt, iv)
    assert decrypted == data
