import datetime
from typing import Optional

from pydantic import AwareDatetime, BaseModel, constr, Field

from common.constants import DeviceType, Location, RENTAL_ID_PATTERN, RESERVATION_ID_PATTERN


class Reservation(BaseModel):
    """Data validation class for a reservation"""
    id: constr(to_upper=True, pattern=RESERVATION_ID_PATTERN) = Field(title="Reservation ID")
    date: datetime.date = Field(title="Reservation Date")
    device_type: DeviceType = Field(title="Reservation Type")
    name: constr(min_length=5, strip_whitespace=True) = Field(title="Name")
    phone_number: constr(min_length=5) = Field(title="Phone Number")
    location: Location = Field(title="Pickup Location")
    pickup_time: AwareDatetime = Field(title="Pickup Time")
    notes: Optional[str] = Field(title="Additional Notes", default="N/A")
    rental_id: Optional[constr(to_upper=True, pattern=RENTAL_ID_PATTERN)] = Field(title="Rental ID", default=None)


class NewReservation(Reservation):
    """Data validation class for a New Reservation"""
    id: Optional[constr(to_upper=True, pattern=RESERVATION_ID_PATTERN)] = Field(title="Reservation ID", default=None)
