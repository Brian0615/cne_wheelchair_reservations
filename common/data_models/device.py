from pydantic import BaseModel, constr, Field, model_validator

from common.constants import DeviceStatus, DeviceType, Location, DEVICE_ID_PATTERN


class Device(BaseModel):
    """Data model for a mobility device"""

    id: constr(to_upper=True, pattern=DEVICE_ID_PATTERN) = Field(title="ID")
    type: DeviceType = Field(title="Type")
    status: DeviceStatus = Field(title="Status")
    location: Location = Field(title="Location")

    # pylint: disable=no-member
    @model_validator(mode="after")
    def check_id(self):
        """Ensure that the device ID matches the device type"""
        if self.type == DeviceType.SCOOTER and not self.id.startswith("S"):
            raise ValueError(f"ID for Scooters should start with 'S' - got {self.id} instead")
        if self.type == DeviceType.WHEELCHAIR and not self.id.startswith("W"):
            raise ValueError(f"ID for Wheelchairs should start with 'W' - got {self.id} instead")
        return self
