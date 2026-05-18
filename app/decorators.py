from functools import wraps
from flask import session, request, redirect, url_for, abort

from .db import db_fetchone


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", next=request.path))
        if not session.get("is_admin"):
            abort(403)
        return f(*args, **kwargs)
    return decorated


def current_user():
    if "user_id" in session:
        return db_fetchone("SELECT * FROM users WHERE id=%s", (session["user_id"],))
    return None
