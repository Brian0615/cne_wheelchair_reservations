import pandas as pd
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from common.data_models.fields import (
    AddressField,
    CityField,
    CNEYearField,
    CountryField,
    DepositPaymentAmountField,
    DepositPaymentMethodField,
    DeviceIDField,
    DeviceTypeField,
    FeePaymentAmountField,
    FeePaymentMethodField,
    ItemsLeftBehindField,
    LocationField,
    NameField,
    NewDeviceIDField,
    NotesField,
    OldDeviceIDField,
    PhoneNumberField,
    PickupLocationField,
    PickupTimeField,
    PostalCodeField,
    ProvinceField,
    RentalDateField,
    RentalIDField,
    RentalStatusField,
    ReservationIDField,
    ReturnLocationField,
    ReturnStaffNameField,
    ReturnTimeField,
    StaffNameField,
)
from common.data_models.validators import (
    check_cne_year_and_date,
    check_country_code,
    check_device_id_and_type,
    check_province_state,
    check_reservation_id_and_type,
    check_postal_code,
)


class ChangeDeviceInfo(BaseModel):
    """Data model for changing device info"""

    cne_year: CNEYearField
    date: RentalDateField
    id: RentalIDField
    device_type: DeviceTypeField
    location: LocationField
    old_device_id: OldDeviceIDField
    new_device_id: NewDeviceIDField
    staff_name: StaffNameField


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

    return_location: ReturnLocationField
    return_time: ReturnTimeField
    return_staff_name: ReturnStaffNameField

    # validators
    check_postal_code_validator = model_validator(mode="after")(check_postal_code)
    cne_year_and_date_validator = model_validator(mode="after")(check_cne_year_and_date)
    country_validator = field_validator("country", mode="before")(check_country_code)
    province_validator = model_validator(mode="after")(check_province_state)
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

    # validators
    cne_year_and_date_validator = model_validator(mode="after")(check_cne_year_and_date)


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

    return_location: ReturnLocationField
    return_time: ReturnTimeField
    return_staff_name: ReturnStaffNameField

    # validators
    check_postal_code_validator = model_validator(mode="after")(check_postal_code)
    cne_year_and_date_validator = model_validator(mode="after")(check_cne_year_and_date)
    province_validator = model_validator(mode="after")(check_province_state)
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
    status: RentalStatusField

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

    # validator to convert pandas NaT/NA to None for all optional fields
    @field_validator("return_time", "return_location", "notes", mode="before")
    @classmethod
    def convert_nat_to_none(cls, value):
        """Convert pandas NaT/NA to None"""
        try:
            return None if pd.isna(value) else value
        except (TypeError, ValueError):
            return value
