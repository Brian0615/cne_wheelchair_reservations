from datetime import datetime
from typing import List, Annotated, Optional

from fastapi import FastAPI, HTTPException, File

from api.routers import devices_router, reservations_router
from api.src.rds_service import RDSService
from api.src.s3_service import S3Service
from api.src.utils import auto_process_database_errors
from common.constants import DeviceType
from common.data_models import (
    ChangeDeviceInfo,
    CompletedRental,
    NewRental,
    RentalSummary,
)

app = FastAPI()
# add the routers
app.include_router(devices_router)
app.include_router(reservations_router)

s3_service = S3Service()
rds_service = RDSService()


# ==============================
# HEALTH CHECK
# ==============================

@app.get("/health")
def health_check():
    """Health check"""
    return {"status": "ok", "time": datetime.now().isoformat()}


# ==============================
# RENTALS
# ==============================

@app.post("/rentals/add_new_rental")
@auto_process_database_errors
def add_new_rental(new_rental: NewRental):
    """Start a new rental"""
    return rds_service.add_new_rental(new_rental=new_rental)


@app.post("/rentals/change_device")
@auto_process_database_errors
def change_rental_device(change_device_info: ChangeDeviceInfo):
    """Change the device of a rental"""
    return rds_service.change_rental_device(change_device_info=change_device_info)


@app.post("/rentals/complete_rental")
@auto_process_database_errors
def complete_rental(completed_rental: CompletedRental):
    """Complete a rental"""
    return rds_service.complete_rental(completed_rental=completed_rental)


@app.get("/rentals/get_rentals_on_date")
@auto_process_database_errors
def get_rentals_on_date(
        date: str,
        device_type: DeviceType = None,
        in_progress_rentals_only: bool = False,
) -> List[RentalSummary]:
    """Get the rentals on a specific date"""
    date = datetime.strptime(date, "%Y-%m-%d").date()
    rentals = rds_service.get_rentals_on_date(
        date=date,
        device_type=device_type,
        in_progress_rentals_only=in_progress_rentals_only,
    )
    rentals["items_left_behind"] = rentals["items_left_behind"].apply(lambda x: [] if x == "{}" else x[1:-1].split(","))
    return [RentalSummary(**x) for x in rentals.to_dict(orient="records")]


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
