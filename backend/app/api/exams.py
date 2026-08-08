from flask import Blueprint, jsonify

from app.models.exam import Exam

bp = Blueprint("exams", __name__)


@bp.get("")
def list_exams():
    exams = Exam.query.order_by(Exam.code).all()
    return jsonify(exams=[{"code": e.code, "name": e.name} for e in exams])
