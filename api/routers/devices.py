from typing import Annotated, List, Optional

from fastapi import APIRouter
from pydantic import StringConstraints

from api.src.dynamodb_service import DynamoDBService
from api.src.utils import auto_process_database_errors
from common.constants import DeviceType, Location, DEVICE_ID_PATTERN, DeviceStatus
from common.data_models import Device, NewDevice
from common.logger import initialize_logger

logger = initialize_logger()

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
) -> List[Annotated[str, StringConstraints(pattern=DEVICE_ID_PATTERN)]]:
    """Get the available devices of a specific type at a specific location (location optional)"""
    return db_service.get_available_device_ids(cne_year=cne_year, device_type=device_type, location=location)


@router.get("/get_full_inventory")
@auto_process_database_errors
def get_full_inventory(cne_year: int) -> List[Device]:
    """Get the full inventory of devices"""
    return [Device(**x) for x in db_service.get_full_inventory(cne_year=cne_year)]


@router.post("/remove")
@auto_process_database_errors
def remove_devices(
        cne_year: int,
        device_ids: List[Annotated[str, StringConstraints(to_upper=True, pattern=DEVICE_ID_PATTERN)]]
):
    """Remove devices from the inventory"""
    result = db_service.remove_devices(cne_year=cne_year, device_ids=device_ids)
    logger.info("Removed devices from the inventory", extra={"device_id": device_ids})
    return result


@router.post("/update_location")
@auto_process_database_errors
def update_devices_location(
        cne_year: int,
        device_ids: List[Annotated[str, StringConstraints(to_upper=True, pattern=DEVICE_ID_PATTERN)]],
        location: Location,
):
    """Update the location of devices"""
    result = db_service.update_devices_location(cne_year=cne_year, device_ids=device_ids, location=location)
    logger.info("Updated device location", extra={"device_id": device_ids, "location": location})
    return result


@router.post("/update_status")
@auto_process_database_errors
def update_devices_status(
        cne_year: int,
        device_ids: List[Annotated[str, StringConstraints(to_upper=True, pattern=DEVICE_ID_PATTERN)]],
        status: DeviceStatus,
):
    """Update the status of devices"""
    result = db_service.update_devices_status(cne_year=cne_year, device_ids=device_ids, status=status)
    logger.info("Updated device status", extra={"device_id": device_ids, "status": status})
    return result
