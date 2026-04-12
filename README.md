# Union Election App (Flask + Postgres)

A production-minded starter app for union-style elections with:
- Voter registration + approval gate
- Candidate roster + candidate application + approval gate
- Office-by-office poll sessions with timed voting windows
- Tie handling (automatic runoff session among tied top candidates)
- Objections workflow reviewed by Election Committee
- Admin / Committee dashboard (full rights)

## Quick start (local)

### 1) Create a virtualenv and install deps
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

# or:
conda activate voting

pip install -r requirements.txt
```

### 2) Set environment variables
Create a `.env` file (or export vars in your shell):
```bash
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/election_app
SECRET_KEY=dev-secret-change-me
```

### 3) Create DB + run migrations
This app uses **Flask-Migrate** (Alembic) so schema changes are trackable.

```bash
# create the database in Postgres first (psql / pgAdmin):
# CREATE DATABASE election_app;

flask --app app.py db init
flask --app app.py db migrate -m "initial"
flask --app app.py db upgrade
```


after any change do:

```
flask --app app.py db migrate -m "add notes column"
flask --app app.py db upgrade
```

### 4) Seed initial admin + offices
```bash
python app.py --seed
```

### 5) Run
```bash
python app.py
```
Open: http://127.0.0.1:5000

## Default admin
When you run `python app.py --seed`, it creates:

- **Admin**: admin@example.com / Admin@12345
- **Committee**: committee@example.com / Committee@12345

Change these immediately in production.

## Uploads
Uploads are stored locally:
- `static/uploads/resumes/`
- `static/uploads/photos/`

In production, switch to S3:
- See commented S3 helper in `utils/storage.py` (uncomment + configure).

## Election Flow (recommended)
1. Admin creates Offices.
2. Candidates apply (upload resume/photo) -> Committee/Admin approves.
3. Voters register -> Committee/Admin approves.
4. Committee opens poll for an Office (5 minutes by default).
5. Approved voters vote once per session.
6. At close:
   - If a clear winner -> office is marked complete.
   - If tie for top -> system creates a runoff session (2 minutes) with tied candidates only.
7. Repeat for next office.

## Notes / Recommended extra requirements
- Identity verification (SMS OTP for voter login)
- Audit log (append-only)
- IP / device rate limiting
- Enforce one active session at a time (per office / globally)
- Freeze candidate list at session start
- Export results (CSV/PDF) with signatures
