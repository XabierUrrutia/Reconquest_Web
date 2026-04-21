from flask import Blueprint, request, session, jsonify, redirect, url_for

from ..db import db_execute, db_commit
from ..decorators import admin_required
from ..utils import _now


bp = Blueprint("bugs", __name__)


@bp.route("/api/bug", methods=["POST"])
def api_bug():
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    if not description or len(description) < 5:
        return jsonify({"ok": False, "error": "Descripción demasiado corta."}), 400
    if len(description) > 2000:
        return jsonify({"ok": False, "error": "Descripción demasiado larga."}), 400
    user_id = session.get("user_id")
    db_execute(
        "INSERT INTO bug_reports (user_id, description, created_at) VALUES (?,?,?)",
        (user_id, description, _now())
    )
    db_commit()
    return jsonify({"ok": True})


@bp.route("/admin/bug/<int:bid>/delete", methods=["POST"])
@admin_required
def admin_bug_delete(bid):
    db_execute("DELETE FROM bug_reports WHERE id=%s", (bid,))
    db_commit()
    return redirect(url_for("admin.admin_dashboard"))
