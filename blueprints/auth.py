from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from forms import LoginForm
from utils.phone import normalize_phone
# /apply/candidate
bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))
    form = LoginForm()
    return render_template("auth/login.html", form=form)

@bp.post("/login")
def login_post():
    form = LoginForm()
    if not form.validate_on_submit():
        return render_template("auth/login.html", form=form), 400

    phone = normalize_phone(form.phone.data)
    user = User.query.filter_by(phone=phone).first()

    if not user or not user.check_password(form.password.data):
        flash("Invalid phone or password.", "danger")
        return render_template("auth/login.html", form=form), 401

    #
    login_user(user)
    flash("Welcome back!", "success")

    next_url = request.args.get("next")
    if next_url:
        return redirect(next_url)

    if user.role == "voter":
        return redirect(url_for("voter.dashboard"))
    elif user.role == "candidate":
        return redirect(url_for("candidate.dashboard"))
    elif user.role in ["admin", "committee"]:
        return redirect(url_for("admin.dashboard"))

    return redirect(url_for("public.index"))

@bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("public.index"))