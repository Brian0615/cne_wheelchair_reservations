import os

import pymupdf

from common.data_models.rental import NewRental
from common.utils import read_secret
from ui.src.signature import Signature


# pylint: disable=too-few-public-methods
class WheelchairForm:
    """Class to fill out the wheelchair form with rental data"""

    __FILLABLE_FORM_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "assets/wheelchair_form_fillable.pdf"
    )

    def __init__(self, rental_data: NewRental, rental_id: str):
        self.rental_data = rental_data
        self.rental_id = rental_id

    def export_form_to_bytes(self) -> bytes:
        """Create a PDF wheelchair form with the rental data, return the data as bytes"""
        field_values = {
            "rental_id": self.rental_id,
            "wheelchair_id": self.rental_data.device_id,
            "date": self.rental_data.date.strftime("%b %d, %Y"),
            "name": self.rental_data.name,
            "phone_number": self.rental_data.phone_number,
            "address": self.rental_data.address,
            "city": self.rental_data.city,
            "province_state": self.rental_data.province,
            "postal_code": self.rental_data.postal_code,
            "country": self.rental_data.country,
            "fee_payment_method": self.rental_data.fee_payment_method.lower().replace(" ", "_"),
            "deposit_payment_method": self.rental_data.deposit_payment_method.lower().replace(" ", "_"),
            "id_verified": "yes",
            "time_out": self.rental_data.pickup_time.strftime("%I:%M %p"),
            "staff_name": self.rental_data.staff_name,
            "rental_id_receipt": self.rental_id,
            "wheelchair_id_receipt": self.rental_data.device_id,
            "date_receipt": self.rental_data.date.strftime("%b %d, %Y"),
            "name_receipt": self.rental_data.name,
        }

        with pymupdf.open(WheelchairForm.__FILLABLE_FORM_PATH) as pdf:
            page = pdf[0]

            # fill in the form fields
            for widget in page.widgets():
                try:
                    widget.field_value = field_values[widget.field_name]
                    widget.update()
                except KeyError:
                    pass

            # insert the signature
            signature = Signature.decode_from_base64(self.rental_data.signature)
            height, width, _ = signature.size
            page.insert_image(pymupdf.Rect(78, 360, 78 + width * 29 / height, 389), stream=signature.to_bytes())
            page.insert_image(pymupdf.Rect(78, 690, 78 + width * 29 / height, 719), stream=signature.to_bytes())

            pdf_perm = int(pymupdf.PDF_PERM_PRINT)  # only allow print, and disable other PDF permissions

            return pdf.tobytes(
                deflate=True,
                garbage=4,
                use_objstms=1,
                permissions=pdf_perm,
                encryption=pymupdf.PDF_ENCRYPT_AES_256,
                owner_pw=read_secret(os.environ["PDF_PASSWORD"]),
                clean=True,
            )
