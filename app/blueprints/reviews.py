from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

from ..db import db_fetchone, db_fetchall, db_execute, db_commit
from ..decorators import login_required, admin_required
from ..utils import _now
from ..ai import review_is_clean
from ..moderation import contains_profanity


bp = Blueprint("reviews", __name__)


@bp.route("/reviews/submit", methods=["POST"])
@login_required
def review_submit():
    rating = request.form.get("rating", "").strip()
    body   = request.form.get("body", "").strip()
    if not rating or not body:
        flash("Completa la puntuación y el comentario.", "error")
        return redirect(url_for("main.index") + "#resenas")
    if not rating.isdigit() or not (1 <= int(rating) <= 5):
        flash("Puntuación no válida.", "error")
        return redirect(url_for("main.index") + "#resenas")
    if len(body) < 10:
        flash("El comentario es demasiado corto (mínimo 10 caracteres).", "error")
        return redirect(url_for("main.index") + "#resenas")
    if len(body) > 800:
        flash("El comentario es demasiado largo (máximo 800 caracteres).", "error")
        return redirect(url_for("main.index") + "#resenas")
    existing = db_fetchone(
        "SELECT id FROM reviews WHERE user_id=%s", (session["user_id"],)
    )
    if existing:
        flash("Ya has enviado una reseña. Solo se permite una por usuario.", "error")
        return redirect(url_for("main.index") + "#resenas")
    bad, word = contains_profanity(body)
    if bad:
        current_app.logger.info("Review blocked by wordlist: user=%s word=%r", session["user_id"], word)
        flash("Tu reseña contiene lenguaje ofensivo. Por favor, mantén un tono respetuoso.", "error")
        return redirect(url_for("main.index") + "#resenas")

    clean, reason, api_ok = review_is_clean(body)
    if not api_ok:
        current_app.logger.warning("Review moderation AI failed (fail-open): user=%s", session["user_id"])
    if not clean:
        current_app.logger.info("Review blocked by AI: user=%s reason=%s", session["user_id"], reason)
        flash(f"Tu reseña ha sido rechazada por mala conducta: {reason}. Por favor, mantén un tono respetuoso.", "error")
        return redirect(url_for("main.index") + "#resenas")
    db_execute(
        "INSERT INTO reviews (user_id, rating, body, created_at) VALUES (?,?,?,?)",
        (session["user_id"], int(rating), body, _now())
    )
    db_commit()
    flash("Reseña enviada. Estará visible tras ser aprobada por un administrador.", "success")
    return redirect(url_for("main.index") + "#resenas")


@bp.route("/admin/reviews")
@admin_required
def admin_reviews():
    pending = db_fetchall(
        """SELECT r.*, u.username FROM reviews r
           JOIN users u ON r.user_id=u.id
           WHERE r.approved=0 ORDER BY r.created_at DESC"""
    )
    approved = db_fetchall(
        """SELECT r.*, u.username FROM reviews r
           JOIN users u ON r.user_id=u.id
           WHERE r.approved=1 ORDER BY r.created_at DESC"""
    )
    return render_template("admin_reviews.html",
                           pending=pending, approved=approved)


@bp.route("/admin/reviews/<int:rid>/approve", methods=["POST"])
@admin_required
def review_approve(rid):
    db_execute("UPDATE reviews SET approved=1 WHERE id=%s", (rid,))
    db_commit()
    return redirect(url_for("reviews.admin_reviews"))


@bp.route("/admin/reviews/<int:rid>/delete", methods=["POST"])
@admin_required
def review_delete(rid):
    db_execute("DELETE FROM reviews WHERE id=%s", (rid,))
    db_commit()
    return redirect(url_for("reviews.admin_reviews"))
