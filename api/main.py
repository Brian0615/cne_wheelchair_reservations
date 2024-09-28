import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import constr

from api.src.data_service import DataService
from api.src.exceptions import UniqueViolation
from api.src.utils import auto_process_database_errors
from common.constants import DeviceType, Location, RESERVATION_ID_PATTERN
from common.data_models import Device, NewRental, NewReservation, Reservation

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
def get_reservations_on_date(date: str, device_type: Optional[DeviceType] = None) -> List[Reservation]:
    """Get the reservations on a specific date"""
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    reservations = data_service.get_reservations_on_date(date=date, device_type=device_type).to_dict(orient="records")
    return [Reservation(**x) for x in reservations]


@app.post("/reservations/add_new_rental")
@auto_process_database_errors
def add_new_rental(new_rental: NewRental):
    """Start a new rental"""
    return data_service.add_new_rental(new_rental=new_rental)
