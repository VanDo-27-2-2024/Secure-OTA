import logging
import httpx
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

# Timeout for KMS requests (seconds)
_KMS_TIMEOUT = 10.0


async def sign_firmware(bin_data: bytes) -> str:
    """
    Send firmware binary to KMS for signing.
    Returns hex-encoded Ed25519 signature.
    Raises HTTP 502 if KMS is unreachable or returns an error.
    """
    data_hex = bin_data.hex()
    try:
        async with httpx.AsyncClient(timeout=_KMS_TIMEOUT) as client:
            response = await client.post(
                f"{settings.kms_url}/sign",
                json={"data": data_hex},
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        logger.error("KMS request timed out")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="KMS service timed out",
        )
    except httpx.HTTPStatusError as exc:
        # Log the internal error detail, but do NOT expose it to the client
        logger.error("KMS returned error: status=%s", exc.response.status_code)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="KMS signing failed",
        )
    except httpx.RequestError as exc:
        logger.error("KMS unreachable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="KMS service unreachable",
        )

    payload = response.json()
    signature_hex: str = payload.get("signature", "")
    if not signature_hex:
        logger.error("KMS returned empty signature")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="KMS returned invalid response",
        )
    return signature_hex
