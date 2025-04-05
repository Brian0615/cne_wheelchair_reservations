import pandas as pd
from pydantic import BaseModel, ConfigDict, constr, Field, field_validator, model_validator

from common.constants import (
    DeviceType,
    Location,
    DEVICE_ID_PATTERN,
    RENTAL_ID_PATTERN,
)
from common.data_models.fields import (
    CNEYearField,
    RentalIDField,
    RentalDateField,
    DeviceIDField,
    DeviceTypeField,
    ReservationIDField,
    PickupLocationField,
    PickupTimeField,
    RentalStatusField,
    NameField,
    PhoneNumberField,
    AddressField,
    CityField,
    ProvinceField,
    PostalCodeField,
    CountryField,
    FeePaymentMethodField,
    FeePaymentAmountField,
    DepositPaymentMethodField,
    DepositPaymentAmountField,
    ItemsLeftBehindField,
    NotesField,
    StaffNameField,
    SignatureField,
    ReturnLocationField,
    ReturnTimeField,
    ReturnStaffNameField,
    ReturnSignatureField,
)
from common.data_models.validators import check_device_id_and_type, check_reservation_id_and_type, \
    check_cne_year_and_date


class Rental(BaseModel):
    """Data model for a rental"""
    model_config = ConfigDict(extra="forbid", ser_json_bytes="utf8")

    cne_year: CNEYearField
    id: RentalIDField
    date: RentalDateField
    device_id: DeviceIDField
    device_type: DeviceTypeField
    reservation_id: ReservationIDField
    pickup_location: PickupLocationField
    pickup_time: PickupTimeField
    status: RentalStatusField

    name: NameField
    phone_number: PhoneNumberField
    address: AddressField
    city: CityField
    province: ProvinceField
    postal_code: PostalCodeField
    country: CountryField

    fee_payment_amount: FeePaymentAmountField
    fee_payment_method: FeePaymentMethodField
    deposit_payment_amount: DepositPaymentAmountField
    deposit_payment_method: DepositPaymentMethodField
    items_left_behind: ItemsLeftBehindField
    notes: NotesField
    staff_name: StaffNameField
    signature: SignatureField

    return_location: ReturnLocationField
    return_time: ReturnTimeField
    return_staff_name: ReturnStaffNameField
    return_signature: ReturnSignatureField

    # validators
    cne_year_and_date_validator = model_validator(mode="after")(check_cne_year_and_date)
    device_id_and_type_validator = model_validator(mode="after")(check_device_id_and_type)
    reservation_id_and_type_validator = model_validator(mode="after")(check_reservation_id_and_type)


class RentalSummary(BaseModel):
    """Data model for a base rental"""
    model_config = ConfigDict(extra="forbid", ser_json_bytes="utf8")

    cne_year: CNEYearField
    id: RentalIDField
    date: RentalDateField
    device_id: DeviceIDField
    device_type: DeviceTypeField
    reservation_id: ReservationIDField
    pickup_location: PickupLocationField
    pickup_time: PickupTimeField

    name: NameField
    phone_number: PhoneNumberField

    deposit_payment_method: DepositPaymentMethodField
    items_left_behind: ItemsLeftBehindField
    notes: NotesField

    return_location: ReturnLocationField
    return_time: ReturnTimeField

    # validators
    cne_year_and_date_validator = model_validator(mode="after")(check_cne_year_and_date)
    device_id_and_type_validator = model_validator(mode="after")(check_device_id_and_type)

    # validator to convert pandas NaT to None
    @field_validator("return_time", mode="before")
    @classmethod
    def convert_nat_to_none(cls, value):
        """Convert pandas NaT to None"""
        return None if pd.isnull(value) else value


class NewRental(BaseModel):
    """Data model for a new rental."""
    model_config = ConfigDict(extra="forbid", ser_json_bytes="utf8")

    cne_year: CNEYearField
    date: RentalDateField
    device_id: DeviceIDField
    device_type: DeviceTypeField
    reservation_id: ReservationIDField
    pickup_location: PickupLocationField
    pickup_time: PickupTimeField
    status: RentalStatusField

    name: NameField
    phone_number: PhoneNumberField
    address: AddressField
    city: CityField
    province: ProvinceField
    postal_code: PostalCodeField
    country: CountryField

    fee_payment_amount: FeePaymentAmountField
    fee_payment_method: FeePaymentMethodField
    deposit_payment_amount: DepositPaymentAmountField
    deposit_payment_method: DepositPaymentMethodField
    items_left_behind: ItemsLeftBehindField
    notes: NotesField
    staff_name: StaffNameField
    signature: SignatureField

    return_location: ReturnLocationField
    return_time: ReturnTimeField
    return_staff_name: ReturnStaffNameField
    return_signature: ReturnSignatureField

    # validators
    cne_year_and_date_validator = model_validator(mode="after")(check_cne_year_and_date)
    device_id_and_type_validator = model_validator(mode="after")(check_device_id_and_type)
    reservation_id_and_type_validator = model_validator(mode="after")(check_reservation_id_and_type)


class CompletedRental(BaseModel):
    """Data model for a completed rental"""
    model_config = ConfigDict(extra="forbid", ser_json_bytes="utf8")

    cne_year: CNEYearField
    id: RentalIDField
    date: RentalDateField
    device_id: DeviceIDField
    reservation_id: ReservationIDField

    name: NameField

    return_location: ReturnLocationField
    return_time: ReturnTimeField
    return_staff_name: ReturnStaffNameField
    return_signature: ReturnSignatureField

    # validators
    cne_year_and_date_validator = model_validator(mode="after")(check_cne_year_and_date)


class ChangeDeviceInfo(BaseModel):
    """Data model for changing device info"""
    rental_id: constr(to_upper=True, pattern=RENTAL_ID_PATTERN) = Field(title="Rental ID")
    device_type: DeviceType = Field(title="Device Type")
    location: Location = Field(title="Location")
    old_device_id: constr(to_upper=True, pattern=DEVICE_ID_PATTERN) = Field(title="Old Device ID")
    new_device_id: constr(to_upper=True, pattern=DEVICE_ID_PATTERN) = Field(title="New Device ID")
    staff_name: constr(min_length=5) = Field(title="Staff Name")
