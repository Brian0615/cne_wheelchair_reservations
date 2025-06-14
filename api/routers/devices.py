from typing import List, Optional

from fastapi import APIRouter
from pydantic import constr

from api.src.dynamodb_service import DynamoDBService
from api.src.utils import auto_process_database_errors
from common.constants import DeviceType, Location, DEVICE_ID_PATTERN, DeviceStatus
from common.data_models import Device, NewDevice

db_service = DynamoDBService()
router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("/add")
@auto_process_database_errors
def add_devices(devices: List[NewDevice]):
    """Add a device to the inventory"""
    return db_service.add_devices(devices=devices)


@router.get("/get_available_devices")
def get_available_device_ids(
        cne_year: int,
        device_type: DeviceType,
        location: Optional[Location] = None,
) -> List[constr(pattern=DEVICE_ID_PATTERN)]:
    """Get the available devices of a specific type at a specific location (location optional)"""
    return db_service.get_available_device_ids(cne_year=cne_year, device_type=device_type, location=location)


@router.get("/get_full_inventory")
@auto_process_database_errors
def get_full_inventory(cne_year: int) -> List[Device]:
    """Get the full inventory of devices"""
    return [Device(**x) for x in db_service.get_full_inventory(cne_year=cne_year)]


@router.post("/remove")
@auto_process_database_errors
def remove_devices(cne_year: int, device_ids: List[constr(to_upper=True, pattern=DEVICE_ID_PATTERN)]):
    """Remove devices from the inventory"""
    return db_service.remove_devices(cne_year=cne_year, device_ids=device_ids)


@router.post("/update_location")
@auto_process_database_errors
def update_devices_location(
        cne_year: int,
        device_ids: List[constr(to_upper=True, pattern=DEVICE_ID_PATTERN)],
        location: Location,
):
    """Update the location of devices"""
    return db_service.update_devices_location(cne_year=cne_year, device_ids=device_ids, location=location)


@router.post("/update_status")
@auto_process_database_errors
def update_devices_status(
        cne_year: int,
        device_ids: List[constr(to_upper=True, pattern=DEVICE_ID_PATTERN)],
        status: DeviceStatus,
):
    """Update the status of devices"""
    return db_service.update_devices_status(cne_year=cne_year, device_ids=device_ids, status=status)
