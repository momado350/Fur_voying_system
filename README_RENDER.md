# Render deployment notes

This version is prepared for:
- Render PostgreSQL managed database
- Render Python web service
- S3-backed candidate photos and resumes

## What changed
- Added `render.yaml` to provision both the web app and Postgres database.
- Added Gunicorn for production startup.
- Added `/healthz` for Render health checks.
- Normalized `DATABASE_URL` handling for Render connection strings.
- Replaced local upload-only logic with a storage layer that supports:
  - `local` for development
  - `s3` for production
- Added `s3_utils.py` using your preferred upload pattern.
- Candidate photos and resumes now save directly to S3 and store the returned HTTPS URL in the database.

## Required S3 environment variables
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_REGION`
- `AWS_S3_BUCKET_NAME`
- `S3_RESUME_PREFIX` (optional, default: `resumes`)
- `S3_PHOTO_PREFIX` (optional, default: `photos`)

## Deploy on Render
1. Push this folder to GitHub.
2. In Render, create a new Blueprint from the repository.
3. Render will read `render.yaml` and create:
   - `fur-online-voting-web`
   - `fur-online-voting-db`
4. In the web service environment, set your S3 credentials and bucket values.
5. After the first deploy, open a Render Shell or run a one-off command:
   - `flask db upgrade`
   - `python app.py --seed`

## Local development
You can still run locally with filesystem uploads:

```bash
cp .env.example .env
# set STORAGE_BACKEND=local
pip install -r requirements.txt
flask db upgrade
python app.py
```

## S3 behavior
- Photos and resumes are uploaded to S3 using direct HTTPS object URLs.
- The app stores the returned S3 URL in the database.
- Files are organized by prefix, such as `photos/...` and `resumes/...`.
