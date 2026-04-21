from flask import Blueprint, render_template, redirect, url_for, session, flash, jsonify

from ..config import GAME_VERSION
from ..db import db_fetchone, db_fetchall, db_execute, db_commit
from ..decorators import admin_required


bp = Blueprint("admin", __name__)


@bp.route("/admin")
@admin_required
def admin_dashboard():
    users = db_fetchall(
        "SELECT id,username,email,is_admin,is_active,created_at,last_login FROM users ORDER BY created_at DESC"
    )
    recent_dls = db_fetchall(
        """SELECT d.ts, d.ip, u.username
           FROM download_log d LEFT JOIN users u ON d.user_id=u.id
           ORDER BY d.ts DESC LIMIT 25"""
    )
    bug_reports = db_fetchall(
        """SELECT b.id, b.description, b.created_at, u.username
           FROM bug_reports b LEFT JOIN users u ON b.user_id=u.id
           ORDER BY b.created_at DESC"""
    )
    dl_row = db_fetchone("SELECT COUNT(*) as cnt FROM download_log")
    total_downloads = dl_row["cnt"] if dl_row else 0

    return render_template("admin.html",
        users=users,
        total_users=len(users),
        active_users=sum(1 for u in users if u["is_active"]),
        total_downloads=total_downloads,
        recent_dls=recent_dls,
        version=GAME_VERSION,
        bug_reports=bug_reports,
    )


@bp.route("/admin/user/<int:uid>/toggle", methods=["POST"])
@admin_required
def admin_toggle(uid):
    if uid == session["user_id"]:
        flash("No puedes desactivarte a ti mismo.", "error")
    else:
        db_execute("UPDATE users SET is_active = 1 - is_active WHERE id=%s", (uid,))
        db_commit()
    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/user/<int:uid>/delete", methods=["POST"])
@admin_required
def admin_delete(uid):
    if uid == session["user_id"]:
        flash("No puedes eliminarte a ti mismo.", "error")
    else:
        db_execute("DELETE FROM users WHERE id=%s", (uid,))
        db_execute("DELETE FROM reset_tokens WHERE user_id=%s", (uid,))
        db_commit()
    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/user/<int:uid>/toggle_admin", methods=["POST"])
@admin_required
def admin_toggle_admin(uid):
    if uid != session["user_id"]:
        db_execute("UPDATE users SET is_admin = 1 - is_admin WHERE id=%s", (uid,))
        db_commit()
    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/api/stats")
@admin_required
def api_stats():
    dl_row   = db_fetchone("SELECT COUNT(*) as cnt FROM download_log")
    user_row = db_fetchone("SELECT COUNT(*) as cnt FROM users")
    active_row = db_fetchone("SELECT COUNT(*) as cnt FROM users WHERE is_active=1")
    return jsonify({
        "total_downloads": dl_row["cnt"] if dl_row else 0,
        "total_users":     user_row["cnt"] if user_row else 0,
        "active_users":    active_row["cnt"] if active_row else 0,
    })


@bp.route("/api/admin/downloads_chart")
@admin_required
def api_downloads_chart():
    rows = db_fetchall(
        """SELECT substr(ts,1,10) as day, COUNT(*) as cnt
           FROM download_log
           GROUP BY day
           ORDER BY day ASC
           LIMIT 30"""
    )
    return jsonify({
        "labels": [r["day"] for r in rows],
        "data":   [r["cnt"] for r in rows],
    })
