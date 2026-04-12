from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db
from models import (Role, ApprovalStatus, Office, Nomination, Objection, ObjectionStatus,
                    PollSession, SessionStatus, SessionCandidate, Ballot, User, OfficeResult)
# /apply/candidate
bp = Blueprint("election", __name__, url_prefix="/election")

def staff_required():
    return current_user.is_authenticated and current_user.role in (Role.ADMIN.value, Role.COMMITTEE.value)

def tally(session_id: int):
    rows = (db.session.query(Ballot.candidate_id, func.count(Ballot.id))
            .filter(Ballot.session_id == session_id)
            .group_by(Ballot.candidate_id)
            .all())
    counts = {cid: int(n) for cid, n in rows}
    return counts

@bp.get("/session/<int:session_id>/results")
@login_required
def session_results(session_id: int):
    session = PollSession.query.get_or_404(session_id)
    candidates = (SessionCandidate.query
                  .filter_by(session_id=session.id)
                  .all())
    candidate_users = [sc.candidate for sc in candidates]
    counts = tally(session.id)

    # order by votes desc
    ranked = sorted(candidate_users, key=lambda u: (-counts.get(u.id, 0), u.full_name.lower()))

    return render_template("election/session_results.html",
                           session=session,
                           candidates=candidate_users,
                           counts=counts,
                           ranked=ranked)

def close_and_resolve(session: PollSession):
    """Close session, resolve winner or create runoff if tie."""
    session.status = SessionStatus.CLOSED.value
    session.end_time = session.end_time or datetime.utcnow()
    counts = tally(session.id)

    # Determine top candidates
    if not counts:
        # no votes: no winner, leave for committee to handle
        db.session.commit()
        return {"status": "no_votes"}

    max_votes = max(counts.values())
    top_ids = [cid for cid, n in counts.items() if n == max_votes]

    if len(top_ids) == 1:
        winner_id = top_ids[0]
        session.winner_candidate_id = winner_id

        # Mark office result (final)
        existing = OfficeResult.query.filter_by(office_id=session.office_id).first()
        if not existing:
            existing = OfficeResult(office_id=session.office_id)
            db.session.add(existing)
        existing.winner_candidate_id = winner_id
        existing.decided_at = datetime.utcnow()

        db.session.commit()
        return {"status": "winner", "winner_id": winner_id}

    # tie -> create runoff session (2 minutes default)
    runoff = PollSession(
        office_id=session.office_id,
        status=SessionStatus.SCHEDULED.value,
        round_number=session.round_number + 1,
        duration_seconds=120,
        is_runoff=True,
    )
    db.session.add(runoff)
    db.session.flush()

    # populate tied candidates only
    for cid in top_ids:
        db.session.add(SessionCandidate(session_id=runoff.id, candidate_id=cid))

    db.session.commit()
    return {"status": "tie", "runoff_id": runoff.id, "tied_ids": top_ids}

@bp.post("/session/<int:session_id>/close")
@login_required
def close_session(session_id: int):
    if not staff_required():
        flash("Committee/Admin access only.", "danger")
        return redirect(url_for("public.index"))

    session = PollSession.query.get_or_404(session_id)
    if session.status != SessionStatus.RUNNING.value:
        flash("That session is not currently running.", "info")
        return redirect(url_for("admin.dashboard"))

    result = close_and_resolve(session)
    if result["status"] == "winner":
        flash("Session closed. Winner resolved.", "success")
    elif result["status"] == "tie":
        flash("Session closed with a tie. Runoff session created.", "warning")
    else:
        flash("Session closed. No votes were cast.", "warning")

    return redirect(url_for("admin.dashboard"))

