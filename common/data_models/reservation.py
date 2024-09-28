import datetime
from typing import Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, constr, Field

from common.constants import (
    DeviceType,
    Location,
    ReservationStatus,
    DEVICE_ID_PATTERN,
    RENTAL_ID_PATTERN,
    RESERVATION_ID_PATTERN,
)


class Reservation(BaseModel):
    """Data validation class for a reservation"""
    model_config = ConfigDict(extra="forbid")

    id: constr(to_upper=True, pattern=RESERVATION_ID_PATTERN) = Field(title="Reservation ID")
    date: datetime.date = Field(title="Reservation Date")
    device_type: DeviceType = Field(title="Reservation Type")
    name: constr(min_length=5, strip_whitespace=True) = Field(title="Name", default=None)
    phone_number: constr(min_length=5) = Field(title="Phone Number", default=None)
    location: Location = Field(title="Pickup Location", default=None, )
    pickup_time: AwareDatetime = Field(title="Pickup Time")
    status: ReservationStatus = Field(title="Status")
    device_id: Optional[constr(to_upper=True, pattern=DEVICE_ID_PATTERN)] = Field(title="Device ID", default=None)
    rental_id: Optional[constr(to_upper=True, pattern=RENTAL_ID_PATTERN)] = Field(title="Rental ID", default=None)
    notes: Optional[str] = Field(title="Additional Notes", default="N/A")



class NewReservation(Reservation):
    """Data validation class for a New Reservation"""
    model_config = ConfigDict(extra="forbid")

    id: Optional[constr(to_upper=True, pattern=RESERVATION_ID_PATTERN)] = Field(title="Reservation ID", default=None)
    status: Optional[ReservationStatus] = Field(title="Status", default=None)
