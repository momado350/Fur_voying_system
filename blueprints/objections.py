from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Nomination, Objection, ObjectionStatus
from forms import ObjectionForm

bp = Blueprint("objections", __name__, url_prefix="/objections")

@bp.get("/file/<int:nomination_id>")
@login_required
def file(nomination_id: int):
    nom = Nomination.query.get_or_404(nomination_id)
    form = ObjectionForm()
    form.nomination_id.data = nom.id
    return render_template("objections/file.html", nomination=nom, form=form)

@bp.post("/file")
@login_required
def file_post():
    form = ObjectionForm()
    if not form.validate_on_submit():
        flash("Please fill all required fields.", "warning")
        return redirect(url_for("public.index"))

    nom = Nomination.query.get_or_404(form.nomination_id.data)
    obj = Objection(
        nomination_id=nom.id,
        filed_by_user_id=current_user.id if current_user.is_authenticated else None,
        filed_by_name=form.filed_by_name.data.strip(),
        filed_by_phone=form.filed_by_phone.data.strip(),
        reason=form.reason.data.strip(),
        evidence=form.evidence.data.strip() if form.evidence.data else None,
        status=ObjectionStatus.PENDING.value,
    )
    db.session.add(obj)
    db.session.commit()
    flash("Objection filed. Committee will review.", "success")
    return redirect(url_for("public.index"))


@bp.get("/queue")
@login_required
def queue():
    if current_user.role not in ["admin", "committee"]:
        flash("Committee access only.", "danger")
        return redirect(url_for("public.index"))

    pending = (Objection.query
               .filter_by(status=ObjectionStatus.PENDING.value)
               .order_by(Objection.created_at.desc())
               .all())
    return render_template("objections/queue.html", objections=pending)