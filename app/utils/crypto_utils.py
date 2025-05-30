from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os

BLOCK_SIZE = 128

# Generates a random key for encryption (32 bytes)
def generate_key() -> bytes:
    return os.urandom(32)

# Encrypts data using AES (CBC, PKCS7 padding)
def encrypt_data(
    data: bytes, 
    key: bytes, 
    iv: bytes
) -> bytes:
    padder = padding.PKCS7(BLOCK_SIZE).padder()
    padded_data = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(padded_data) + encryptor.finalize()

# Decrypts data encrypted with AES (CBC, PKCS7 padding)
def decrypt_data(
    encrypted_data: bytes, 
    key: bytes, 
    iv: bytes
) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
    unpadder = padding.PKCS7(BLOCK_SIZE).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()
