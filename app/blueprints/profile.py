import secrets
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from ..db import db_fetchone, db_fetchall, db_execute, db_commit
from ..decorators import login_required
from ..utils import _hash_pwd


bp = Blueprint("profile", __name__)


@bp.route("/profile")
@login_required
def profile():
    user    = db_fetchone("SELECT * FROM users WHERE id=%s", (session["user_id"],))
    reviews = db_fetchall(
        "SELECT * FROM reviews WHERE user_id=%s ORDER BY created_at DESC",
        (session["user_id"],)
    )
    dl_row  = db_fetchone(
        "SELECT COUNT(*) as cnt FROM download_log WHERE user_id=%s",
        (session["user_id"],)
    )
    dl_count = dl_row["cnt"] if dl_row else 0
    return render_template("profile.html", user=user, reviews=reviews, dl_count=dl_count)


@bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    user  = db_fetchone("SELECT * FROM users WHERE id=%s", (session["user_id"],))
    error = None
    if request.method == "POST":
        action = request.form.get("action")

        if action == "email":
            new_email = request.form.get("email", "").strip().lower()
            if not new_email:
                error = "El email no puede estar vacío."
            else:
                dup = db_fetchone(
                    "SELECT id FROM users WHERE email=%s AND id!=%s",
                    (new_email, session["user_id"])
                )
                if dup:
                    error = "Ese email ya está en uso."
                else:
                    db_execute("UPDATE users SET email=%s WHERE id=%s",
                               (new_email, session["user_id"]))
                    db_commit()
                    flash("Email actualizado correctamente.", "success")
                    return redirect(url_for("profile.profile"))

        elif action == "password":
            current  = request.form.get("current", "")
            new_pwd  = request.form.get("password", "")
            confirm  = request.form.get("confirm", "")
            if _hash_pwd(current, user["salt"]) != user["password"]:
                error = "La contraseña actual no es correcta."
            elif len(new_pwd) < 8:
                error = "La nueva contraseña debe tener al menos 8 caracteres."
            elif new_pwd != confirm:
                error = "Las contraseñas no coinciden."
            else:
                salt = secrets.token_hex(16)
                db_execute("UPDATE users SET password=%s,salt=%s WHERE id=%s",
                           (_hash_pwd(new_pwd, salt), salt, session["user_id"]))
                db_commit()
                flash("Contraseña actualizada correctamente.", "success")
                return redirect(url_for("profile.profile"))

        elif action == "avatar":
            avatar_url = request.form.get("avatar_url", "").strip()
            db_execute("UPDATE users SET avatar_url=%s WHERE id=%s",
                       (avatar_url or None, session["user_id"]))
            db_commit()
            flash("Avatar actualizado.", "success")
            return redirect(url_for("profile.profile"))

        user = db_fetchone("SELECT * FROM users WHERE id=%s", (session["user_id"],))

    return render_template("profile_edit.html", user=user, error=error)
