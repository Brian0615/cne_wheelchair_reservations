import datetime
from typing import Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, conint, constr, Field

from common.constants import (
    DeviceType,
    Location,
    ReservationStatus,
    RENTAL_ID_PATTERN,
    RESERVATION_ID_PATTERN,
)


class Reservation(BaseModel):
    """Data validation class for a reservation"""
    model_config = ConfigDict(extra="forbid")

    cne_year: conint(ge=2000) = Field(title="CNE Year")
    id: constr(to_upper=True, pattern=RESERVATION_ID_PATTERN) = Field(title="Reservation ID")
    date: datetime.date = Field(title="Reservation Date")
    device_type: DeviceType = Field(title="Reservation Type")
    location: Location = Field(title="Pickup Location")
    reservation_time: AwareDatetime = Field(title="Reservation Time")
    name: constr(min_length=5, strip_whitespace=True) = Field(title="Name")
    phone_number: constr(min_length=5) = Field(title="Phone Number")
    notes: Optional[str] = Field(title="Additional Notes", default="N/A")
    status: ReservationStatus = Field(title="Status")
    rental_id: Optional[constr(to_upper=True, pattern=RENTAL_ID_PATTERN)] = Field(title="Rental ID", default=None)


class NewReservation(Reservation):
    """Data validation class for a New Reservation"""
    model_config = ConfigDict(extra="forbid")

    id: Optional[constr(to_upper=True, pattern=RESERVATION_ID_PATTERN)] = Field(title="Reservation ID", default=None)
