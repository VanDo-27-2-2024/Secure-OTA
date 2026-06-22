import logging
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

logger = logging.getLogger(__name__)

# Private key lives inside the container — never exposed outside KMS service
_KEY_PATH = Path(__file__).parent.parent / "keys" / "private.pem"


def _load_private_key() -> Ed25519PrivateKey:
    """Load Ed25519 private key from PEM file. Fail fast if key is missing."""
    if not _KEY_PATH.exists():
        raise RuntimeError(
            f"Private key not found at {_KEY_PATH}. "
            "Run scripts/generate_keys.py to generate a key pair."
        )
    pem_data = _KEY_PATH.read_bytes()
    key = serialization.load_pem_private_key(pem_data, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise RuntimeError("Key file does not contain an Ed25519 private key")
    return key


# Load key once at module import — fail fast on startup if missing
_private_key = _load_private_key()


def sign(data_hex: str) -> str:
    """
    Sign hex-encoded data with the Ed25519 private key.
    Returns hex-encoded signature.
    The private key never leaves this KMS process.
    """
    try:
        data_bytes = bytes.fromhex(data_hex)
    except ValueError as exc:
        raise ValueError(f"Invalid hex input: {exc}") from exc

    signature = _private_key.sign(data_bytes)
    return signature.hex()
