from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Role, ApprovalStatus, Office, Nomination, Objection, ObjectionStatus
from forms import NominateForm
# /apply/candidate
bp = Blueprint("candidate", __name__, url_prefix="/candidate")

def candidate_required():
    if not current_user.is_authenticated or current_user.role != Role.CANDIDATE.value:
        return False
    return True

@bp.get("/dashboard")
@login_required
def dashboard():
    if not candidate_required():
        flash("Candidate access only.", "danger")
        return redirect(url_for("public.index"))

    offices = Office.query.order_by(Office.sort_order.asc(), Office.name.asc()).all()
    nominations = (Nomination.query
                   .filter_by(candidate_id=current_user.id)
                   .order_by(Nomination.created_at.desc())
                   .all())

    form = NominateForm()
    form.office_id.choices = [(o.id, o.name) for o in offices]

    return render_template("candidate/dashboard.html", form=form, nominations=nominations)

@bp.post("/nominate")
@login_required
def nominate():
    if not candidate_required():
        flash("Candidate access only.", "danger")
        return redirect(url_for("public.index"))

    if current_user.candidate_status != ApprovalStatus.APPROVED.value or not current_user.is_roster_member:
        flash("You must be roster-verified and approved before nominating for office.", "warning")
        return redirect(url_for("candidate.dashboard"))

    offices = Office.query.order_by(Office.sort_order.asc(), Office.name.asc()).all()
    form = NominateForm()
    form.office_id.choices = [(o.id, o.name) for o in offices]

    if not form.validate_on_submit():
        return render_template("candidate/dashboard.html",
                               form=form,
                               nominations=Nomination.query.filter_by(candidate_id=current_user.id).all()), 400

    office_id = form.office_id.data

    existing = Nomination.query.filter_by(candidate_id=current_user.id, office_id=office_id).first()
    if existing:
        flash("You already have a nomination for this office.", "info")
        return redirect(url_for("candidate.dashboard"))

    nom = Nomination(
        candidate_id=current_user.id,
        office_id=office_id,
        status=ApprovalStatus.PENDING.value,
        nominated_by_name=form.nominated_by_name.data.strip() if form.nominated_by_name.data else None,
        nominated_by_phone=form.nominated_by_phone.data.strip() if form.nominated_by_phone.data else None,
        statement=form.statement.data.strip() if form.statement.data else None,
    )
    db.session.add(nom)
    db.session.commit()

    flash("Nomination submitted. Committee will review and handle any objections.", "success")
    return redirect(url_for("candidate.dashboard"))
