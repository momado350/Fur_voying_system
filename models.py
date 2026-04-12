from datetime import datetime
from enum import Enum

from flask_login import UserMixin

from extensions import db
from utils.security import hash_password, verify_password


# =========================
# ENUMS
# =========================
class Role(str, Enum):
    ADMIN = "admin"
    COMMITTEE = "committee"
    VOTER = "voter"
    CANDIDATE = "candidate"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ObjectionStatus(str, Enum):
    PENDING = "pending"
    UPHELD = "upheld"        # objection accepted => nomination blocked for that office
    DISMISSED = "dismissed"  # objection rejected


class SessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    CLOSED = "closed"


# =========================
# MODELS
# =========================
class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(200), nullable=False)

    # NOTE: Email is NOT used in your flows anymore.
    # Kept optional (nullable) for compatibility; safe in Postgres UNIQUE (multiple NULLs allowed).
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)

    # Phone is the username (required + unique)
    phone = db.Column(db.String(40), unique=True, nullable=False, index=True)

    role = db.Column(db.String(50), nullable=False, default=Role.VOTER.value)
    password_hash = db.Column(db.String(255), nullable=False)

    state = db.Column(db.String(80))
    city = db.Column(db.String(120))

    voter_status = db.Column(db.String(50), nullable=False, default=ApprovalStatus.PENDING.value)
    candidate_status = db.Column(db.String(50), nullable=False, default=ApprovalStatus.PENDING.value)

    # Candidate profile uploads (local filesystem now; later S3)
    resume_path = db.Column(db.String(500))
    photo_path = db.Column(db.String(500))

    # Candidate must be in roster to be eligible (committee/admin sets this)
    is_roster_member = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ---- auth helpers ----
    def set_password(self, pw: str):
        self.password_hash = hash_password(pw)

    def check_password(self, pw: str) -> bool:
        return verify_password(self.password_hash, pw)

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN.value

    @property
    def is_committee(self) -> bool:
        return self.role == Role.COMMITTEE.value

    @property
    def is_voter(self) -> bool:
        return self.role == Role.VOTER.value

    @property
    def is_candidate(self) -> bool:
        return self.role == Role.CANDIDATE.value


class Office(db.Model):
    __tablename__ = "office"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Nomination(db.Model):
    """
    Candidate nomination to a specific office.
    Committee may approve/reject; objections may uphold/dismiss nomination.
    """
    __tablename__ = "nomination"

    id = db.Column(db.Integer, primary_key=True)

    candidate_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    office_id = db.Column(db.Integer, db.ForeignKey("office.id"), nullable=False, index=True)

    # nomination review status
    status = db.Column(db.String(50), default=ApprovalStatus.PENDING.value, nullable=False)

    nominated_by_name = db.Column(db.String(200))
    nominated_by_phone = db.Column(db.String(40))
    statement = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    candidate = db.relationship("User", foreign_keys=[candidate_id])
    office = db.relationship("Office", foreign_keys=[office_id])

    __table_args__ = (
        db.UniqueConstraint("candidate_id", "office_id", name="uq_candidate_office"),
    )


class Objection(db.Model):
    __tablename__ = "objection"

    id = db.Column(db.Integer, primary_key=True)

    nomination_id = db.Column(db.Integer, db.ForeignKey("nomination.id"), nullable=False, index=True)

    # optional link to a registered voter/user who filed the objection
    filed_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)

    filed_by_name = db.Column(db.String(200))
    filed_by_phone = db.Column(db.String(40))

    reason = db.Column(db.Text, nullable=False)
    evidence = db.Column(db.Text)

    status = db.Column(db.String(50), default=ObjectionStatus.PENDING.value, nullable=False)
    decision_notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    nomination = db.relationship("Nomination", foreign_keys=[nomination_id])
    filed_by_user = db.relationship("User", foreign_keys=[filed_by_user_id])


class PollSession(db.Model):
    """
    A poll session is opened for ONE office at a time, for a fixed duration.
    Runoff sessions are new sessions with is_runoff=True and (optionally) restricted candidates
    by SessionCandidate rows.
    """
    __tablename__ = "poll_session"

    id = db.Column(db.Integer, primary_key=True)

    office_id = db.Column(db.Integer, db.ForeignKey("office.id"), nullable=False, index=True)

    status = db.Column(db.String(50), default=SessionStatus.SCHEDULED.value, nullable=False)

    round_number = db.Column(db.Integer, default=1, nullable=False)
    is_runoff = db.Column(db.Boolean, default=False, nullable=False)

    duration_seconds = db.Column(db.Integer, default=300, nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    office = db.relationship("Office", foreign_keys=[office_id])


class SessionCandidate(db.Model):
    """
    Which candidates appear on the ballot for a given session.
    For normal (non-runoff) sessions you can either populate all eligible candidates,
    or compute candidates dynamically. Your blueprint imports this, so keep it.
    """
    __tablename__ = "session_candidate"

    id = db.Column(db.Integer, primary_key=True)

    session_id = db.Column(db.Integer, db.ForeignKey("poll_session.id"), nullable=False, index=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    session = db.relationship("PollSession", foreign_keys=[session_id])
    candidate = db.relationship("User", foreign_keys=[candidate_id])

    __table_args__ = (
        db.UniqueConstraint("session_id", "candidate_id", name="uq_session_candidate"),
    )


class Ballot(db.Model):
    """
    A cast vote (one per voter per session).
    """
    __tablename__ = "ballot"

    id = db.Column(db.Integer, primary_key=True)

    session_id = db.Column(db.Integer, db.ForeignKey("poll_session.id"), nullable=False, index=True)
    voter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    cast_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    session = db.relationship("PollSession", foreign_keys=[session_id])
    voter = db.relationship("User", foreign_keys=[voter_id])
    candidate = db.relationship("User", foreign_keys=[candidate_id])

    __table_args__ = (
        db.UniqueConstraint("session_id", "voter_id", name="uq_ballot_one_per_voter_per_session"),
    )


class OfficeResult(db.Model):
    """
    Stores final winner per office once decided.
    """
    __tablename__ = "office_result"

    id = db.Column(db.Integer, primary_key=True)

    office_id = db.Column(db.Integer, db.ForeignKey("office.id"), nullable=False, unique=True, index=True)
    winner_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)

    decided_at = db.Column(db.DateTime)
    winning_round_number = db.Column(db.Integer)
    last_session_id = db.Column(db.Integer, db.ForeignKey("poll_session.id"), nullable=True, index=True)

    office = db.relationship("Office", foreign_keys=[office_id])
    winner = db.relationship("User", foreign_keys=[winner_user_id])
    last_session = db.relationship("PollSession", foreign_keys=[last_session_id])