import pickle
from Crypto.Cipher import AES
from Crypto.Util import Padding
from typing import Dict, Any

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
    # Serialize the object
    obj_bytes: bytes = pickle.dumps(obj)
    # Pad the serialized bytes to a multiple of 16 bytes
    padded_bytes: bytes = Padding.pad(obj_bytes, AES.block_size)
    # Encrypt the padded bytes
    iv: bytes = AES.new(key, AES.MODE_CBC).iv
    encryptor: AES.Cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    ciphertext: bytes = iv + encryptor.encrypt(padded_bytes)
    # Save the encrypted bytes to a file
    with open(filename, "wb") as f:
        f.write(ciphertext)


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
    # Deserialize the object
    obj: object = pickle.loads(unpadded_data)
    return obj
