from pathlib import Path

from flask import Blueprint, Response, abort

bp = Blueprint("courses", __name__)

# Free study manuals -- one self-contained HTML document per exam, authored
# independently of the tutor, public with no login or subscription required.
COURSES_DIR = Path(__file__).resolve().parent.parent / "static_content" / "courses"

# Explicit exam_code -> filename mapping rather than a derived one -- keeps
# adding a new exam's manual a one-line addition (drop the file in, add its
# entry here) instead of depending on a naming convention holding forever.
_FILENAMES = {"P": "exam_p.html", "FM": "exam_fm.html", "FAM": "exam_fam.html"}


@bp.get("/<exam_code>")
def get_course(exam_code):
    filename = _FILENAMES.get(exam_code.upper())
    if filename is None:
        abort(404)
    return Response((COURSES_DIR / filename).read_text(encoding="utf-8"), mimetype="text/html")
