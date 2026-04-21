from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify

from ..config import (GAME_VERSION, INSTALLER_URL_WIN, INSTALLER_URL_LNX)
from ..db import db_fetchone, db_fetchall, db_execute, db_commit
from ..decorators import login_required, current_user
from ..utils import detect_client_os, is_mobile, _now


bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    reviews = db_fetchall(
        """SELECT r.rating, r.body, r.created_at, u.username
           FROM reviews r JOIN users u ON r.user_id=u.id
           WHERE r.approved=1 ORDER BY r.created_at DESC"""
    )
    avg_rating = None
    if reviews:
        avg_rating = round(sum(r["rating"] for r in reviews) / len(reviews), 1)
    user = current_user()
    user_reviewed = False
    if user:
        user_reviewed = bool(db_fetchone(
            "SELECT id FROM reviews WHERE user_id=%s", (user["id"],)
        ))
    dl_row = db_fetchone("SELECT COUNT(*) as cnt FROM download_log")
    total_downloads = dl_row["cnt"] if dl_row else 0

    client_os = detect_client_os(request.user_agent.string)
    mobile    = is_mobile(client_os)

    return render_template("index.html",
        version=GAME_VERSION,
        downloads=total_downloads,
        installer_exists=True,
        installer_size=None,
        user=user,
        reviews=reviews,
        avg_rating=avg_rating,
        user_reviewed=user_reviewed,
        client_os=client_os,
        mobile=mobile,
    )


@bp.route("/download")
@login_required
def download():
    client_os = detect_client_os(request.user_agent.string)
    if is_mobile(client_os) or client_os == "mac":
        flash("Reconquest solo está disponible para PC (Windows/Linux).", "error")
        return redirect(url_for("main.index"))

    db_execute(
        "INSERT INTO download_log (user_id,ip,user_agent,ts) VALUES (?,?,?,?)",
        (session["user_id"], request.remote_addr, request.user_agent.string[:120], _now())
    )
    db_commit()

    if client_os == "linux":
        return redirect(INSTALLER_URL_LNX)
    return redirect(INSTALLER_URL_WIN)


@bp.route("/api/version")
def api_version():
    return jsonify({"version": GAME_VERSION, "available": True})
