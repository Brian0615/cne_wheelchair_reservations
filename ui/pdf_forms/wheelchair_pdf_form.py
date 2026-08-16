import os
from typing import Dict

from ui.pdf_forms.base_pdf_form import BasePDFForm


# pylint: disable=too-few-public-methods
class WheelchairPDFForm(BasePDFForm):
    """Class to fill out the wheelchair form with rental data"""

    _FILLABLE_FORM_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "assets/wheelchair_form_fillable.pdf"
    )

    def _create_form_field_values(self) -> Dict[str, str]:
        """Create a dictionary of form fields to fill in the PDF"""
        phone_number_formatted = self.rental_data.phone_number.replace("tel:", "")
        field_values = {
            "rental_id": self.rental_id,
            "wheelchair_id": self.rental_data.device_id,
            "date": self.rental_data.date.strftime("%b %d, %Y"),
            "name": self.rental_data.name,
            "phone_number": phone_number_formatted,
            "address": self.rental_data.address,
            "city": self.rental_data.city,
            "province_state": self.rental_data.province,
            "postal_code": self.rental_data.postal_code,
            "country": self.rental_data.country,
            "fee": str(self.rental_data.fee_payment_amount),
            "deposit": str(self.rental_data.deposit_payment_amount),
            "id_verified": "yes",
            "pickup_time": self.rental_data.pickup_time.strftime("%I:%M %p"),
            "pickup_location": f"({self.rental_data.pickup_location.value})",
            "staff_name": self.rental_data.staff_name,
            "rental_id_receipt": self.rental_id,
            "wheelchair_id_receipt": self.rental_data.device_id,
            "date_receipt": self.rental_data.date.strftime("%b %d, %Y"),
            "name_receipt": self.rental_data.name,
            "phone_number_receipt": phone_number_formatted,
            "fee_receipt": str(self.rental_data.fee_payment_amount),
            "deposit_receipt": str(self.rental_data.deposit_payment_amount),
        }
        # add fee and deposit payment method fields
        fee_payment_method_formatted = self.rental_data.fee_payment_method.lower().replace(" ", "_")
        deposit_payment_method_formatted = self.rental_data.deposit_payment_method.lower().replace(" ", "_")
        field_values[f"fee_payment_method_{fee_payment_method_formatted}"] = "yes"
        field_values[f"deposit_payment_method_{deposit_payment_method_formatted}"] = "yes"
        field_values[f"fee_payment_method_receipt_{fee_payment_method_formatted}"] = "yes"
        field_values[f"deposit_payment_method_receipt_{deposit_payment_method_formatted}"] = "yes"
        return field_values
