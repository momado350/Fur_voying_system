from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import (
    User, Role, ApprovalStatus, Office, OfficeResult, Nomination, Objection,
    ObjectionStatus, PollSession, SessionStatus, SessionCandidate
)
from forms import OfficeForm, StartSessionForm

bp = Blueprint("admin", __name__, url_prefix="/admin")


def staff_required() -> bool:
    return current_user.is_authenticated and current_user.role in (Role.ADMIN.value, Role.COMMITTEE.value)


# -------------------------
# DASHBOARD
# -------------------------
@bp.get("/")
@login_required
def dashboard():
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))

    pending_voters = User.query.filter_by(
        role=Role.VOTER.value,
        voter_status=ApprovalStatus.PENDING.value
    ).all()

    pending_candidates = User.query.filter_by(
        role=Role.CANDIDATE.value,
        candidate_status=ApprovalStatus.PENDING.value
    ).all()

    offices = Office.query.order_by(Office.sort_order.asc(), Office.name.asc()).all()

    nominations = (Nomination.query
                   .order_by(Nomination.created_at.desc())
                   .limit(50)
                   .all())

    objections = (Objection.query
                  .order_by(Objection.created_at.desc())
                  .limit(50)
                  .all())

    sessions = (PollSession.query
                .order_by(PollSession.created_at.desc())
                .limit(20)
                .all())

    form = StartSessionForm()
    form.office_id.choices = [(o.id, o.name) for o in offices]
    form.duration_seconds.data = 300

    office_form = OfficeForm()

    return render_template(
        "admin/dashboard.html",
        pending_voters=pending_voters,
        pending_candidates=pending_candidates,
        offices=offices,
        nominations=nominations,
        objections=objections,
        sessions=sessions,
        form=form,
        office_form=office_form,
    )


# -------------------------
# NOMINATIONS REVIEW (Queue)
# -------------------------
@bp.get("/nominations")
@login_required
def nominations_queue():
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))

    pending = (Nomination.query
               .filter_by(status=ApprovalStatus.PENDING.value)
               .order_by(Nomination.created_at.desc())
               .all())

    objection_counts = {}
    for n in pending:
        objection_counts[n.id] = Objection.query.filter_by(nomination_id=n.id).count()

    return render_template(
        "admin/nominations.html",
        pending=pending,
        objection_counts=objection_counts
    )


@bp.post("/nominations/<int:nomination_id>/approve")
@login_required
def approve_nomination(nomination_id: int):
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))

    nom = Nomination.query.get_or_404(nomination_id)

    upheld_exists = (Objection.query
                     .filter_by(nomination_id=nom.id, status=ObjectionStatus.UPHELD.value)
                     .first())
    if upheld_exists:
        flash("Cannot approve: an objection was upheld for this nomination.", "warning")
        return redirect(url_for("admin.nominations_queue"))

    nom.status = ApprovalStatus.APPROVED.value
    db.session.commit()
    flash("Nomination approved.", "success")
    return redirect(url_for("admin.nominations_queue"))


@bp.post("/nominations/<int:nomination_id>/reject")
@login_required
def reject_nomination(nomination_id: int):
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))

    nom = Nomination.query.get_or_404(nomination_id)
    nom.status = ApprovalStatus.REJECTED.value
    db.session.commit()
    flash("Nomination rejected.", "warning")
    return redirect(url_for("admin.nominations_queue"))


# -------------------------
# VOTERS APPROVAL
# -------------------------
@bp.post("/voters/<int:user_id>/approve")
@login_required
def approve_voter(user_id: int):
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))
    u = User.query.get_or_404(user_id)
    u.voter_status = ApprovalStatus.APPROVED.value
    db.session.commit()
    flash("Voter approved.", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/voters/<int:user_id>/reject")
@login_required
def reject_voter(user_id: int):
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))
    u = User.query.get_or_404(user_id)
    u.voter_status = ApprovalStatus.REJECTED.value
    db.session.commit()
    flash("Voter rejected.", "warning")
    return redirect(url_for("admin.dashboard"))


# -------------------------
# CANDIDATES APPROVAL + ROSTER
# -------------------------
@bp.post("/candidates/<int:user_id>/approve")
@login_required
def approve_candidate(user_id: int):
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))
    u = User.query.get_or_404(user_id)
    u.candidate_status = ApprovalStatus.APPROVED.value
    db.session.commit()
    flash("Candidate approved.", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/candidates/<int:user_id>/reject")
@login_required
def reject_candidate(user_id: int):
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))
    u = User.query.get_or_404(user_id)
    u.candidate_status = ApprovalStatus.REJECTED.value
    db.session.commit()
    flash("Candidate rejected.", "warning")
    return redirect(url_for("admin.dashboard"))


