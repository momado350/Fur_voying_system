import os
import sys
from datetime import datetime

from flask import Flask, jsonify

from config import Config
from extensions import db, login_manager, migrate
from models import Office, Role, User
from utils.phone import normalize_phone
from utils.storage import file_url


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if app.config["STORAGE_BACKEND"] == "local":
        os.makedirs(app.config["RESUME_FOLDER"], exist_ok=True)
        os.makedirs(app.config["PHOTO_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_helpers():
        return {
            "now": datetime.utcnow,
            "file_url": file_url,
        }

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True}), 200

    from blueprints.admin import bp as admin_bp
    from blueprints.auth import bp as auth_bp
    from blueprints.candidate import bp as candidate_bp
    from blueprints.election import bp as election_bp
    from blueprints.objections import bp as objections_bp
    from blueprints.public import bp as public_bp
    from blueprints.voter import bp as voter_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(voter_bp)
    app.register_blueprint(candidate_bp)
    app.register_blueprint(objections_bp)
    app.register_blueprint(election_bp)

    return app


app = create_app()


def seed():
    from models import ApprovalStatus

    with app.app_context():
        db.create_all()

        def upsert_user(phone, full_name, role, pw):
            phone_n = normalize_phone(phone)
            u = User.query.filter_by(phone=phone_n).first()
            if not u:
                u = User(email=None, phone=phone_n, full_name=full_name, role=role)
                u.set_password(pw)
                u.voter_status = ApprovalStatus.APPROVED.value
                u.candidate_status = ApprovalStatus.APPROVED.value
                u.is_roster_member = True
                db.session.add(u)
                db.session.commit()
            return u

        upsert_user("+10000000001", "Election Admin", Role.ADMIN.value, "Admin@12345")
        upsert_user("+10000000002", "Election Committee", Role.COMMITTEE.value, "Committee@12345")

        defaults = [
            ("President", 10),
            ("Vice President", 20),
            ("Secretary", 30),
            ("Treasurer", 40),
        ]
        for name, order in defaults:
            if not Office.query.filter_by(name=name).first():
                db.session.add(Office(name=name, sort_order=order))
        db.session.commit()

        print("Seed complete:")
        print("  Admin phone: +10000000001  / Admin@12345")
        print("  Committee phone: +10000000002  / Committee@12345")


if __name__ == "__main__":
    if "--seed" in sys.argv:
        seed()
        raise SystemExit(0)

    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
