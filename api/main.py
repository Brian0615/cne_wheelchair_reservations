from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import constr

from api.src.data_service import DataService
from api.src.exceptions import UniqueViolation
from common.constants import DeviceType, Location
from common.data_models.device import Device

app = FastAPI()
data_service = DataService()


@app.get("/devices/get_available_devices")
def get_available_devices(device_type: DeviceType, location: Location) -> List[constr(pattern=r"[S|W][0-9]{2}")]:
    """Get the available devices of a specific type at a specific location"""
    return data_service.get_available_devices(device_type, location)


@app.get("/devices/get_full_inventory")
def get_full_inventory() -> List[Device]:
    """Get the full inventory of devices"""
    return data_service.get_full_inventory().to_dict(orient="records")


@app.post("/devices/add_to_inventory")
def add_to_inventory(devices: List[Device]):
    """Add a device to the inventory"""
    try:
        return data_service.add_to_inventory(devices)
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/devices/update_inventory")
def update_inventory(devices: List[Device]):
    """Set the full inventory of devices. Overwrites the existing inventory."""
    try:
        return data_service.update_inventory(devices)
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
