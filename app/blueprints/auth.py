import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from ..db import db_fetchone, db_execute, db_commit
from ..utils import _now, _hash_pwd
from ..email_utils import send_reset_email


bp = Blueprint("auth", __name__)


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
                salt = secrets.token_hex(16)
                db_execute(
                    "INSERT INTO users (username,email,password,salt,created_at) VALUES (?,?,?,?,?)",
                    (username, email, _hash_pwd(password, salt), salt, _now())
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
        if not user or _hash_pwd(password, user["salt"]) != user["password"]:
            error = "Credenciales incorrectas."
        else:
            session.permanent = True
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = bool(user["is_admin"])
            db_execute("UPDATE users SET last_login=%s WHERE id=%s", (_now(), user["id"]))
            db_commit()
            return redirect(request.args.get("next", url_for("main.index")))
    return render_template("login.html", error=error)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))


@bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    sent = False
    dev_token = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user  = db_fetchone("SELECT * FROM users WHERE email=%s", (email,))
        if user:
            token = secrets.token_urlsafe(32)
            exp   = (datetime.utcnow() + timedelta(hours=1)).isoformat()
            db_execute("INSERT INTO reset_tokens (user_id,token,expires_at) VALUES (?,?,?)",
                       (user["id"], token, exp))
            db_commit()
            ok = send_reset_email(email, token)
            if not ok:
                dev_token = token
        sent = True
    return render_template("forgot.html", sent=sent, dev_token=dev_token)


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
            salt = secrets.token_hex(16)
            db_execute("UPDATE users SET password=%s,salt=%s WHERE id=%s",
                       (_hash_pwd(pwd, salt), salt, row["user_id"]))
            db_execute("UPDATE reset_tokens SET used=1 WHERE token=%s", (token,))
            db_commit()
            flash("Contraseña actualizada.", "success")
            return redirect(url_for("auth.login"))
    return render_template("reset.html", invalid=invalid, token=token, error=error)
