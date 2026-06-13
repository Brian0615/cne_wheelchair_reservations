import datetime
from typing import Annotated, Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

from common.constants import (
    DeviceType,
    Location,
    ReservationStatus,
    RENTAL_ID_PATTERN,
    RESERVATION_ID_PATTERN,
)
from common.data_models.fields import CNEYearField, PhoneNumberField


class Reservation(BaseModel):
    """Data validation class for a reservation"""
    model_config = ConfigDict(extra="forbid")

    cne_year: CNEYearField
    id: Annotated[str, StringConstraints(to_upper=True, pattern=RESERVATION_ID_PATTERN)] = Field(title="Reservation ID")
    date: datetime.date = Field(title="Reservation Date")
    device_type: DeviceType = Field(title="Reservation Type")
    location: Location = Field(title="Pickup Location")
    reservation_time: AwareDatetime = Field(title="Reservation Time")
    name: Annotated[str, StringConstraints(min_length=5, strip_whitespace=True)] = Field(title="Name")
    phone_number: PhoneNumberField = Field(title="Phone Number")
    notes: Optional[str] = Field(title="Additional Notes", default="N/A")
    status: ReservationStatus = Field(title="Status")
    rental_id: Optional[
        Annotated[str, StringConstraints(to_upper=True, pattern=RENTAL_ID_PATTERN)]
    ] = Field(title="Rental ID", default=None)


class NewReservation(Reservation):
    """Data validation class for a New Reservation"""
    model_config = ConfigDict(extra="forbid")

    id: Optional[Annotated[str, StringConstraints(to_upper=True, pattern=RESERVATION_ID_PATTERN)]] = Field(
        title="Reservation ID", default=None)


class ReservationCount(BaseModel):
    """Data validation class for reservation counts"""
    model_config = ConfigDict(extra="forbid")

    date: datetime.date = Field(title="Reservation Date")
    device_type: DeviceType = Field(title="Reservation Type")
    location: Location = Field(title="Pickup Location")
    count: Annotated[int, Field(title="Reservation Count", ge=0)]


class ReservationStatusCount(BaseModel):
    """Data validation class for reservation counts broken down by status"""
    model_config = ConfigDict(extra="forbid")

    status: ReservationStatus = Field(title="Status")
    device_type: DeviceType = Field(title="Reservation Type")
    count: Annotated[int, Field(title="Reservation Count", ge=0)]
