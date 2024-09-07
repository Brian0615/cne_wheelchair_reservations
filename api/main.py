from typing import List

from fastapi import FastAPI, HTTPException

from api.src.data_service import DataService
from api.src.exceptions import UniqueViolation
from common.data_models.device import Device

app = FastAPI()
data_service = DataService()


@app.get("/devices/get_full_inventory")
def get_full_inventory() -> List[Device]:
    return data_service.get_full_inventory().to_dict(orient="records")


@app.post("/devices/set_full_inventory")
def set_full_inventory(devices: List[Device]):
    try:
        return data_service.set_full_inventory(devices)
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc))
