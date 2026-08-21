import os
from typing import Dict, Union

from ui.pdf_forms.base_pdf_form import BasePDFForm


# pylint: disable=too-few-public-methods
class ScooterPDFForm(BasePDFForm):
    """Class to fill out the scooter form with rental data"""

    _FILLABLE_FORM_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "assets/scooter_form_fillable.pdf"
    )

    def _create_form_field_values(self) -> Dict[str, Union[str, bool]]:
        """Create a dictionary of form fields to fill in the PDF"""
        phone_number_formatted = self.rental_data.phone_number.replace("tel:", "")
        field_values = {
            "rental_id": self.rental_id,
            "scooter_id": self.rental_data.device_id,
            "date": self.rental_data.date.strftime("%b %d, %Y"),
            "name": self.rental_data.name,
            "phone_number": phone_number_formatted,
            "address": self.rental_data.address,
            "city": self.rental_data.city,
            "province_state": self.rental_data.province,
            "postal_code": self.rental_data.postal_code,
            "country": self.rental_data.country,
            "fee": f"{self.rental_data.fee_payment_amount:.2f}",
            "fee_summary": str(self.rental_data.fee_payment_amount),
            "deposit": f"{self.rental_data.deposit_payment_amount:.2f}",
            "deposit_summary": str(self.rental_data.deposit_payment_amount),
            "id_verified": True,
        }
        # add fee and deposit payment method fields
        fee_payment_method_formatted = self.rental_data.fee_payment_method.lower().replace(" ", "_")
        deposit_payment_method_formatted = self.rental_data.deposit_payment_method.lower().replace(" ", "_")
        field_values[f"fee_payment_method_{fee_payment_method_formatted}"] = True
        field_values[f"deposit_payment_method_{deposit_payment_method_formatted}"] = True

        # format day as 1st, 2nd, 3rd, etc.
        day = self.rental_data.date.day
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][day % 10 - 1]
        field_values["date_day"] = self.rental_data.date.strftime("%-d") + suffix
        field_values["date_month"] = self.rental_data.date.strftime("%B")
        field_values["date_year"] = self.rental_data.date.strftime("%Y")
        return field_values
