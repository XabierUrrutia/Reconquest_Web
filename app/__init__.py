import os
import secrets
import logging
from datetime import timedelta
from flask import Flask

from .db import close_db
from .extensions import csrf, limiter


def create_app():
    flask_app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    logging.basicConfig(level=logging.INFO)

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        logging.warning(
            "SECRET_KEY no configurada como variable de entorno. "
            "Las sesiones se invalidarán en cada reinicio."
        )
        secret_key = secrets.token_hex(32)
    flask_app.secret_key = secret_key
    flask_app.permanent_session_lifetime = timedelta(days=7)

    csrf.init_app(flask_app)
    limiter.init_app(flask_app)

    flask_app.teardown_appcontext(close_db)

    from .blueprints.main import bp as main_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.reviews import bp as reviews_bp
    from .blueprints.profile import bp as profile_bp
    from .blueprints.bugs import bp as bugs_bp
    from .blueprints.chat import bp as chat_bp

    flask_app.register_blueprint(main_bp)
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(reviews_bp)
    flask_app.register_blueprint(profile_bp)
    flask_app.register_blueprint(bugs_bp)
    flask_app.register_blueprint(chat_bp)

    return flask_app


app = create_app()
