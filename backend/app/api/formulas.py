from pathlib import Path

from flask import Blueprint, Response, abort

bp = Blueprint("formulas", __name__)

# Formula sheets -- one self-contained HTML document per exam, same
# treatment as the study manuals (see courses.py): public, no login or
# subscription required.
FORMULAS_DIR = Path(__file__).resolve().parent.parent / "static_content" / "formulas"

# Explicit exam_code -> filename mapping rather than a derived one -- keeps
# adding a new exam's formula sheet a one-line addition (drop the file in,
# add its entry here) instead of depending on a naming convention holding
# forever.
_FILENAMES = {"P": "exam_p.html", "FM": "exam_fm.html", "FAM": "exam_fam.html"}


@bp.get("/<exam_code>")
def get_formula_sheet(exam_code):
    filename = _FILENAMES.get(exam_code.upper())
    if filename is None:
        abort(404)
    return Response((FORMULAS_DIR / filename).read_text(encoding="utf-8"), mimetype="text/html")
