#!/usr/bin/env python3
"""
Generate an Ed25519 key pair for the KMS service.
Run once before first deployment:
    python scripts/generate_keys.py

Outputs:
    kms/keys/private.pem  — Ed25519 private key (PEM, keep secret!)
    kms/keys/public.pem   — Ed25519 public key  (PEM, share with devices for verification)
"""
import sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("ERROR: 'cryptography' library not installed. Run: pip install cryptography")
    sys.exit(1)

KEYS_DIR = Path(__file__).parent.parent / "kms" / "keys"
PRIVATE_KEY_PATH = KEYS_DIR / "private.pem"
PUBLIC_KEY_PATH = KEYS_DIR / "public.pem"


def generate():
    KEYS_DIR.mkdir(parents=True, exist_ok=True)

    if PRIVATE_KEY_PATH.exists():
        print(f"[!] Private key already exists at {PRIVATE_KEY_PATH}")
        print("    Delete it manually if you want to regenerate (this will invalidate all existing signatures).")
        sys.exit(1)

    # Generate using OS CSPRNG (Ed25519PrivateKey.generate() uses os.urandom internally)
    private_key = Ed25519PrivateKey.generate()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    PRIVATE_KEY_PATH.write_bytes(private_pem)
    # Restrict permissions: owner read-only
    PRIVATE_KEY_PATH.chmod(0o400)

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    PUBLIC_KEY_PATH.write_bytes(public_pem)
    PUBLIC_KEY_PATH.chmod(0o644)

    print(f"[+] Private key → {PRIVATE_KEY_PATH}  (chmod 400)")
    print(f"[+] Public key  → {PUBLIC_KEY_PATH}")
    print()
    print("IMPORTANT: Keep private.pem secret. Distribute public.pem to devices for signature verification.")


if __name__ == "__main__":
    generate()
