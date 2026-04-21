import os
import secrets
import logging
from datetime import timedelta
from flask import Flask

from .db import close_db


def create_app():
    flask_app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    flask_app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    flask_app.permanent_session_lifetime = timedelta(days=7)
    logging.basicConfig(level=logging.INFO)

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
