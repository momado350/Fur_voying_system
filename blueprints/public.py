from flask import Blueprint, render_template, redirect, url_for, flash
from flask import current_app
from extensions import db
from models import User, Role, ApprovalStatus, Office, PollSession, SessionStatus, OfficeResult
from forms import VoterRegisterForm, CandidateApplyForm
from utils.storage import save_upload, ext_ok, ALLOWED_IMAGE, ALLOWED_RESUME
from utils.phone import normalize_phone
from flask_login import login_user

bp = Blueprint("public", __name__)

@bp.get("/")
def index():
    offices = Office.query.order_by(Office.sort_order.asc(), Office.name.asc()).all()
    results = {r.office_id: r for r in OfficeResult.query.all()}
    active_session = (PollSession.query
                      .filter(PollSession.status == SessionStatus.RUNNING.value)
                      .order_by(PollSession.start_time.desc())
                      .first())
    return render_template("public/index.html", offices=offices, results=results, active_session=active_session)

@bp.get("/register/voter")
def register_voter():
    form = VoterRegisterForm()
    return render_template("public/register_voter.html", form=form)

@bp.post("/register/voter")
def register_voter_post():
    form = VoterRegisterForm()
    if not form.validate_on_submit():
        return render_template("public/register_voter.html", form=form), 400

    phone = normalize_phone(form.phone.data)
    if User.query.filter_by(phone=phone).first():
        flash("That phone number is already registered.", "warning")
        return render_template("public/register_voter.html", form=form), 409

    u = User(
        email=None,
        full_name=form.full_name.data.strip(),
        role=Role.VOTER.value,
        phone=phone,
        state=form.state.data.strip(),
        city=form.city.data.strip(),
        voter_status=ApprovalStatus.PENDING.value,
        candidate_status=ApprovalStatus.PENDING.value,
    )
    u.set_password(form.password.data)
    db.session.add(u)
    db.session.commit()

    flash("Registered! Your voter account is pending approval by the Election Committee.", "success")
    return redirect(url_for("auth.login"))

@bp.get("/apply/candidate")
def apply_candidate():
    form = CandidateApplyForm()
    return render_template("public/apply_candidate.html", form=form)

@bp.post("/apply/candidate")
def apply_candidate_post():
    form = CandidateApplyForm()
    if not form.validate_on_submit():
        return render_template("public/apply_candidate.html", form=form), 400

    phone = normalize_phone(form.phone.data)
    if User.query.filter_by(phone=phone).first():
        flash("That phone number is already registered.", "warning")
        return render_template("public/apply_candidate.html", form=form), 409

    resume_path = None
    photo_path = None

    # Local upload now (S3 later)
    if form.resume.data and getattr(form.resume.data, "filename", ""):
        if not ext_ok(form.resume.data.filename, ALLOWED_RESUME):
            flash("Resume must be PDF, DOC, or DOCX.", "danger")
            return render_template("public/apply_candidate.html", form=form), 400
        resume_path = save_upload(form.resume.data, "resume")

    if form.photo.data and getattr(form.photo.data, "filename", ""):
        if not ext_ok(form.photo.data.filename, ALLOWED_IMAGE):
            flash("Photo must be PNG, JPG, JPEG, or WebP.", "danger")
            return render_template("public/apply_candidate.html", form=form), 400
        photo_path = save_upload(form.photo.data, "photo")

    u = User(
        email=None,
        full_name=form.full_name.data.strip(),
        role=Role.CANDIDATE.value,
        phone=phone,
        state=form.state.data.strip(),
        city=form.city.data.strip(),
        resume_path=resume_path,
        photo_path=photo_path,
        candidate_status=ApprovalStatus.PENDING.value,
        voter_status=ApprovalStatus.PENDING.value,
        is_roster_member=False,  # committee/admin must confirm roster membership
    )
    u.set_password(form.password.data)
    db.session.add(u)
    db.session.commit()
# /apply/candidate
    flash("Registered! Your candidate account is pending approval by the Election Committee. Visit your profile at the top right 'Candidate' button", "success")
    login_user(u)
    return redirect(url_for("voter.dashboard"))



    