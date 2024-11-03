import datetime
from typing import List, Optional

import pandas as pd
from pydantic import AwareDatetime, BaseModel, ConfigDict, conint, constr, Field, field_validator

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
    """Base Data Model for Rentals"""

    model_config = ConfigDict(extra="forbid", ser_json_bytes="utf8")

    id: constr(to_upper=True, pattern=RENTAL_ID_PATTERN) = Field(title="Rental ID")


class RentalSummary(RentalBase):
    """Data model for a base rental"""

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

    # validator to convert pandas NaT to None
    @field_validator("return_time", mode="before")
    @classmethod
    def convert_nat_to_none(cls, value):
        return None if pd.isnull(value) else value


class NewRental(RentalSummary):
    """Data model for a rental."""

    id: Optional[constr(to_upper=True, pattern=RENTAL_ID_PATTERN)] = Field(title="Rental ID", default=None)
    reservation_id: Optional[constr(pattern=RESERVATION_ID_PATTERN)] = Field(title="Reservation ID", default=None)
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


class CompletedRental(RentalBase):
    return_location: Optional[Location] = Field(title="Return Location", default=None)
    return_time: Optional[AwareDatetime] = Field(title="Return Time", default=None)
    return_staff_name: constr(min_length=5) = Field(title="Return Staff Name")
    return_signature: bytes = Field(title="Return Signature")


class ChangeDeviceInfo(BaseModel):
    """Data model for changing device info"""
    rental_id: constr(to_upper=True, pattern=RENTAL_ID_PATTERN) = Field(title="Rental ID")
    device_type: DeviceType = Field(title="Device Type")
    location: Location = Field(title="Location")
    old_device_id: constr(to_upper=True, pattern=DEVICE_ID_PATTERN) = Field(title="Old Device ID")
    new_device_id: constr(to_upper=True, pattern=DEVICE_ID_PATTERN) = Field(title="New Device ID")
    staff_name: constr(min_length=5) = Field(title="Staff Name")
