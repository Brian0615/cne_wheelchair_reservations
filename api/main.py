from datetime import datetime
from typing import List, Annotated, Optional

from fastapi import FastAPI, HTTPException, File
from pydantic import constr

from api.routers import devices_router
from api.src.exceptions import UniqueViolation
from api.src.rds_service import RDSService
from api.src.s3_service import S3Service
from api.src.utils import auto_process_database_errors
from common.constants import (
    DeviceType,
    Location,
    ReservationStatus,
    RESERVATION_ID_PATTERN,
)
from common.data_models import (
    ChangeDeviceInfo,
    CompletedRental,
    NewRental,
    NewReservation,
    RentalSummary,
    Reservation,
)

app = FastAPI()
# add the routers
app.include_router(devices_router)
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


# ==============================
# RESERVATIONS
# ==============================

@app.get("/reservations/get_number_of_reservations_on_date")
@auto_process_database_errors
def get_number_of_reservations_on_date(date: str, device_type: DeviceType, location: Location) -> int:
    """Get the number of reservations on a specific date"""
    date = datetime.strptime(date, "%Y-%m-%d").date()
    result = rds_service.get_number_of_reservations_on_date(date=date, device_type=device_type, location=location)
    return result.iloc[0]["number_of_reservations"] if not result.empty else 0


@app.get("/reservations/get_reservations_on_date")
@auto_process_database_errors
def get_reservations_on_date(
        date: str,
        device_type: Optional[DeviceType] = None,
        exclude_picked_up_reservations: bool = False,
) -> List[Reservation]:
    """Get the reservations on a specific date"""
    date = datetime.strptime(date, "%Y-%m-%d").date()
    reservations = rds_service.get_reservations_on_date(
        date=date,
        device_type=device_type,
        exclude_picked_up_reservations=exclude_picked_up_reservations,
    )
    return [Reservation(**x) for x in reservations.to_dict(orient="records")]


@app.post("/reservations/add_new_reservation")
@auto_process_database_errors
def insert_new_reservation(reservation: NewReservation) -> constr(to_upper=True, pattern=RESERVATION_ID_PATTERN):
    """Add a new reservation"""
    try:
        return rds_service.insert_new_reservation(reservation=reservation)
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/reservations/update_reservation")
@auto_process_database_errors
def update_reservation(reservation: Reservation):
    """Update reservation"""
    return rds_service.update_reservation(reservation=reservation)


@app.post("/reservations/update_reservation_status")
@auto_process_database_errors
def update_reservation_status(reservation_id: str, reservation_status: ReservationStatus):
    """Update the status of a reservation"""
    return rds_service.update_reservation_status(reservation_id=reservation_id, reservation_status=reservation_status)
