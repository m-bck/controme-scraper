import json
import os
import requests
from Crypto.Cipher import AES
from Crypto.Util import Padding

# LOGGING________________________________________________________________________________
from ..logging_config import configure_logging

logger = configure_logging(__name__)


def encrypt_object(obj: object, key: bytes, filename: str) -> None:
    """Serializes and encrypts an object and saves it to a file.

    Args:
        obj (object): The object to be serialized and encrypted.
        key (bytes): The encryption key to be used.
        filename (str): The name of the file to be saved.

    Returns:
        None
    """
    logger.info("encrypt file %s", filename)
    # Serialize only the session state needed for restoration
    # Build cookies dict safely — if duplicate names exist, keep the last one
    cookies = {}
    for cookie in obj.cookies:
        cookies[cookie.name] = cookie.value
    state = {"cookies": cookies, "headers": dict(obj.headers)}
    obj_bytes: bytes = json.dumps(state).encode("utf-8")
    # Pad the serialized bytes to a multiple of 16 bytes
    padded_bytes: bytes = Padding.pad(obj_bytes, AES.block_size)
    # Encrypt the padded bytes
    iv: bytes = AES.new(key, AES.MODE_CBC).iv
    encryptor: AES.Cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    encrypted_bytes: bytes = encryptor.encrypt(padded_bytes)
    # Save the encrypted bytes to a file with owner-only permissions (mode 0o600)
    fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(iv + encrypted_bytes)


def decrypt_object(key: bytes, filename: str) -> object:
    """Reads an encrypted object from a file, decrypts it, and returns the original object.

    Args:
        key (bytes): The encryption key to be used.
        filename (str): The name of the file to be read.

    Returns:
        object: The decrypted object.
    """
    logger.info("decrypt file %s", filename)
    # Read the encrypted bytes from the file
    with open(filename, "rb") as f:
        ciphertext: bytes = f.read()
    # Extract the IV and encrypted data
    iv: bytes = ciphertext[:16]
    encrypted_data: bytes = ciphertext[16:]
    # Decrypt the padded data
    decryptor: AES.Cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    padded_data: bytes = decryptor.decrypt(encrypted_data)
    # Unpad the padded data
    unpadded_data: bytes = Padding.unpad(padded_data, AES.block_size)
    # Reconstruct the session from the serialized state
    state = json.loads(unpadded_data.decode("utf-8"))
    session = requests.Session()
    session.cookies.update(state["cookies"])
    session.headers.update(state["headers"])
    return session
