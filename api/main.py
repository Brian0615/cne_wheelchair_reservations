from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, File

from api.routers import devices_router, rentals_router, reservations_router, settings_router
from api.src.s3_service import S3Service

app = FastAPI()
# add the routers
app.include_router(devices_router)
app.include_router(reservations_router)
app.include_router(rentals_router)
app.include_router(settings_router)
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

@app.get("/forms/download_rental_form")
def download_rental_form(rental_id: str) -> Optional[bytes]:
    """Download a rental form from S3"""
    try:
        return s3_service.download_rental_form(rental_id=rental_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/forms/upload_rental_form")
def upload_rental_form(pdf_bytes: Annotated[bytes, File()], rental_id: str):
    """Upload a rental form to S3"""
    s3_service.upload_rental_form(pdf_bytes=pdf_bytes, rental_id=rental_id)
