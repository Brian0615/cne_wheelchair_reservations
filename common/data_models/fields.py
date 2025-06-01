import datetime
from typing import Annotated, List, Optional

from pydantic import Field, StringConstraints, AwareDatetime, conint
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator

from common.constants import (
    RENTAL_ID_PATTERN,
    DEVICE_ID_PATTERN,
    DeviceType,
    RESERVATION_ID_PATTERN,
    Location,
    RentalStatus,
    PaymentMethod,
    HoldItem,
)

AddressField = Annotated[str, StringConstraints(min_length=5, strip_whitespace=True), Field(title="Address")]
CNEYearField = Annotated[int, Field(title="CNE Year", gt=2000)]
CityField = Annotated[str, StringConstraints(min_length=5), Field(title="City")]
CountryField = Annotated[str, StringConstraints(min_length=3), Field(title="Country")]
DepositPaymentMethodField = Annotated[PaymentMethod, Field(title="Deposit Payment Method")]
DepositPaymentAmountField = Annotated[conint(gt=0), Field(title="Deposit Payment Amount")]
DeviceIDField = Annotated[str, StringConstraints(to_upper=True, pattern=DEVICE_ID_PATTERN), Field(title="Device ID")]
DeviceTypeField = Annotated[DeviceType, Field(title="Device Type")]
FeePaymentMethodField = Annotated[PaymentMethod, Field(title="Fee Payment Method")]
FeePaymentAmountField = Annotated[conint(gt=0), Field(title="Fee Payment Amount")]
ItemsLeftBehindField = Annotated[List[HoldItem], Field(title="Items Left Behind", default=[])]
LocationField = Annotated[Location, Field(title="Location")]
NameField = Annotated[str, StringConstraints(min_length=3), Field(title="Name")]
NewDeviceIDField = Annotated[DeviceIDField, Field(title="New Device ID")]
NotesField = Annotated[Optional[str], Field(title="Notes", default=None)]
OldDeviceIDField = Annotated[DeviceIDField, Field(title="Old Device ID")]
PhoneNumberField = Annotated[PhoneNumber, PhoneNumberValidator(default_region="CA"), Field(title="Phone Number")]
PickupLocationField = Annotated[Location, Field(title="Pickup Location")]
PickupTimeField = Annotated[AwareDatetime, Field(title="Pickup Time")]
PostalCodeField = Annotated[Optional[str], StringConstraints(min_length=3), Field(title="Postal Code", default=None)]
ProvinceField = Annotated[str, StringConstraints(min_length=2), Field(title="Province")]
RentalDateField = Annotated[datetime.date, Field(title="Rental Date")]
RentalIDField = Annotated[str, StringConstraints(to_upper=True, pattern=RENTAL_ID_PATTERN), Field(title="Rental ID")]
RentalStatusField = Annotated[RentalStatus, Field(title="Status")]
ReservationIDField = Annotated[
    Optional[str],
    StringConstraints(pattern=RESERVATION_ID_PATTERN), Field(title="Reservation ID", default=None),
]
ReturnLocationField = Annotated[Optional[Location], Field(title="Return Location", default=None)]
ReturnSignatureField = Annotated[Optional[bytes], Field(title="Return Signature", default=None)]
ReturnStaffNameField = Annotated[
    Optional[str],
    StringConstraints(min_length=5), Field(title="Return Staff Name", default=None),
]
ReturnTimeField = Annotated[Optional[AwareDatetime], Field(title="Return Time", default=None)]
SignatureField = Annotated[bytes, Field(title="Signature")]
StaffNameField = Annotated[str, StringConstraints(min_length=5), Field(title="Staff Name")]
