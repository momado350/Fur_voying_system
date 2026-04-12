from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FileField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, EqualTo, NumberRange

class LoginForm(FlaskForm):
    phone = StringField("Phone", validators=[DataRequired(), Length(max=40)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")

class VoterRegisterForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=200)])
    phone = StringField("Phone (this is your username)", validators=[DataRequired(), Length(max=40)])
    state = StringField("State", validators=[DataRequired(), Length(max=80)])
    city = StringField("City", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register as voter")

class CandidateApplyForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=200)])
    phone = StringField("Phone (this is your username)", validators=[DataRequired(), Length(max=40)])
    state = StringField("State", validators=[DataRequired(), Length(max=80)])
    city = StringField("City", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    resume = FileField("Resume (PDF/DOC/DOCX)", validators=[Optional()])
    photo = FileField("Profile photo (PNG/JPG/WebP)", validators=[Optional()])
    submit = SubmitField("Apply as candidate")

class NominateForm(FlaskForm):
    office_id = SelectField("Office", coerce=int, validators=[DataRequired()])
    statement = TextAreaField("Nomination statement (optional)", validators=[Optional(), Length(max=4000)])
    nominated_by_name = StringField("Nominated by (name)", validators=[Optional(), Length(max=200)])
    nominated_by_phone = StringField("Nominated by (phone)", validators=[Optional(), Length(max=40)])
    submit = SubmitField("Submit nomination")

class ObjectionForm(FlaskForm):
    nomination_id = IntegerField("Nomination ID", validators=[DataRequired()])
    filed_by_name = StringField("Your name", validators=[DataRequired(), Length(max=200)])
    filed_by_phone = StringField("Your phone", validators=[DataRequired(), Length(max=40)])
    reason = TextAreaField("Reason for objection", validators=[DataRequired(), Length(max=6000)])
    evidence = TextAreaField("Evidence / references (optional)", validators=[Optional(), Length(max=6000)])
    submit = SubmitField("File objection")

class OfficeForm(FlaskForm):
    name = StringField("Office name", validators=[DataRequired(), Length(max=120)])
    sort_order = IntegerField("Sort order", validators=[DataRequired(), NumberRange(min=0, max=9999)])
    submit = SubmitField("Save office")

class StartSessionForm(FlaskForm):
    office_id = SelectField("Office", coerce=int, validators=[DataRequired()])
    duration_seconds = IntegerField("Duration (seconds)", validators=[DataRequired(), NumberRange(min=30, max=3600)])
    submit = SubmitField("Open poll session")

class CastVoteForm(FlaskForm):
    candidate_id = SelectField("Choose candidate", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Cast vote")