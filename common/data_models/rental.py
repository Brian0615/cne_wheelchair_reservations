import datetime
from typing import List, Optional

import pandas as pd
from pydantic import AwareDatetime, BaseModel, ConfigDict, conint, constr, Field, field_validator, model_validator

from common.constants import (
    DeviceType,
    HoldItem,
    Location,
    PaymentMethod,
    RentalStatus,
    DEVICE_ID_PATTERN,
    RENTAL_ID_PATTERN,
    RESERVATION_ID_PATTERN,
)


class Rental(BaseModel):
    """Data model for a rental"""
    model_config = ConfigDict(extra="forbid", ser_json_bytes="utf8")

    cne_year: conint(ge=2000) = Field(title="CNE Year")
    id: constr(to_upper=True, pattern=RENTAL_ID_PATTERN) = Field(title="Rental ID")
    date: datetime.date = Field(title="Rental Date")
    device_id: constr(to_upper=True, pattern=DEVICE_ID_PATTERN) = Field(title="Device ID")
    device_type: DeviceType = Field(title="Device Type")
    reservation_id: Optional[constr(pattern=RESERVATION_ID_PATTERN)] = Field(title="Reservation ID", default=None)
    pickup_location: Location = Field(title="Pickup Location")
    pickup_time: AwareDatetime = Field(title="Pickup Time")
    status: RentalStatus = Field(title="Status")

    name: constr(min_length=3) = Field(title="Name")
    phone_number: constr(min_length=5) = Field(title="Phone Number")
    address: constr(min_length=5, strip_whitespace=True) = Field(title="Address")
    city: constr(min_length=5) = Field(title="City")
    province: constr(min_length=2) = Field(title="Province")
    postal_code: Optional[constr(min_length=3)] = Field(title="Postal Code", default=None)
    country: constr(min_length=3) = Field(title="Country")

    fee_payment_method: PaymentMethod = Field(title="Fee Payment Method")
    fee_payment_amount: conint(gt=0) = Field(title="Fee Payment Amount")
    deposit_payment_amount: conint(gt=0) = Field(title="Deposit Payment Amount")
    deposit_payment_method: PaymentMethod = Field(title="Deposit Payment Method")
    items_left_behind: List[HoldItem] = Field(title="Items Left Behind", default=[])
    notes: Optional[str] = Field(title="Notes", default=None)
    staff_name: constr(min_length=5) = Field(title="Staff Name")
    signature: bytes = Field(title="Signature")

    return_location: Optional[Location] = Field(title="Return Location", default=None)
    return_time: Optional[AwareDatetime] = Field(title="Return Time", default=None)
    return_staff_name: Optional[constr(min_length=5)] = Field(title="Return Staff Name", default=None)
    return_signature: Optional[bytes] = Field(title="Return Signature", default=None)

    # pylint: disable=no-member
    @model_validator(mode="after")
    def check_device_id(self):
        """Ensure that the device ID matches the device type"""
        if not self.device_id.startswith(self.device_type.get_prefix()):
            raise ValueError(f"Device ID ({self.device_id}) and type ({self.device_type}) do not match")
        return self

    # pylint: disable=no-member
    @model_validator(mode="after")
    def check_reservation_id(self):
        """Ensure that the reservation ID matches the device type"""
        if self.reservation_id:
            if not self.reservation_id.startswith(self.device_type.get_prefix()):
                raise ValueError(f"Reservation ID ({self.reservation_id}) and type ({self.device_type}) do not match")
        return self

    @model_validator(mode="after")
    def check_year_and_date(self):
        """Ensure that the CNE year and the year of the rental date match"""
        if self.cne_year != self.date.year:
            raise ValueError(f"CNE Year ({self.cne_year}) and date ({self.date}) do not match")
        return self


class RentalBase(BaseModel):
    """Base Data Model for Rentals"""

    model_config = ConfigDict(extra="forbid", ser_json_bytes="utf8")

    id: constr(to_upper=True, pattern=RENTAL_ID_PATTERN) = Field(title="Rental ID")


class RentalSummary(Rental):
    """Data model for a base rental"""

    # make unneeded fields optional and set defaults to None
    reservation_id: Optional[constr(pattern=RESERVATION_ID_PATTERN)] = Field(title="Reservation ID", default=None)
    status: Optional[RentalStatus] = Field(title="Status", default=None)

    address: Optional[constr(min_length=5, strip_whitespace=True)] = Field(title="Address", default=None)
    city: Optional[constr(min_length=5)] = Field(title="City", default=None)
    province: Optional[constr(min_length=2)] = Field(title="Province", default=None)
    postal_code: Optional[constr(min_length=3)] = Field(title="Postal Code", default=None)
    country: Optional[constr(min_length=3)] = Field(title="Country", default=None)

    fee_payment_method: Optional[PaymentMethod] = Field(title="Fee Payment Method", default=None)
    fee_payment_amount: Optional[conint(gt=0)] = Field(title="Fee Payment Amount", default=None)
    deposit_payment_amount: Optional[conint(gt=0)] = Field(title="Deposit Payment Amount", default=None)
    staff_name: Optional[constr(min_length=5)] = Field(title="Staff Name", default=None)
    signature: Optional[bytes] = Field(title="Signature", default=None)

    return_staff_name: Optional[constr(min_length=5)] = Field(title="Return Staff Name", default=None)
    return_signature: Optional[bytes] = Field(title="Return Signature", default=None)

    # validator to convert pandas NaT to None
    @field_validator("return_time", mode="before")
    @classmethod
    def convert_nat_to_none(cls, value):
        """Convert pandas NaT to None"""
        return None if pd.isnull(value) else value


class NewRental(Rental):
    """Data model for a new rental."""

    id: Optional[constr(to_upper=True, pattern=RENTAL_ID_PATTERN)] = Field(title="Rental ID", default=None)


class CompletedRental(RentalBase):
    """Data model for a completed rental"""
    name: constr(min_length=3) = Field(title="Name")
    device_id: constr(to_upper=True, pattern=DEVICE_ID_PATTERN) = Field(title="Device ID")
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
