"""Add AcroForm fields to the blank rental form PDFs exported from Word.

The Word exports in ``ui/assets/*_form_v2.pdf`` have no form fields, only underscore
runs and blank spaces where values belong. This script locates those blanks by the
text that precedes them and writes a widget over each one, producing the
``ui/assets/*_form_fillable.pdf`` files that ``ui/pdf_forms/`` fills at runtime.

Re-run it whenever the Word source is re-exported:

    python scripts/build_fillable_forms.py
"""

import os
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

import pymupdf

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "assets")

# PyMuPDF only emits the base-14 font names below in a widget's /DA string; Aptos (the
# font used throughout the Word sources) and its bold variant are not available, so
# fields fall back to Helvetica/Courier to match the v1 fillable forms.
HELVETICA = "Helv"
COURIER = "Cour"

# A blank is either a run of underscores or, for the "($   )" amounts, a run of spaces.
UNDERSCORE = "underscore"
SPACE = "space"

# (preceding text on the line, rect covering the blank)
Blank = Tuple[str, pymupdf.Rect]


@dataclass
class BlankRef:
    """Where in the page text a widget belongs."""
    # The text immediately preceding the blank, e.g. "Rental ID:  ".
    preceded_by: str
    occurrence: int = 0
    # Require the preceding text to be the whole line prefix rather than just its tail,
    # so that "Name:  " does not also match the "Staff Name:  " blank.
    at_line_start: bool = False
    kind: str = UNDERSCORE
    # Some blanks hold two values side by side (e.g. a time then a location); these trim
    # the located rect down to a sub-range measured in points from its left or right edge.
    from_left: Optional[float] = None
    from_right: Optional[float] = None
    # Widen the rect past the end of the blank, for values that need more room than the
    # underscores allow (the v1 forms did the same).
    extend_right: float = 0.0


@dataclass
class TextField:
    """A text widget to place over a blank."""
    name: str
    font: str
    size: float
    blank: Optional[BlankRef] = None
    # Fields with no blank in the source text are positioned explicitly.
    rect: Optional[Tuple[float, float, float, float]] = None


@dataclass
class CheckBoxRow:
    """A row of checkboxes sharing a baseline, one per space run at the given positions."""
    y_top: float
    names: List[str] = field(default_factory=list)
    x_positions: List[float] = field(default_factory=list)


@dataclass
class FormSpec:
    """Everything needed to turn one blank export into a fillable form."""
    source: str
    output: str
    text_fields: List[TextField]
    checkbox_rows: List[CheckBoxRow]
    checkbox_size: float
    checkbox_dx: float


