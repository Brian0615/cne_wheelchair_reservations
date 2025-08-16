from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from api.src.dynamodb_service import DynamoDBService
from api.src.exceptions import DeviceNotFoundOrNotAvailableException, NewReservationNotFoundOrNotEditableException
from api.src.utils import auto_process_database_errors
from common.constants import DeviceType
from common.data_models import ChangeDeviceInfo, CompletedRental, NewRental, RentalSummary

db_service = DynamoDBService()
router = APIRouter(prefix="/rentals", tags=["rentals"])


@router.post("/add")
@auto_process_database_errors
def add_new_rental(new_rental: NewRental):
    """Start a new rental"""
    try:
        return db_service.insert_rental(rental=new_rental)
    except (DeviceNotFoundOrNotAvailableException, NewReservationNotFoundOrNotEditableException) as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.post("/change_device")
@auto_process_database_errors
def change_rental_device(change_device_info: ChangeDeviceInfo):
    """Change the device of a rental"""
    return db_service.change_rental_device(change_info=change_device_info)


@router.post("/complete_rental")
@auto_process_database_errors
def complete_rental(completed_rental: CompletedRental):
    """Complete a rental"""
    return db_service.complete_rental(rental=completed_rental)


@router.get("/get_rentals_on_date")
@auto_process_database_errors
def get_rentals_on_date(
        date: datetime,
        device_type: DeviceType = None,
        in_progress_rentals_only: bool = False,
) -> List[RentalSummary]:
    """Get the rentals on a specific date"""
    rentals = db_service.get_rentals_on_date(
        date=date.date(),
        device_type=device_type,
        in_progress_rentals_only=in_progress_rentals_only,
    )
    return [RentalSummary(**x) for x in rentals]
