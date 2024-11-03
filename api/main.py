import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import constr

from api.src.data_service import DataService
from api.src.exceptions import UniqueViolation
from api.src.utils import auto_process_database_errors
from common.constants import DeviceType, Location, DEVICE_ID_PATTERN, RESERVATION_ID_PATTERN
from common.data_models import (
    ChangeDeviceInfo,
    CompletedRental,
    Device,
    NewRental,
    NewReservation,
    RentalSummary,
    Reservation,
)

app = FastAPI()
data_service = DataService()


@app.get("/devices/get_available_devices")
def get_available_device_ids(device_type: DeviceType, location: Location) -> List[constr(pattern=r"[S|W][0-9]{2}")]:
    """Get the available devices of a specific type at a specific location"""
    return data_service.select_available_device_ids(device_type, location)


@app.get("/devices/get_full_inventory")
@auto_process_database_errors
def get_full_inventory() -> List[Device]:
    """Get the full inventory of devices"""
    return data_service.get_full_inventory().to_dict(orient="records")


@app.post("/devices/add_to_inventory")
@auto_process_database_errors
def insert_devices(devices: List[Device]):
    """Add a device to the inventory"""
    return data_service.insert_devices(devices)


@app.post("/devices/update_inventory")
@auto_process_database_errors
def update_devices(devices: List[Device]):
    """Set the full inventory of devices. Overwrites the existing inventory."""
    return data_service.update_devices(devices)


@app.post("/devices/update_location")
@auto_process_database_errors
def update_devices_location(device_ids: List[constr(to_upper=True, pattern=DEVICE_ID_PATTERN)], location: Location):
    """Update the location of devices"""
    return data_service.update_devices_location(device_ids, location)


@app.post("/reservations/add_new_reservation")
@auto_process_database_errors
def insert_new_reservation(reservation: NewReservation) -> constr(to_upper=True, pattern=RESERVATION_ID_PATTERN):
    """Add a new reservation"""
    try:
        return data_service.insert_new_reservation(reservation=reservation)
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/reservations/get_reservations_on_date")
@auto_process_database_errors
def get_reservations_on_date(
        date: str,
        device_type: Optional[DeviceType] = None,
        exclude_picked_up_reservations: bool = False,
) -> List[Reservation]:
    """Get the reservations on a specific date"""
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    reservations = data_service.get_reservations_on_date(
        date=date,
        device_type=device_type,
        exclude_picked_up_reservations=exclude_picked_up_reservations,
    )
    return [Reservation(**x) for x in reservations.to_dict(orient="records")]


@app.post("/rentals/add_new_rental")
@auto_process_database_errors
def add_new_rental(new_rental: NewRental):
    """Start a new rental"""
    return data_service.add_new_rental(new_rental=new_rental)


@app.post("/rentals/change_device")
@auto_process_database_errors
def change_device(change_device_info: ChangeDeviceInfo):
    """Change the device of a rental"""
    return data_service.change_device_for_rental(change_device_info=change_device_info)


@app.post("/rentals/complete_rental")
@auto_process_database_errors
def complete_rental(completed_rental: CompletedRental):
    """Complete a rental"""
    return data_service.complete_rental(completed_rental=completed_rental)


@app.get("/rentals/get_rentals_on_date")
@auto_process_database_errors
def get_rentals_on_date(
        date: str,
        device_type: DeviceType = None,
        in_progress_rentals_only: bool = False,
) -> List[RentalSummary]:
    """Get the rentals on a specific date"""
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    rentals = data_service.get_rentals_on_date(
        date=date,
        device_type=device_type,
        in_progress_rentals_only=in_progress_rentals_only,
    )
    rentals["items_left_behind"] = rentals["items_left_behind"].apply(lambda x: [] if x == "{}" else x[1:-1].split(","))
    return [RentalSummary(**x) for x in rentals.to_dict(orient="records")]
