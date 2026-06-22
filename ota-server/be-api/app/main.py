import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.services.admin.admin_router import router as admin_router
from app.services.device.device_router import router as device_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OTA Server API",
    description="Secure Over-The-Air firmware update service",
    version="1.0.0",
)

# TODO(security): CORS — tighten allowed_origins before production deployment.
# Currently set to allow all for local development only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO(security): restrict to known origins in prod
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Attach security headers to every response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


# Register routers
app.include_router(admin_router)
app.include_router(device_router)
