from pydantic import BaseModel, constr, Field, model_validator

from common.constants import DeviceStatus, DeviceType, Location


class Device(BaseModel):
    id: constr(to_upper=True, pattern=r"[A-Z][0-9]{2}") = Field(title="ID")
    type: DeviceType = Field(title="Type")
    status: DeviceStatus = Field(title="Status")
    location: Location = Field(title="Location")

    # check that id starts with S if type is Scooter and W if type is Wheelchair
    @model_validator(mode="after")
    def check_id(self):
        if self.type == DeviceType.SCOOTER and not self.id.startswith("S"):
            raise ValueError(f"ID for Scooters should start with 'S' - got {self.id} instead")
        if self.type == DeviceType.WHEELCHAIR and not self.id.startswith("W"):
            raise ValueError(f"ID for Wheelchairs should start with 'W' - got {self.id} instead")
        return self