@bp.post("/candidates/<int:user_id>/roster_yes")
@login_required
def roster_yes(user_id: int):
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))
    u = User.query.get_or_404(user_id)
    u.is_roster_member = True
    db.session.commit()
    flash("Marked as roster member.", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/candidates/<int:user_id>/roster_no")
@login_required
def roster_no(user_id: int):
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))
    u = User.query.get_or_404(user_id)
    u.is_roster_member = False
    db.session.commit()
    flash("Unmarked roster member.", "warning")
    return redirect(url_for("admin.dashboard"))


# -------------------------
# OFFICES
# -------------------------
@bp.post("/offices/create")
@login_required
def create_office():
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))

    form = OfficeForm()
    if not form.validate_on_submit():
        flash("Please provide a valid office name and sort order.", "warning")
        return redirect(url_for("admin.dashboard"))

    if Office.query.filter_by(name=form.name.data.strip()).first():
        flash("That office already exists.", "info")
        return redirect(url_for("admin.dashboard"))

    o = Office(name=form.name.data.strip(), sort_order=form.sort_order.data)
    db.session.add(o)
    db.session.commit()
    flash("Office created.", "success")
    return redirect(url_for("admin.dashboard"))


# -------------------------
# OBJECTIONS DECISIONS
# -------------------------
@bp.post("/objections/<int:obj_id>/uphold")
@login_required
def uphold_objection(obj_id: int):
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))

    obj = Objection.query.get_or_404(obj_id)
    obj.status = ObjectionStatus.UPHELD.value
    obj.decision_notes = (request.form.get("decision_notes") or "").strip() or None

    # If you have decided_at in your model, keep these lines.
    # If you DON'T, remove them.
    if hasattr(obj, "decided_at"):
        obj.decided_at = datetime.utcnow()

    # Block the nomination for that office
    obj.nomination.status = ApprovalStatus.REJECTED.value

    db.session.commit()
    flash("Objection upheld (nomination blocked for this office).", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/objections/<int:obj_id>/dismiss")
@login_required
def dismiss_objection(obj_id: int):
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))

    obj = Objection.query.get_or_404(obj_id)
    obj.status = ObjectionStatus.DISMISSED.value
    obj.decision_notes = (request.form.get("decision_notes") or "").strip() or None

    if hasattr(obj, "decided_at"):
        obj.decided_at = datetime.utcnow()

    db.session.commit()
    flash("Objection dismissed.", "warning")
    return redirect(url_for("admin.dashboard"))


# -------------------------
# START SESSION
# -------------------------
@bp.post("/sessions/start")
@login_required
def start_session():
    if not staff_required():
        flash("Admin/Committee access only.", "danger")
        return redirect(url_for("public.index"))

    form = StartSessionForm()
    offices = Office.query.order_by(Office.sort_order.asc(), Office.name.asc()).all()
    form.office_id.choices = [(o.id, o.name) for o in offices]

    if not form.validate_on_submit():
        flash("Please select an office and a valid duration.", "warning")
        return redirect(url_for("admin.dashboard"))

    office_id = form.office_id.data
    duration = int(form.duration_seconds.data)

    running = PollSession.query.filter_by(status=SessionStatus.RUNNING.value).first()
    if running:
        flash("A session is already running. Close it before starting another.", "warning")
        return redirect(url_for("admin.dashboard"))

    if OfficeResult.query.filter_by(office_id=office_id).first():
        flash("That office is already decided. Reset results (not implemented) if you want to rerun.", "info")
        return redirect(url_for("admin.dashboard"))

    # candidates = approved nomination for office + candidate approved + roster verified
    approved_noms = (Nomination.query
                     .filter_by(office_id=office_id, status=ApprovalStatus.APPROVED.value)
                     .all())

    candidates = []
    for nom in approved_noms:
        c = nom.candidate
        if (
            c.role == Role.CANDIDATE.value
            and c.candidate_status == ApprovalStatus.APPROVED.value
            and c.is_roster_member
        ):
            candidates.append(c)

    if len(candidates) < 2:
        flash("Need at least 2 approved, roster-verified candidates for this office.", "warning")
        return redirect(url_for("admin.dashboard"))

    session = PollSession(
        office_id=office_id,
        status=SessionStatus.RUNNING.value,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(seconds=duration),
        duration_seconds=duration,
        is_runoff=False,
        round_number=1,
    )
    db.session.add(session)
    db.session.flush()

    for c in candidates:
        db.session.add(SessionCandidate(session_id=session.id, candidate_id=c.id))

    db.session.commit()
    flash("Poll session opened.", "success")
    return redirect(url_for("public.index"))