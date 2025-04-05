import datetime
from typing import Annotated, Optional, List

from pydantic import Field, StringConstraints, AwareDatetime, conint

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

CNEYearField = Annotated[int, Field(title="CNE Year", gt=2000)]
RentalIDField = Annotated[str, StringConstraints(to_upper=True, pattern=RENTAL_ID_PATTERN), Field(title="Rental ID")]
RentalDateField = Annotated[datetime.date, Field(title="Rental Date")]
DeviceIDField = Annotated[str, StringConstraints(to_upper=True, pattern=DEVICE_ID_PATTERN), Field(title="Device ID")]
DeviceTypeField = Annotated[DeviceType, Field(title="Device Type")]
ReservationIDField = Annotated[
    Optional[str],
    StringConstraints(pattern=RESERVATION_ID_PATTERN), Field(title="Reservation ID", default=None),
]
PickupLocationField = Annotated[Location, Field(title="Pickup Location")]
PickupTimeField = Annotated[AwareDatetime, Field(title="Pickup Time")]
RentalStatusField = Annotated[RentalStatus, Field(title="Status")]
NameField = Annotated[str, StringConstraints(min_length=3), Field(title="Name")]
PhoneNumberField = Annotated[str, StringConstraints(min_length=5), Field(title="Phone Number")]
AddressField = Annotated[str, StringConstraints(min_length=5, strip_whitespace=True), Field(title="Address")]
CityField = Annotated[str, StringConstraints(min_length=5), Field(title="City")]
ProvinceField = Annotated[str, StringConstraints(min_length=2), Field(title="Province")]
PostalCodeField = Annotated[Optional[str], StringConstraints(min_length=3), Field(title="Postal Code", default=None)]
CountryField = Annotated[str, StringConstraints(min_length=3), Field(title="Country")]
FeePaymentMethodField = Annotated[PaymentMethod, Field(title="Fee Payment Method")]
FeePaymentAmountField = Annotated[conint(gt=0), Field(title="Fee Payment Amount")]
DepositPaymentMethodField = Annotated[PaymentMethod, Field(title="Deposit Payment Method")]
DepositPaymentAmountField = Annotated[conint(gt=0), Field(title="Deposit Payment Amount")]
ItemsLeftBehindField = Annotated[List[HoldItem], Field(title="Items Left Behind", default=[])]
NotesField = Annotated[Optional[str], Field(title="Notes", default=None)]
StaffNameField = Annotated[str, StringConstraints(min_length=5), Field(title="Staff Name")]
SignatureField = Annotated[bytes, Field(title="Signature")]
ReturnLocationField = Annotated[Optional[Location], Field(title="Return Location", default=None)]
ReturnTimeField = Annotated[Optional[AwareDatetime], Field(title="Return Time", default=None)]
ReturnStaffNameField = Annotated[
    Optional[str],
    StringConstraints(min_length=5), Field(title="Return Staff Name", default=None),
]
ReturnSignatureField = Annotated[Optional[bytes], Field(title="Return Signature", default=None)]
LocationField = Annotated[Location, Field(title="Location")]
