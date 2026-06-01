"""
Pure unit tests for controme_scraper.

No live Controme system required. All external I/O is either exercised through
temp files (encryption roundtrip) or avoided entirely via direct logic testing.
"""

import hashlib
import logging
import os
import pickle
import sys
import tempfile

import pytest
import requests

from controme_scraper.encryption_utils.encryption_utils import decrypt_object, encrypt_object
from controme_scraper.logging_config import configure_logging
from controme_scraper.models import Thermostat


# ---------------------------------------------------------------------------
# 1. AES key derivation
# ---------------------------------------------------------------------------


def _derive_key(user: str, password: str) -> bytes:
    return hashlib.sha256((user + password).encode("utf-8")).digest()


def test_key_is_32_bytes():
    key = _derive_key("user@example.com", "s3cr3t")
    assert len(key) == 32


def test_key_is_deterministic():
    key1 = _derive_key("alice", "hunter2")
    key2 = _derive_key("alice", "hunter2")
    assert key1 == key2


def test_key_changes_with_different_user():
    key_a = _derive_key("alice", "password")
    key_b = _derive_key("bob", "password")
    assert key_a != key_b


def test_key_changes_with_different_password():
    key_a = _derive_key("alice", "password1")
    key_b = _derive_key("alice", "password2")
    assert key_a != key_b


# ---------------------------------------------------------------------------
# 2. Session file location
# ---------------------------------------------------------------------------


def _generate_filename(user: str, password: str) -> str:
    combined_string = user + password
    hashed_string = hashlib.sha256(combined_string.encode("utf-8")).hexdigest()
    return os.path.join(tempfile.gettempdir(), f"controme_{hashed_string}.session")


def test_session_file_is_inside_tempdir():
    path = _generate_filename("user", "pass")
    assert path.startswith(tempfile.gettempdir())


def test_session_file_ends_with_dot_session():
    path = _generate_filename("user", "pass")
    assert path.endswith(".session")


def test_session_file_contains_sha256_of_credentials():
    user, password = "user", "pass"
    expected_hash = hashlib.sha256((user + password).encode("utf-8")).hexdigest()
    path = _generate_filename(user, password)
    assert expected_hash in os.path.basename(path)


def test_session_file_not_in_cwd():
    path = _generate_filename("user", "pass")
    assert not path.startswith(os.getcwd())


# ---------------------------------------------------------------------------
# 3. Encryption / decryption roundtrip
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_roundtrip():
    key = _derive_key("roundtrip_user", "roundtrip_pass")

    original = requests.Session()
    original.cookies.set("sessionid", "abc123")
    original.headers.update({"X-Custom-Header": "test-value"})

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".session")
    tmp.close()
    try:
        encrypt_object(original, key, tmp.name)
        restored = decrypt_object(key, tmp.name)

        assert restored.cookies.get("sessionid") == "abc123"
        assert restored.headers.get("X-Custom-Header") == "test-value"
    finally:
        os.unlink(tmp.name)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file permissions not applicable on Windows")
def test_encrypted_file_has_owner_only_permissions():
    key = _derive_key("perm_user", "perm_pass")
    session = requests.Session()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".session")
    tmp.close()
    try:
        encrypt_object(session, key, tmp.name)
        mode = oct(os.stat(tmp.name).st_mode & 0o777)
        assert mode == oct(0o600)
    finally:
        os.unlink(tmp.name)


# ---------------------------------------------------------------------------
# 4. Backward compatibility: old pickle session files fail gracefully
# ---------------------------------------------------------------------------


def test_decrypt_raises_on_pickle_bytes():
    key = _derive_key("any_user", "any_pass")

    # Write raw pickle bytes that are not a valid AES-encrypted JSON payload.
    # After AES decryption the result will not be valid JSON, so json.loads raises.
    pickle_bytes = pickle.dumps({"some": "old-format"})

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".session")
    tmp.close()
    try:
        with open(tmp.name, "wb") as f:
            # Prepend 16 bytes of fake IV so decrypt_object won't fail reading the IV slice
            f.write(b"\x00" * 16 + pickle_bytes)

        with pytest.raises(Exception):
            decrypt_object(key, tmp.name)
    finally:
        os.unlink(tmp.name)


# ---------------------------------------------------------------------------
# 5. Thermostat.is_battery_powered
# ---------------------------------------------------------------------------


def _make_thermostat(**kwargs) -> Thermostat:
    defaults = {"device_id": "RFAktor*1"}
    defaults.update(kwargs)
    return Thermostat(**defaults)


def test_is_battery_powered_batterie_german():
    t = _make_thermostat(power_source="Batterie")
    assert t.is_battery_powered is True


def test_is_battery_powered_lowercase():
    t = _make_thermostat(power_source="batterie")
    assert t.is_battery_powered is True


def test_is_battery_powered_festanschluss():
    t = _make_thermostat(power_source="Festanschluss")
    assert t.is_battery_powered is False


def test_is_battery_powered_none():
    t = _make_thermostat(power_source=None)
    assert t.is_battery_powered is False


# ---------------------------------------------------------------------------
# 6. configure_logging installs NullHandler by default
# ---------------------------------------------------------------------------


def test_configure_logging_returns_logger_with_handler():
    logger = configure_logging("test.unit.module_a")
    assert len(logger.handlers) >= 1


def test_configure_logging_handler_is_null_handler():
    logger = configure_logging("test.unit.module_b")
    assert any(isinstance(h, logging.NullHandler) for h in logger.handlers)


def test_configure_logging_no_duplicate_handlers():
    name = "test.unit.module_c"
    configure_logging(name)
    configure_logging(name)
    logger = logging.getLogger(name)
    null_handlers = [h for h in logger.handlers if isinstance(h, logging.NullHandler)]
    assert len(null_handlers) == 1


def test_configure_logging_no_stream_handler_by_default():
    logger = configure_logging("test.unit.module_d")
    assert not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.NullHandler) for h in logger.handlers)
