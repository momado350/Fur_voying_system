from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Role, ApprovalStatus, PollSession, SessionStatus, SessionCandidate, Ballot, User
from forms import CastVoteForm
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Role, ApprovalStatus, Office, Nomination
from extensions import db


bp = Blueprint("voter", __name__, url_prefix="/voter")

def voter_required():
    return current_user.is_authenticated and current_user.role == Role.VOTER.value

@bp.get("/dashboard")
@login_required
def dashboard():
    if not voter_required():
        flash("Voter access only.", "danger")
        return redirect(url_for("public.index"))

    session = (PollSession.query
               .filter(PollSession.status == SessionStatus.RUNNING.value)
               .order_by(PollSession.start_time.desc())
               .first())

    offices = Office.query.order_by(Office.sort_order.asc(), Office.name.asc()).all()

    noms = (Nomination.query
            .filter_by(status=ApprovalStatus.APPROVED.value)
            .order_by(Nomination.created_at.desc())
            .all())

    by_office = {}
    for n in noms:
        by_office.setdefault(n.office_id, []).append(n)

    return render_template(
        "voter/dashboard.html",
        session=session,
        offices=offices,
        by_office=by_office
    )

@bp.get("/session/<int:session_id>")
@login_required
def session_view(session_id: int):
    if not voter_required():
        flash("Voter access only.", "danger")
        return redirect(url_for("public.index"))

    if current_user.voter_status != ApprovalStatus.APPROVED.value:
        flash("Your voter registration is pending approval.", "warning")
        return redirect(url_for("voter.dashboard"))

    session = PollSession.query.get_or_404(session_id)
    if session.status != SessionStatus.RUNNING.value:
        flash("That session is not currently open.", "info")
        return redirect(url_for("voter.dashboard"))

    now = datetime.utcnow()
    if session.end_time and now >= session.end_time:
        flash("Voting has ended for this session.", "info")
        return redirect(url_for("election.session_results", session_id=session.id))

    # prevent revote
    existing = Ballot.query.filter_by(session_id=session.id, voter_id=current_user.id).first()
    if existing:
        flash("You already voted in this session.", "info")
        return redirect(url_for("election.session_results", session_id=session.id))

    candidates = (SessionCandidate.query
                  .filter_by(session_id=session.id)
                  .all())
    candidate_users = [sc.candidate for sc in candidates]

    form = CastVoteForm()
    form.candidate_id.choices = [(c.id, c.full_name) for c in candidate_users]

    return render_template("voter/session.html", session=session, candidates=candidate_users, form=form)

@bp.post("/session/<int:session_id>/vote")
@login_required
def cast_vote(session_id: int):
    if not voter_required():
        flash("Voter access only.", "danger")
        return redirect(url_for("public.index"))

    if current_user.voter_status != ApprovalStatus.APPROVED.value:
        flash("Your voter registration is pending approval.", "warning")
        return redirect(url_for("voter.dashboard"))

    session = PollSession.query.get_or_404(session_id)
    if session.status != SessionStatus.RUNNING.value:
        flash("That session is not currently open.", "info")
        return redirect(url_for("voter.dashboard"))

    existing = Ballot.query.filter_by(session_id=session.id, voter_id=current_user.id).first()
    if existing:
        flash("You already voted in this session.", "info")
        return redirect(url_for("election.session_results", session_id=session.id))

    candidates = (SessionCandidate.query
                  .filter_by(session_id=session.id)
                  .all())
    allowed_ids = {sc.candidate_id for sc in candidates}

    form = CastVoteForm()
    form.candidate_id.choices = [(sc.candidate_id, sc.candidate.full_name) for sc in candidates]

    if not form.validate_on_submit():
        flash("Please choose a candidate.", "warning")
        return redirect(url_for("voter.session_view", session_id=session.id))

    cid = form.candidate_id.data
    if cid not in allowed_ids:
        abort(400)

    b = Ballot(session_id=session.id, voter_id=current_user.id, candidate_id=cid)
    db.session.add(b)
    db.session.commit()

    flash("Your vote has been recorded.", "success")
    return redirect(url_for("election.session_results", session_id=session.id))


@bp.get("/slate")
@login_required
def slate():
    # voters only
    if current_user.role != Role.VOTER.value:
        flash("Voter access only.", "danger")
        return redirect(url_for("public.index"))

    # must be approved to participate
    if current_user.voter_status != ApprovalStatus.APPROVED.value:
        flash("Your voter registration is pending approval.", "warning")
        return redirect(url_for("voter.dashboard"))

    offices = Office.query.order_by(Office.sort_order.asc(), Office.name.asc()).all()

    # Only show APPROVED nominations (these are the ones that would appear on ballots)
    noms = (Nomination.query
            .filter_by(status=ApprovalStatus.APPROVED.value)
            .order_by(Nomination.created_at.desc())
            .all())

    # group nominations by office
    by_office = {}
    for n in noms:
        by_office.setdefault(n.office_id, []).append(n)

    return render_template("voter/slate.html", offices=offices, by_office=by_office)