import secrets
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from ..db import db_fetchone, db_execute, db_commit
from ..utils import _now, _hash_pwd, _check_pwd, _is_legacy_hash
from ..email_utils import send_reset_email


bp = Blueprint("auth", __name__)


def _is_safe_url(target):
    ref  = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ("http", "https") and ref.netloc == test.netloc


@bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.index"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm", "")
        if not username or not email or not password:
            error = "Todos los campos son obligatorios."
        elif len(password) < 8:
            error = "La contraseña debe tener al menos 8 caracteres."
        elif password != confirm:
            error = "Las contraseñas no coinciden."
        else:
            dup = db_fetchone("SELECT id FROM users WHERE username=%s OR email=%s",
                              (username, email))
            if dup:
                error = "El nombre de usuario o email ya está registrado."
            else:
                db_execute(
                    "INSERT INTO users (username,email,password,salt,created_at) VALUES (?,?,?,?,?)",
                    (username, email, _hash_pwd(password), "", _now())
                )
                db_commit()
                flash("Cuenta creada. Ya puedes iniciar sesión.", "success")
                return redirect(url_for("auth.login"))
    return render_template("register.html", error=error)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.index"))
    error = None
    if request.method == "POST":
        ident    = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        user = db_fetchone(
            "SELECT * FROM users WHERE (username=%s OR email=%s) AND is_active=1",
            (ident, ident.lower())
        )
        if not user or not _check_pwd(password, user["password"], user["salt"]):
            error = "Credenciales incorrectas."
        else:
            if _is_legacy_hash(user["password"]):
                # Migrate SHA256 → bcrypt transparently on first login
                db_execute("UPDATE users SET password=%s, salt=%s WHERE id=%s",
                           (_hash_pwd(password), "", user["id"]))
                db_commit()
            session.permanent = True
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = bool(user["is_admin"])
            db_execute("UPDATE users SET last_login=%s WHERE id=%s", (_now(), user["id"]))
            db_commit()
            next_url = request.args.get("next")
            return redirect(next_url if next_url and _is_safe_url(next_url) else url_for("main.index"))
    return render_template("login.html", error=error)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))


@bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    sent = False
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user  = db_fetchone("SELECT * FROM users WHERE email=%s", (email,))
        if user:
            token = secrets.token_urlsafe(32)
            exp   = (datetime.utcnow() + timedelta(hours=1)).isoformat()
            db_execute("INSERT INTO reset_tokens (user_id,token,expires_at) VALUES (?,?,?)",
                       (user["id"], token, exp))
            db_commit()
            send_reset_email(email, token)
        sent = True
    return render_template("forgot.html", sent=sent)


@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    row = db_fetchone(
        "SELECT * FROM reset_tokens WHERE token=%s AND used=0", (token,)
    )
    invalid = not row or row["expires_at"] < _now()
    error   = None
    if not invalid and request.method == "POST":
        pwd  = request.form.get("password", "")
        conf = request.form.get("confirm", "")
        if len(pwd) < 8:
            error = "La contraseña debe tener al menos 8 caracteres."
        elif pwd != conf:
            error = "Las contraseñas no coinciden."
        else:
            db_execute("UPDATE users SET password=%s, salt=%s WHERE id=%s",
                       (_hash_pwd(pwd), "", row["user_id"]))
            db_execute("UPDATE reset_tokens SET used=1 WHERE token=%s", (token,))
            db_commit()
            flash("Contraseña actualizada.", "success")
            return redirect(url_for("auth.login"))
    return render_template("reset.html", invalid=invalid, token=token, error=error)