def _char_runs(page: pymupdf.Page, matches: Callable[[str], bool], min_length: int) -> List[Blank]:
    """Find every maximal run of matching characters, with the text preceding it."""
    results = []
    for block in page.get_text("rawdict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            chars = [char for span in line["spans"] for char in span["chars"]]
            index = 0
            while index < len(chars):
                if not matches(chars[index]["c"]):
                    index += 1
                    continue
                end = index
                while end < len(chars) and matches(chars[end]["c"]):
                    end += 1
                if end - index >= min_length:
                    rect = pymupdf.Rect(chars[index]["bbox"])
                    for position in range(index, end):
                        rect |= pymupdf.Rect(chars[position]["bbox"])
                    results.append(("".join(char["c"] for char in chars[:index]), rect))
                index = end
    return sorted(results, key=lambda blank: (round(blank[1].y0), blank[1].x0))


def _find_blanks(page: pymupdf.Page) -> dict:
    """Collect the underscore and space runs on the page, keyed by kind."""
    return {
        UNDERSCORE: _char_runs(page, lambda char: char == "_", min_length=3),
        SPACE: _char_runs(page, lambda char: char == " ", min_length=5),
    }


def _locate(blanks: dict, name: str, ref: BlankRef) -> pymupdf.Rect:
    """Return the rect of the blank that ``ref`` describes, trimmed to its sub-range."""
    if ref.at_line_start:
        hits = [rect for preceding, rect in blanks[ref.kind] if preceding == ref.preceded_by]
    else:
        hits = [rect for preceding, rect in blanks[ref.kind] if preceding.endswith(ref.preceded_by)]
    if len(hits) <= ref.occurrence:
        raise ValueError(
            f"Found {len(hits)} blank(s) for {name!r} preceded by {ref.preceded_by!r}, "
            f"needed at least {ref.occurrence + 1}"
        )

    rect = hits[ref.occurrence]
    if ref.from_left is not None:
        rect = pymupdf.Rect(rect.x0, rect.y0, rect.x0 + ref.from_left, rect.y1)
    elif ref.from_right is not None:
        rect = pymupdf.Rect(rect.x1 - ref.from_right, rect.y0, rect.x1, rect.y1)
    return pymupdf.Rect(rect.x0, rect.y0, rect.x1 + ref.extend_right, rect.y1)


def _add_text_field(page: pymupdf.Page, text_field: TextField, rect: pymupdf.Rect) -> None:
    """Add a text widget, growing the rect vertically if the blank is shorter than the font."""
    minimum_height = text_field.size * 1.35
    if rect.height < minimum_height:
        padding = (minimum_height - rect.height) / 2
        rect = pymupdf.Rect(rect.x0, rect.y0 - padding, rect.x1, rect.y1 + padding)

    widget = pymupdf.Widget()
    widget.field_name = text_field.name
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT  # pylint: disable=no-member
    widget.rect = rect
    widget.text_font = text_field.font
    widget.text_fontsize = text_field.size
    widget.border_width = 0
    page.add_widget(widget)


def _add_checkbox_row(page: pymupdf.Page, spec: FormSpec, row: CheckBoxRow, blanks: dict) -> None:
    """Add one checkbox per named position on a row of the form."""
    on_row = [rect for _, rect in blanks[SPACE] if abs(rect.y0 - row.y_top) < 1]
    for name, x_position in zip(row.names, row.x_positions):
        match = next((rect for rect in on_row if abs(rect.x0 - x_position) < 1), None)
        if match is None:
            raise ValueError(f"No blank at x={x_position} on the row at y={row.y_top} for {name}")
        x0 = match.x0 + spec.checkbox_dx
        y0 = (match.y0 + match.y1 - spec.checkbox_size) / 2

        widget = pymupdf.Widget()
        widget.field_name = name
        widget.field_type = pymupdf.PDF_WIDGET_TYPE_CHECKBOX  # pylint: disable=no-member
        widget.rect = pymupdf.Rect(x0, y0, x0 + spec.checkbox_size, y0 + spec.checkbox_size)
        widget.field_value = False
        widget.border_width = 0
        page.add_widget(widget)


def build_form(spec: FormSpec) -> int:
    """Write the widgets described by ``spec`` into a copy of its source PDF."""
    with pymupdf.open(os.path.join(ASSETS_DIR, spec.source)) as pdf:
        page = pdf[0]
        if list(page.widgets()):
            raise ValueError(f"{spec.source} already has form fields; expected a blank export")

        blanks = _find_blanks(page)
        for text_field in spec.text_fields:
            if text_field.rect is not None:
                rect = pymupdf.Rect(text_field.rect)
            else:
                rect = _locate(blanks, text_field.name, text_field.blank)
            _add_text_field(page, text_field, rect)

        for row in spec.checkbox_rows:
            _add_checkbox_row(page, spec, row, blanks)

        count = len(list(page.widgets()))
        pdf.save(os.path.join(ASSETS_DIR, spec.output), deflate=True, garbage=4, clean=True)
    return count


WHEELCHAIR_FORM = FormSpec(
    source="wheelchair_form_v2.pdf",
    output="wheelchair_form_fillable.pdf",
    checkbox_size=11.0,
    checkbox_dx=0.2,
    text_fields=[
        # rental copy
        TextField("rental_id", COURIER, 12, BlankRef("Rental ID:  ")),
        TextField("wheelchair_id", COURIER, 12, BlankRef("Wheelchair #:  ")),
        TextField("date", HELVETICA, 12, BlankRef("Date:  ")),
        TextField("name", HELVETICA, 12, BlankRef("Name:  ", at_line_start=True)),
        TextField("phone_number", COURIER, 12, BlankRef("Phone:  ")),
        TextField("address", HELVETICA, 12, BlankRef("Address:  ")),
        TextField("city", HELVETICA, 12, BlankRef("City:  ")),
        TextField("province_state", HELVETICA, 12, BlankRef("Province:  ")),
        TextField("postal_code", HELVETICA, 12, BlankRef("Postal Code:  ")),
        TextField("country", HELVETICA, 12, BlankRef("Country:  ")),
        TextField("fee", HELVETICA, 12, BlankRef("Fee ($", kind=SPACE)),
        TextField("deposit", HELVETICA, 12, BlankRef("Deposit ($", kind=SPACE)),
        # "Time Out" and "Time In" each hold a time then a location on one blank
        TextField("pickup_time", COURIER, 12, BlankRef("Time Out:  ", from_left=60)),
        TextField("pickup_location", COURIER, 12, BlankRef("Time Out:  ", from_right=39)),
        TextField("return_time", COURIER, 12, BlankRef("Time In:  ", from_left=60)),
        TextField("return_location", COURIER, 12, BlankRef("Time In:  ", from_right=39)),
        # "Staff" uses an ff ligature whose ToUnicode mapping extracts as a capital I
        TextField("staff_name", HELVETICA, 12, BlankRef("StaI Name:  ")),
        # receipt copy
        TextField("rental_id_receipt", COURIER, 12, BlankRef("Rental ID:  ", occurrence=1)),
        TextField("wheelchair_id_receipt", COURIER, 12, BlankRef("Wheelchair #:  ", occurrence=1)),
        TextField("date_receipt", HELVETICA, 12, BlankRef("Date:  ", occurrence=1)),
        TextField("name_receipt", HELVETICA, 12, BlankRef("Name:  ", occurrence=1, at_line_start=True)),
        TextField("phone_number_receipt", COURIER, 12, BlankRef("Phone:  ", occurrence=1)),
        TextField("fee_receipt", HELVETICA, 12, BlankRef("Fee ($", occurrence=1, kind=SPACE)),
        TextField("deposit_receipt", HELVETICA, 12, BlankRef("Deposit ($", occurrence=1, kind=SPACE)),
    ],
    checkbox_rows=[
        CheckBoxRow(
            y_top=148.6,
            names=["fee_payment_method_cash", "fee_payment_method_credit_card", "fee_payment_method_debit_card"],
            x_positions=[226.8, 339.8, 453.1],
        ),
        CheckBoxRow(
            y_top=166.8,
            names=["deposit_payment_method_cash", "deposit_payment_method_credit_card"],
            x_positions=[226.8, 339.8],
        ),
        CheckBoxRow(y_top=185.3, names=["id_verified"], x_positions=[226.8]),
        CheckBoxRow(
            y_top=501.4,
            names=[
                "fee_payment_method_receipt_cash",
                "fee_payment_method_receipt_credit_card",
                "fee_payment_method_receipt_debit_card",
            ],
            x_positions=[226.8, 339.8, 453.1],
        ),
        CheckBoxRow(
            y_top=519.8,
            names=["deposit_payment_method_receipt_cash", "deposit_payment_method_receipt_credit_card"],
            x_positions=[226.8, 339.8],
        ),
    ],
)

SCOOTER_FORM = FormSpec(
    source="scooter_form_v2.pdf",
    output="scooter_form_fillable.pdf",
    checkbox_size=10.7,
    checkbox_dx=0.9,
    text_fields=[
        # the "SCOOTER #" and "RENTAL ID" labels are not followed by a blank, so these
        # keep the rects used by the v1 fillable form
        TextField("scooter_id", COURIER, 16, rect=(124.0, 101.0, 154.5, 126.0)),
        TextField("rental_id", COURIER, 16, rect=(123.5, 132.0, 206.5, 157.0)),
        TextField("name", HELVETICA, 14, BlankRef("NAME:  ")),
        # the underscores stop ~2pt short of a full phone number at Courier 14
        TextField("phone_number", COURIER, 14, BlankRef("PHONE:  ", extend_right=12)),
        TextField("address", HELVETICA, 14, BlankRef("ADDRESS:  ")),
        TextField("city", HELVETICA, 14, BlankRef("CITY:  ")),
        TextField("province_state", HELVETICA, 14, BlankRef("PROVINCE:  ")),
        TextField("postal_code", HELVETICA, 14, BlankRef("POSTAL CODE:  ")),
        TextField("country", HELVETICA, 14, BlankRef("COUNTRY: ")),
        TextField("date", HELVETICA, 14, BlankRef("from the Association on   ")),
        TextField("fee", HELVETICA, 10.1, BlankRef("for the sum of $")),
        TextField("deposit", HELVETICA, 10.1, BlankRef("in the amount of $")),
        TextField("date_day", HELVETICA, 14, BlankRef("Dated this ")),
        TextField("date_month", HELVETICA, 14, BlankRef(" day of ")),
        TextField("date_year", HELVETICA, 12, BlankRef(" , ")),
        TextField("deposit_summary", HELVETICA, 11, BlankRef("DEPOSIT ($", kind=SPACE)),
        TextField("fee_summary", HELVETICA, 11, BlankRef("FEE ($", kind=SPACE)),
    ],
    checkbox_rows=[
        CheckBoxRow(y_top=693.3, names=["id_verified"], x_positions=[213.1]),
        CheckBoxRow(
            y_top=712.7,
            names=["deposit_payment_method_cash", "deposit_payment_method_credit_card"],
            x_positions=[213.1, 310.6],
        ),
        CheckBoxRow(
            y_top=732.2,
            names=["fee_payment_method_cash", "fee_payment_method_credit_card", "fee_payment_method_debit_card"],
            x_positions=[213.1, 310.6, 408.0],
        ),
    ],
)


def main() -> None:
    """Rebuild both fillable forms from their blank exports."""
    for spec in (WHEELCHAIR_FORM, SCOOTER_FORM):
        count = build_form(spec)
        print(f"{spec.source} -> {spec.output}: {count} fields")


if __name__ == "__main__":
    main()
