import pymupdf

from common.data_models.rental import NewRental
from common.logger import initialize_logger

logger = initialize_logger()


# pylint: disable=too-few-public-methods
class BasePDFForm:
    """Base class for PDF forms to fill out with rental data"""
    _FILLABLE_FORM_PATH = None

    def __init__(self, rental_data: NewRental, rental_id: str):
        self.rental_data = rental_data
        self.rental_id = rental_id

    def _create_form_field_values(self):
        """Create a dictionary of form fields to fill in the PDF"""
        raise NotImplementedError("Subclasses must implement this method")

    def export_form_to_bytes(self) -> bytes:
        """Create a PDF form with the rental data, return the data as bytes"""
        try:
            field_values = self._create_form_field_values()

            with pymupdf.open(self._FILLABLE_FORM_PATH) as pdf:
                page = pdf[0]

                # fill in the form fields
                for widget in page.widgets():
                    try:
                        widget.field_value = field_values[widget.field_name]
                        widget.update()
                    except KeyError:
                        pass

                # pylint: disable=no-member
                pdf_perm = int(pymupdf.PDF_PERM_PRINT)  # only allow print, and disable other PDF permissions

                # pylint: disable=no-member
                pdf_bytes = pdf.tobytes(
                    deflate=True,
                    garbage=4,
                    use_objstms=1,
                    permissions=pdf_perm,
                    encryption=pymupdf.PDF_ENCRYPT_AES_256,
                    clean=True,
                )
        except Exception:
            logger.exception(
                "PDF form generation failed",
                extra={"rental_id": self.rental_id, "form": type(self).__name__},
            )
            raise
        logger.info(
            "PDF form generated",
            extra={"rental_id": self.rental_id, "form": type(self).__name__},
        )
        return pdf_bytes
