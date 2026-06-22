import os
import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

# Resolve and store the canonical storage root path once at startup
_STORAGE_ROOT = Path(settings.storage_base_path).resolve()


def _safe_resolve(path: str) -> Path:
    """
    Resolve a path and verify it stays within the storage root.
    Raises ValueError on path traversal attempts.
    Security: prevents ../../../etc/passwd style attacks.
    """
    resolved = Path(path).resolve()
    # Enforce trailing sep to prevent partial prefix match bypass
    # e.g. /storage-evil would bypass a plain startswith("/storage") check
    storage_root_str = str(_STORAGE_ROOT) + os.sep
    resolved_str = str(resolved)
    if not (resolved_str + os.sep).startswith(storage_root_str) and resolved_str != str(_STORAGE_ROOT):
        raise ValueError(f"Path traversal detected: {path!r}")
    return resolved


def firmware_dir(version: str) -> Path:
    """Return the directory path for a given firmware version."""
    # Use only the version string — never trust user-supplied filenames
    safe_version = version.replace("/", "_").replace("..", "_")
    return _STORAGE_ROOT / "firmware" / safe_version


def save_firmware(version: str, bin_data: bytes, sig_hex: str) -> tuple[str, str]:
    """
    Persist firmware binary and signature to disk.
    Returns (file_path, signature_path) as strings.
    """
    fw_dir = firmware_dir(version)
    fw_dir.mkdir(parents=True, exist_ok=True)

    bin_path = fw_dir / "firmware.bin"
    sig_path = fw_dir / "firmware.sig"

    # Validate resolved paths are within storage root before writing
    _safe_resolve(str(bin_path))
    _safe_resolve(str(sig_path))

    bin_path.write_bytes(bin_data)
    sig_path.write_text(sig_hex, encoding="utf-8")

    logger.info("Firmware saved: version=%s, path=%s", version, fw_dir)
    return str(bin_path), str(sig_path)


def read_firmware_bytes(file_path: str) -> bytes:
    """
    Read firmware binary from storage.
    Validates path is within storage root before reading.
    """
    resolved = _safe_resolve(file_path)
    if not resolved.is_file():
        raise FileNotFoundError(f"Firmware file not found: {file_path}")
    return resolved.read_bytes()


def read_signature_hex(sig_path: str) -> str:
    """
    Read firmware hex signature from storage.
    Validates path is within storage root before reading.
    """
    resolved = _safe_resolve(sig_path)
    if not resolved.is_file():
        raise FileNotFoundError(f"Signature file not found: {sig_path}")
    return resolved.read_text(encoding="utf-8").strip()
