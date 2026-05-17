from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator, StringConstraints

from common.constants import DeviceStatus, DeviceType, Location, DEVICE_ID_PATTERN
from common.data_models.fields import CNEYearField


class Device(BaseModel):
    """Data model for a mobility device"""
    model_config = ConfigDict(extra="forbid")

    cne_year: CNEYearField
    id: Annotated[str, StringConstraints(to_upper=True, pattern=DEVICE_ID_PATTERN)] = Field(title="ID")
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


class NewDevice(Device):
    """Data model for a new mobility device"""

    id: Optional[Annotated[str, StringConstraints(to_upper=True, pattern=DEVICE_ID_PATTERN)]] = Field(title="ID",
                                                                                                      default=None)

    @model_validator(mode="after")
    def check_id(self):
        """Overwrite this validator as ID is optional for new devices"""
        return self
