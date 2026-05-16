from __future__ import annotations

import base64
import hashlib

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from configs import dify_config


class TeamModelEncryptionError(Exception):
    pass


def _build_key() -> bytes:
    encryption_key = (dify_config.ENCRYPTION_KEY or "").strip()
    if not encryption_key:
        raise TeamModelEncryptionError("ENCRYPTION_KEY is not configured.")

    return hashlib.sha256(encryption_key.encode("utf-8")).digest()


def encrypt_api_key(api_key: str) -> str:
    if not api_key:
        raise TeamModelEncryptionError("API key cannot be empty.")

    cipher = AES.new(_build_key(), AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(api_key.encode("utf-8"))
    payload = cipher.nonce + tag + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt_api_key(encrypted_value: str) -> str:
    if not encrypted_value:
        raise TeamModelEncryptionError("Encrypted API key cannot be empty.")

    try:
        payload = base64.b64decode(encrypted_value)
        nonce, tag, ciphertext = payload[:16], payload[16:32], payload[32:]
        cipher = AES.new(_build_key(), AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")
    except Exception as exc:
        raise TeamModelEncryptionError("Failed to decrypt API key.") from exc
