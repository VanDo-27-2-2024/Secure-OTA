import logging
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from app import signer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# TODO(security): KMS must only be reachable from the be-api service via the internal
# Docker network. It MUST NOT be exposed on a public port in production.
# The docker-compose.yml network configuration enforces this.

app = FastAPI(
    title="OTA KMS — Key Management Service",
    description="Internal signing service. NOT to be exposed publicly.",
    version="1.0.0",
)


class SignRequest(BaseModel):
    data: str  # hex-encoded firmware binary


class SignResponse(BaseModel):
    signature: str  # hex-encoded Ed25519 signature


@app.post(
    "/sign",
    response_model=SignResponse,
    summary="Sign firmware data with the private key",
)
async def sign_data(body: SignRequest):
    """
    Accepts hex-encoded firmware data, returns hex-encoded Ed25519 signature.
    The private key never leaves this service.
    """
    try:
        sig_hex = signer.sign(body.data)
    except ValueError as exc:
        logger.warning("Invalid sign request: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid hex input",
        )
    except Exception as exc:
        # Never expose internal key errors to caller
        logger.error("Signing error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signing failed",
        )

    return SignResponse(signature=sig_hex)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}
