from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter
from pydantic import constr

from api.src.dynamodb_service import DynamoDBService
from api.src.utils import auto_process_database_errors
from common.constants import DeviceType, RESERVATION_ID_PATTERN, ReservationStatus
from common.data_models import NewReservation, Reservation

db_service = DynamoDBService()
router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("/get_reservations_on_date")
@auto_process_database_errors
def get_reservations_on_date(
        date: datetime,
        device_type: Optional[DeviceType] = None,
        exclude_picked_up_reservations: bool = False,
) -> List[Reservation]:
    """Get the reservations on a specific date"""
    reservations = db_service.get_reservations_on_date(
        date=date.date(),
        device_type=device_type,
        exclude_picked_up_reservations=exclude_picked_up_reservations,
    )
    return [Reservation(**x) for x in reservations]


@router.post("/add")
@auto_process_database_errors
def insert_reservation(reservation: NewReservation) -> constr(to_upper=True, pattern=RESERVATION_ID_PATTERN):
    """Add a new reservation"""
    return db_service.insert_reservation(reservation=reservation)


@router.post("/update_reservation")
@auto_process_database_errors
def update_reservation(reservation: Reservation) -> None:
    """Update reservation"""
    return db_service.update_reservation(reservation=reservation)


@router.post("/update_reservation_status")
@auto_process_database_errors
def update_reservation_status(
        cne_year: int,
        reservation_id: constr(to_upper=True, pattern=RESERVATION_ID_PATTERN),
        reservation_status: ReservationStatus,
) -> None:
    """Update the status of a reservation"""
    return db_service.update_reservation_status(
        cne_year=cne_year,
        reservation_id=reservation_id,
        status=reservation_status,
    )
