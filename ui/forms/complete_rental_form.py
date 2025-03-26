from common.constants import DeviceType
from common.data_models import RentalSummary
from ui.forms.base_form import BaseForm
from ui.forms.form_fields import (
    ButtonField,
    CheckboxField,
    DateField,
    TimeField,
    SelectboxField,
    TextField,
    SignatureField,
)


# pylint: disable=too-few-public-methods
class CompleteRentalForm(BaseForm):
    """Form for completing a rental"""

    def __init__(self, key_prefix: str, rental_info: RentalSummary):
        self.rental_info = rental_info

        fields = {
            "date": DateField(key=f"{key_prefix}_date", label="Rental Date"),
            "return_date": DateField(
                key=f"{key_prefix}_return_date",
                label="Return Date",
                default_value=self.rental_info.date,
            ),
            "return_time": TimeField(key=f"{key_prefix}_return_time", label="Return Time"),
            "return_location": SelectboxField(key=f"{key_prefix}_return_location", label="Return Location"),
            "return_signature": SignatureField(key=f"{key_prefix}_return_signature", label="Signature"),
            "return_staff_name": TextField(key=f"{key_prefix}_staff_name", label="Staff Name"),
            "deposit_received": CheckboxField(
                key=f"{key_prefix}_deposit_received",
                label=f"{self.rental_info.deposit_payment_method} Deposit of "
                      f"${DeviceType.get_deposit_amount(self.rental_info.device_type)}",
            ),
            "submit": ButtonField(key=f"{key_prefix}_submit", label="Complete Rental"),
        }
        if self.rental_info.items_left_behind:
            fields["items_left_behind"] = CheckboxField(
                key=f"{key_prefix}_items_left_behind",
                label="Items Left Behind during Rental: " + ", ".join(self.rental_info.items_left_behind),
            )
        super().__init__(fields=fields, key_prefix=key_prefix)
