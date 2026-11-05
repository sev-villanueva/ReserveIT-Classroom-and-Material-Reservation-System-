"""ReserveIT - Classroom and Material Reservation System (Flask + PostgreSQL)."""
import os
import secrets

from dotenv import load_dotenv
from flask import Flask, abort, render_template, request, session


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    app.config["PENALTY_THRESHOLD"] = float(os.getenv("PENALTY_THRESHOLD", "500"))

    from . import admin, auth, db, main, reservations

    db.init_app(app)
    for module in (auth, main, reservations, admin):
        app.register_blueprint(module.bp)

    @app.before_request
    def check_csrf():
        """Every POST form must carry the token we put in the session."""
        if request.method == "POST":
            sent = request.form.get("_csrf", "").encode()
            expected = session.get("_csrf", "").encode()
            if not sent or not secrets.compare_digest(sent, expected):
                abort(400, "This form has expired. Go back, refresh the page, and try again.")

    @app.context_processor
    def template_globals():
        def csrf_token():
            if "_csrf" not in session:
                session["_csrf"] = secrets.token_hex(16)
            return session["_csrf"]

        return {"csrf_token": csrf_token, "account": session.get("account")}

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def show_error(err):
        return render_template("error.html", err=err), err.code

    return app
