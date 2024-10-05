import datetime
from typing import List, Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, conint, constr, Field

from common.constants import (
    DeviceType,
    HoldItem,
    Location,
    PaymentMethod,
    DEVICE_ID_PATTERN,
    RENTAL_ID_PATTERN,
    RESERVATION_ID_PATTERN,
)


class RentalBase(BaseModel):
    """Data model for a base rental"""
    model_config = ConfigDict(extra="forbid", ser_json_bytes="utf8")

    id: constr(to_upper=True, pattern=RENTAL_ID_PATTERN) = Field(title="Rental ID")
    date: datetime.date = Field(title="Rental Date")
    name: constr(min_length=3) = Field(title="Name")
    phone_number: constr(min_length=5) = Field(title="Phone Number")
    device_type: DeviceType = Field(title="Device Type")
    device_id: constr(to_upper=True, pattern=DEVICE_ID_PATTERN) = Field(title="Device ID")
    pickup_location: Location = Field(title="Pickup Location")
    pickup_time: AwareDatetime = Field(title="Pickup Time")

    deposit_payment_method: PaymentMethod = Field(title="Deposit Payment Method")
    return_location: Optional[Location] = Field(title="Return Location", default=None)
    return_time: Optional[AwareDatetime] = Field(title="Return Time", default=None)
    items_left_behind: List[HoldItem] = Field(title="Items Left Behind", default=[])
    notes: Optional[str] = Field(title="Notes", default="N/A")


class Rental(RentalBase):
    """Data model for a rental."""

    address: constr(min_length=5, strip_whitespace=True) = Field(title="Address")
    city: constr(min_length=5) = Field(title="City")
    province: constr(min_length=2) = Field(title="Province")
    postal_code: Optional[constr(min_length=3)] = Field(title="Postal Code", default=None)
    country: constr(min_length=3) = Field(title="Country")
    fee_payment_method: PaymentMethod = Field(title="Fee Payment Method")
    fee_payment_amount: conint(gt=0) = Field(title="Fee Payment Amount")
    deposit_payment_amount: conint(gt=0) = Field(title="Deposit Payment Amount")
    staff_name: constr(min_length=5) = Field(title="Staff Name")
    signature: bytes = Field(title="Signature")


class NewRental(Rental):
    """Data model for a new rental."""

    id: Optional[constr(to_upper=True, pattern=RENTAL_ID_PATTERN)] = Field(title="Rental ID", default=None)
    reservation_id: Optional[constr(pattern=RESERVATION_ID_PATTERN)] = Field(title="Reservation ID", default=None)
