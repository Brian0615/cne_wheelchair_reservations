import time
from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI, HTTPException, File, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.routers import chat_router, devices_router, rentals_router, reservations_router, settings_router
from api.src.s3_service import S3Service
from common.logger import initialize_logger

logger = initialize_logger()

app = FastAPI()


# pylint: disable=too-few-public-methods
class AccessLogMiddleware(BaseHTTPMiddleware):
    """Logs each request's outcome and duration."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception",
                extra={"method": request.method, "path": request.url.path},
            )
            raise
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


app.add_middleware(AccessLogMiddleware)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # pylint: disable=unused-argument
    """Log unhandled exceptions and return a generic 500 response."""
    logger.exception("Unhandled exception in handler", extra={"path": request.url.path})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# add the routers
app.include_router(devices_router)
app.include_router(reservations_router)
app.include_router(rentals_router)
app.include_router(settings_router)
app.include_router(chat_router)
s3_service = S3Service()


# ==============================
# HEALTH CHECK
# ==============================

@app.get("/health")
def health_check():
    """Health check"""
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


# ==============================
# RENTAL FORMS
# ==============================

@app.get("/forms/download_rental_form", responses={404: {"description": "Rental form not found"}})
def download_rental_form(rental_id: str) -> Response:
    """Download a rental form from S3"""
    try:
        content = s3_service.download_rental_form(rental_id=rental_id)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=rental_form_{rental_id}.pdf"},
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/forms/upload_rental_form")
def upload_rental_form(pdf_bytes: Annotated[bytes, File()], rental_id: str):
    """Upload a rental form to S3"""
    s3_service.upload_rental_form(pdf_bytes=pdf_bytes, rental_id=rental_id)
