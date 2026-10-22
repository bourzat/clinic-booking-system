# Clinic Booking API: Setup and Run Guide

This guide walks you through the project from a fresh machine to a working API with every endpoint tested. Follow the parts in order the first time. After that, use [Part 11](#part-11-daily-cheat-sheet) as a cheat sheet.

The commands are written for **Ubuntu on WSL2**, which is the setup this project was checked on.

## Contents

0. [What you are building](#part-0-what-you-are-building)
1. [Tools to install](#part-1-tools-to-install)
2. [Get the code](#part-2-get-the-code)
3. [Create a virtual environment](#part-3-create-a-virtual-environment)
4. [Install the dependencies](#part-4-install-the-dependencies)
5. [Set up the database](#part-5-set-up-the-database)
6. [Configure and migrate](#part-6-configure-and-migrate)
7. [Run the API](#part-7-run-the-api)
8. [Test every endpoint by hand](#part-8-test-every-endpoint-by-hand)
9. [Run the automated tests](#part-9-run-the-automated-tests)
10. [Run everything with Docker](#part-10-run-everything-with-docker)
11. [Daily cheat sheet](#part-11-daily-cheat-sheet)
12. [Deploy to Vercel](#part-12-deploy-to-vercel)
13. [Troubleshooting](#part-13-troubleshooting)

---

## Part 0: What you are building

A REST API for a small clinic with 5 doctors. Patients can see free 30-minute slots, book one, reschedule it, and cancel it.

```
Your browser / curl ──HTTP──▶ FastAPI app (uvicorn, port 8000) ──SQL──▶ PostgreSQL (port 5432)
```

| Piece | What it is | Where it lives |
|---|---|---|
| **FastAPI** | The Python web framework that serves the endpoints | `clinic-booking/app/` |
| **Uvicorn** | The server that runs the FastAPI app | started from the command line |
| **PostgreSQL** | The database | your machine, or a Docker container |
| **Alembic** | Creates the tables and seeds the 5 doctors ("migrations") | `clinic-booking/migrations/` |
| **pytest** | Runs the 43 automated tests | `clinic-booking/tests/` |
| **Docker Compose** | Starts Postgres and the API together with one command | `clinic-booking/docker-compose.yml` |

There are two ways to run it:

- **Route A, local Python:** you run the API in a virtual environment and use a Postgres database. This is how you develop and run tests. It is covered in Parts 3 to 9.
- **Route B, Docker:** one command starts both the database and the API in containers. This is covered in Part 10.

Do Route A first. It teaches you how the pieces fit together.

---

## Part 1: Tools to install

Check what you already have:

```bash
git --version
uv --version            # Python package and environment manager
psql --version          # PostgreSQL client
docker --version        # only needed for Part 10
```

### 1.1 uv (manages Python versions and virtual environments)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
uv --version
```

> **Why uv?** The project runs on **Python 3.12**, as set in the `Dockerfile` and CI. Ubuntu may ship a newer Python, such as 3.14, and some of the pinned packages don't have builds for it yet. uv downloads Python 3.12 for you, so you don't need to install it system-wide.

### 1.2 PostgreSQL (if you are not using Docker for the database)

```bash
sudo apt update
sudo apt install -y postgresql postgresql-client
sudo systemctl start postgresql
pg_isready              # should print "accepting connections"
```

### 1.3 Docker (for Part 10)

On WSL, the easiest route is **Docker Desktop for Windows**:

1. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Open Docker Desktop, then go to **Settings → Resources → WSL Integration**, and turn on integration for your Ubuntu distro.
3. Restart your WSL terminal, then check:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

If `docker: command not found` still shows up, WSL integration is not turned on for your distro (step 2).

---

## Part 2: Get the code

```bash
cd ~/clinic-booking-system        # or: git clone <repo-url> && cd clinic-booking-system
git pull
cd clinic-booking                 # ALL commands from here on run inside this folder
ls
```

You should see `app/`, `migrations/`, `tests/`, `Dockerfile`, `docker-compose.yml`, and `requirements.txt`.

> The repo root holds `README.md` and this guide. The actual project is in the `clinic-booking/` subfolder. Most "file not found" errors happen because the command ran from the wrong folder.

---

## Part 3: Create a virtual environment

### What is a virtual environment?

A virtual environment (venv) is a private folder of Python packages for **one project**. Without one, every project on your machine shares the same packages, and version clashes break things. With one:

- this project gets exactly the versions in `requirements.txt`
- nothing gets installed into your system Python
- if something goes wrong, you delete the `.venv` folder and start again

The venv is a folder called `.venv` inside `clinic-booking/`. It is already in `.gitignore`, so it never gets committed.

### 3.1 Create it

```bash
cd ~/clinic-booking-system/clinic-booking
uv venv --python 3.12 .venv
```

uv downloads Python 3.12 if you don't have it, then creates `.venv/`.

<details>
<summary>Without uv: the classic way (needs Python 3.12 already installed)</summary>

```bash
python3.12 -m venv .venv
```

If `python3.12` is not found, use uv. That's simpler than installing a second Python on Ubuntu.
</details>

### 3.2 Activate it

```bash
source .venv/bin/activate
```

Your prompt now starts with `(.venv)` or `(clinic-booking)`. That's how you know it's active.

### 3.3 Check that it worked

```bash
which python          # must end in .../clinic-booking/.venv/bin/python
python --version      # must say Python 3.12.x
```

### 3.4 Everyday rules

| Situation | What to do |
|---|---|
| New terminal opened | `cd ~/clinic-booking-system/clinic-booking && source .venv/bin/activate` |
| Done for the day | `deactivate` |
| Something is badly broken | `deactivate; rm -rf .venv` and redo Parts 3 and 4 |
| VS Code | `Ctrl+Shift+P` → "Python: Select Interpreter" → pick `.venv/bin/python` |

> **Activate the venv every time you open a new terminal.** If `pytest`, `alembic` or `uvicorn` says "command not found", you forgot this step.

---

## Part 4: Install the dependencies

With the venv **active**:

```bash
uv pip install -r requirements-dev.txt
```

(Without uv: `pip install -r requirements-dev.txt`.)

`requirements-dev.txt` contains everything in `requirements.txt` (FastAPI, SQLAlchemy, Alembic and others) **plus** the testing tools (pytest, httpx).

Check:

```bash
pip list | grep -Ei "fastapi|alembic|pytest|psycopg"
```

---

## Part 5: Set up the database

The app expects:

| Setting | Value |
|---|---|
| Host / port | `localhost:5432` |
| User / password | `clinic` / `clinic` |
| App database | `clinic` |
| Test database | `clinic_test` (the tests wipe it on every run, so keep it separate) |

Pick **one** option.

### Option A: Postgres in Docker (easiest if Docker is installed)

```bash
# If a local Postgres is running, it already holds port 5432. Stop it first:
sudo systemctl stop postgresql

docker compose up -d db
docker compose ps                 # db should show "healthy"
```

This creates both `clinic` and `clinic_test` automatically. `scripts/create-test-db.sql` runs the first time the container starts.

### Option B: Postgres installed on your machine

Create the user and both databases once:

```bash
sudo -u postgres psql -c "CREATE ROLE clinic WITH LOGIN PASSWORD 'clinic';"
sudo -u postgres psql -c "CREATE DATABASE clinic OWNER clinic;"
sudo -u postgres psql -c "CREATE DATABASE clinic_test OWNER clinic;"
```

Check that you can log in:

```bash
PGPASSWORD=clinic psql -h localhost -U clinic -d clinic -c "SELECT 1;"
```

If you see `password authentication failed for user "clinic"`, the role doesn't exist yet. Run the three commands above.

---

## Part 6: Configure and migrate

### 6.1 Create your `.env`

```bash
cp .env.example .env
cat .env
```

```ini
DATABASE_URL=postgresql+psycopg://clinic:clinic@localhost:5432/clinic
CLINIC_TIMEZONE=Africa/Nairobi
SLOT_MINUTES=30
MIN_LEAD_MINUTES=60
TEST_DATABASE_URL=postgresql+psycopg://clinic:clinic@localhost:5432/clinic_test
```

The defaults match Part 5, so you don't need to change anything. `.env` is git-ignored, so never commit it.

### 6.2 Run the migrations

```bash
alembic upgrade head
```

Expected output ends with:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, ...
INFO  [alembic.runtime.migration] Running upgrade 0001 -> 0002, Seed the clinic's 5 doctors ...
```

This creates the tables (`doctors`, `working_hours`, `patients`, `appointments`, `appointment_events`) and seeds 5 doctors. Running it again is safe, because it does nothing if the schema is already current.

Look at what it created:

```bash
PGPASSWORD=clinic psql -h localhost -U clinic -d clinic -c "\dt"
PGPASSWORD=clinic psql -h localhost -U clinic -d clinic -c "SELECT id, full_name FROM doctors;"
```

Useful Alembic commands:

| Command | Does |
|---|---|
| `alembic current` | Shows which migration the database is on |
| `alembic history` | Lists all migrations |
| `alembic downgrade -1` | Undoes the last migration |
| `alembic downgrade base` | Undoes everything (empties the schema) |

---

## Part 7: Run the API

```bash
uvicorn app.main:app --reload
```

- `app.main:app` means "in `app/main.py`, use the object called `app`"
- `--reload` restarts the server automatically when you save a code change

You should see `Uvicorn running on http://127.0.0.1:8000`.

Open these in your Windows browser (WSL forwards localhost):

| URL | What you get |
|---|---|
| http://localhost:8000/docs | **Swagger UI**: interactive docs where you can call every endpoint from the browser |
| http://localhost:8000/redoc | Read-only docs |
| http://localhost:8000/health | `{"status":"ok","database":"ok","commit":"unknown"}` |

Leave this terminal running. Open a **second terminal** for Part 8. You don't need the venv for curl.

Stop the server with `Ctrl+C`.

---

## Part 8: Test every endpoint by hand

### 8.1 The endpoints

| # | Method and path | Purpose |
|---|---|---|
| 1 | `GET /health` | Is the app up, and can it reach the database? |
| 2 | `GET /doctors` | List doctors and their weekly hours |
| 3 | `GET /doctors/{id}/availability?date=YYYY-MM-DD` | Free 30-minute slots on a date |
| 4 | `POST /patients` | Create a patient |
| 5 | `POST /appointments` | Book a slot |
| 6 | `PATCH /appointments/{id}/reschedule` | Move a booking to a new slot |
| 7 | `PATCH /appointments/{id}/cancel` | Cancel with a reason |
| 8 | `GET /patients/{id}/appointments` | A patient's upcoming bookings |

### 8.2 The seeded doctors

| ID | Doctor | Hours (Nairobi time) |
|---|---|---|
| `11111111-1111-1111-1111-111111111111` | Dr. Amina Odhiambo, General Practice | Mon–Fri 08–12 and 13–17, Sat 09–13 |
| `22222222-2222-2222-2222-222222222222` | Dr. Brian Mwangi, Paediatrics | Mon–Fri 08–12 and 13–17 |
| `33333333-3333-3333-3333-333333333333` | Dr. Cynthia Wanjiru, Gynaecology | Mon–Fri 08–13 |
| `44444444-4444-4444-4444-444444444444` | Dr. David Kiprono, Internal Medicine | Mon–Fri 12–18 |
| `55555555-5555-5555-5555-555555555555` | Dr. Esther Achieng, Dermatology | Mon, Wed, Fri 08–12 and 13–17 |

### 8.3 Booking rules to keep in mind

- Times **must include a timezone offset**: `2026-10-27T09:00:00+03:00`, not `2026-10-27T09:00:00`.
- Slots start on 30-minute boundaries inside working hours: 09:00 and 09:30 are fine, 09:10 is rejected.
- A booking must be **at least 1 hour in the future**.
- `422` means you broke a rule. `409` means there's a clash with existing data (slot taken, already cancelled). `404` means the record was not found.

### 8.4 Walk through the whole flow with curl

Paste these blocks one at a time into your second terminal. They save IDs into shell variables so you don't have to copy them by hand.

```bash
BASE=http://localhost:8000
DOC=11111111-1111-1111-1111-111111111111
DAY=$(date -d "next tuesday" +%F)        # always a future weekday
echo "Using $DAY"

# Small helper: pull "id" out of a JSON response
getid() { python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])'; }
```

**1. Health**

```bash
curl -s $BASE/health; echo
# {"status":"ok","database":"ok","commit":"unknown"}
```

**2. List doctors**

```bash
curl -s $BASE/doctors | python3 -m json.tool | head -30
```

**3. Availability**

```bash
curl -s "$BASE/doctors/$DOC/availability?date=$DAY" | python3 -m json.tool | head -20
# {"doctor_id": ..., "date": ..., "timezone": "Africa/Nairobi", "slot_minutes": 30, "slots": [{"start_at": "...T08:00:00+03:00", ...}, ...]}
```

**4. Create a patient**

```bash
PAT=$(curl -s -X POST $BASE/patients -H "content-type: application/json" \
  -d '{"full_name": "Wanjiku Kamau", "phone": "+254711222333"}' | getid)
echo "PAT=$PAT"
```

**5. Book 09:00**, which should return `201`

```bash
APPT=$(curl -s -X POST $BASE/appointments -H "content-type: application/json" \
  -d "{\"doctor_id\": \"$DOC\", \"patient_id\": \"$PAT\", \"start_at\": \"${DAY}T09:00:00+03:00\"}" | getid)
echo "APPT=$APPT"
```

Check that 09:00 is no longer in the free slots:

```bash
curl -s "$BASE/doctors/$DOC/availability?date=$DAY" | grep -c "T09:00:00"   # prints 0
```

**6. Reschedule to 14:00**, which should return `200`

```bash
curl -s -X PATCH $BASE/appointments/$APPT/reschedule -H "content-type: application/json" \
  -d "{\"start_at\": \"${DAY}T14:00:00+03:00\"}"; echo
```

**7. Upcoming appointments for the patient**

```bash
curl -s $BASE/patients/$PAT/appointments; echo
```

**8. Cancel**, which should return `200` with `"status":"cancelled"`

```bash
curl -s -X PATCH $BASE/appointments/$APPT/cancel -H "content-type: application/json" \
  -d '{"reason": "Feeling better"}'; echo
```

### 8.5 Test the error cases

`-w " -> %{http_code}\n"` prints the HTTP status after each response.

```bash
# 409 SLOT_TAKEN: a second patient tries a slot that is already booked
PAT2=$(curl -s -X POST $BASE/patients -H "content-type: application/json" \
  -d '{"full_name": "Otieno Juma", "phone": "+254722333444"}' | getid)
curl -s -X POST $BASE/appointments -H "content-type: application/json" \
  -d "{\"doctor_id\": \"$DOC\", \"patient_id\": \"$PAT\",  \"start_at\": \"${DAY}T10:00:00+03:00\"}" > /dev/null
curl -s -w " -> %{http_code}\n" -X POST $BASE/appointments -H "content-type: application/json" \
  -d "{\"doctor_id\": \"$DOC\", \"patient_id\": \"$PAT2\", \"start_at\": \"${DAY}T10:00:00+03:00\"}"

# 422 SLOT_MISALIGNED: not on a 30-minute boundary
curl -s -w " -> %{http_code}\n" -X POST $BASE/appointments -H "content-type: application/json" \
  -d "{\"doctor_id\": \"$DOC\", \"patient_id\": \"$PAT\", \"start_at\": \"${DAY}T09:10:00+03:00\"}"

# 422 OUTSIDE_WORKING_HOURS: lunch break
curl -s -w " -> %{http_code}\n" -X POST $BASE/appointments -H "content-type: application/json" \
  -d "{\"doctor_id\": \"$DOC\", \"patient_id\": \"$PAT\", \"start_at\": \"${DAY}T12:00:00+03:00\"}"

# 422 VALIDATION_ERROR: no timezone offset
curl -s -w " -> %{http_code}\n" -X POST $BASE/appointments -H "content-type: application/json" \
  -d "{\"doctor_id\": \"$DOC\", \"patient_id\": \"$PAT\", \"start_at\": \"${DAY}T09:00:00\"}"

# 409 ALREADY_CANCELLED: cancel the same appointment twice
curl -s -w " -> %{http_code}\n" -X PATCH $BASE/appointments/$APPT/cancel -H "content-type: application/json" \
  -d '{"reason": "again"}'

# 404 DOCTOR_NOT_FOUND
curl -s -w " -> %{http_code}\n" "$BASE/doctors/00000000-0000-0000-0000-000000000000/availability?date=$DAY"
```

### 8.6 Or do it all in the browser

Open http://localhost:8000/docs, click an endpoint, then **Try it out**, fill in the body, and click **Execute**. Use the same order as above: create a patient, copy its `id`, then book, reschedule and cancel.

---

## Part 9: Run the automated tests

The tests use the **`clinic_test`** database, never `clinic`. They wipe and rebuild it on every run using the real migrations.

```bash
# venv active, inside clinic-booking/, Postgres running (Part 5)
pytest                   # quick summary
pytest -v                # one line per test
```

Expected: **43 passed** (you may see a few deprecation warnings, which you can ignore).

Useful variations:

```bash
pytest tests/unit                                  # only the fast tests that need no database
pytest tests/integration/test_booking.py           # one file
pytest -k cancel                                   # tests with "cancel" in the name
pytest -x                                          # stop at the first failure
pytest -v tests/integration/test_concurrency.py    # 10 threads racing for one slot; exactly one wins
```

| Folder | What it covers |
|---|---|
| `tests/unit/` | Slot arithmetic: lunch breaks, boundaries, days off |
| `tests/integration/` | Real HTTP calls against real Postgres: booking, cancel, reschedule, availability, patients, concurrency |

---

## Part 10: Run everything with Docker

Docker runs the database **and** the API in containers. You don't need a venv or a local Postgres.

### 10.1 Start

```bash
cd ~/clinic-booking-system/clinic-booking
sudo systemctl stop postgresql          # only if a local Postgres is running (it holds port 5432)
docker compose up --build
```

What happens:

1. `db` starts (Postgres 16) and creates the `clinic` and `clinic_test` databases.
2. Compose waits until `db` is healthy.
3. `api` is built from the `Dockerfile`. On start it runs `alembic upgrade head`, then `uvicorn`.

When you see `Uvicorn running on http://0.0.0.0:8000`, open http://localhost:8000/docs.

To run in the background instead, use `docker compose up --build -d`.

### 10.2 Test the endpoints

The API is on the same `localhost:8000`, so **repeat Part 8 exactly as written**.

You can also run the test suite against the Docker database, using your venv on the host:

```bash
source .venv/bin/activate
pytest -v
```

### 10.3 Docker commands you'll use

| Command | Does |
|---|---|
| `docker compose ps` | Shows the running containers and their health |
| `docker compose logs -f api` | Follows the API logs (`Ctrl+C` to stop following) |
| `docker compose logs db` | Shows the database logs |
| `docker compose exec db psql -U clinic -d clinic` | Opens a SQL shell inside the database container |
| `docker compose up --build -d api` | Rebuilds and restarts only the API after a code change |
| `docker compose restart api` | Restarts the API without rebuilding |
| `docker compose stop` | Stops the containers and keeps the data |
| `docker compose down` | Removes the containers and **keeps** the data volume |
| `docker compose down -v` | Removes the containers **and deletes all data**, for a clean start |

> With Docker there is no `--reload`. After changing code, run `docker compose up --build -d api`.

### 10.4 Build the image on its own (what CI does)

```bash
docker build -t clinic-booking-api:local .
docker images | grep clinic-booking
```

---

## Part 11: Daily cheat sheet

**Local development (Route A):**

```bash
cd ~/clinic-booking-system/clinic-booking
source .venv/bin/activate
docker compose up -d db          # or: sudo systemctl start postgresql
alembic upgrade head             # in case new migrations were pulled
uvicorn app.main:app --reload    # terminal 1
pytest -v                        # terminal 2
```

**Everything in Docker (Route B):**

```bash
cd ~/clinic-booking-system/clinic-booking
docker compose up --build        # open http://localhost:8000/docs
docker compose down              # when done
```

**Before you push:**

```bash
pytest -v                        # must be all green
docker build -t clinic-booking-api:check .
```

---

## Part 12: Deploy to Vercel

### How it fits together

```
GitHub push to main
   └─▶ GitHub Actions: Tests ──pass──▶ alembic upgrade head (Neon) ──▶ vercel deploy --prod ──▶ poll /health
                                                                              │
Browser / curl ──HTTPS──▶ Vercel Function (FastAPI, app/main.py, region fra1) ──▶ Neon Postgres (Frankfurt)
```

| Concern | On Render (before) | On Vercel (now) |
|---|---|---|
| Runs the app | Docker container | Vercel Python Function. It finds `app/main.py` and the `app` object automatically, and ignores the Dockerfile |
| Database | Render Postgres | **Neon**, from the Vercel Marketplace (Vercel has no Postgres of its own) |
| Migrations | Container ran `alembic upgrade head` on start | **GitHub Actions** runs `alembic upgrade head` before each deploy |
| Who deploys | Render deploy hook from CI | `vercel deploy --prod` from CI. Vercel's own Git auto-deploy is turned off in `vercel.json` so nothing skips the tests |
| Python | 3.12 in Dockerfile | 3.12 from `clinic-booking/.python-version` |

Files that make this work: `clinic-booking/vercel.json`, `clinic-booking/.python-version`, `tzdata` in `requirements.txt` (time zone data, so `Africa/Nairobi` resolves on Vercel), and `.github/workflows/ci-cd.yml`.

> Everything Vercel-related runs **from inside `clinic-booking/`**. That folder is the Vercel project.

### 12.1 Install the Vercel CLI and log in

You already have Node. Then:

```bash
npm install --global vercel
vercel --version
vercel login
```

### 12.2 Create the Vercel project

```bash
cd ~/clinic-booking-system/clinic-booking
vercel link
```

Answer the prompts:

- *Set up and link?* → **Y**
- *Which scope?* → your account
- *Link to existing project?* → **N**
- *Project name?* → `clinic-booking-api`
- *In which directory is your code located?* → **`./`** (you're already inside `clinic-booking/`)

This creates `clinic-booking/.vercel/project.json` (git-ignored). It holds your `orgId` and `projectId`, which you'll need for CI.

### 12.3 Create the database (Neon)

1. Go to https://vercel.com, open the **clinic-booking-api** project, then **Storage → Create Database → Neon**.
2. Region: **Frankfurt (aws-eu-central-1)**. It matches the function region `fra1` in `vercel.json` and is the closest to Nairobi.
3. Plan: Free. Connect it to the project for **Production** (and Development if you want).

Vercel adds these environment variables to the project for you:

| Variable | Used for |
|---|---|
| `DATABASE_URL` | **Pooled** connection. The app uses it at runtime. |
| `DATABASE_URL_UNPOOLED` | **Direct** connection. Use it for migrations only. |

`CLINIC_TIMEZONE`, `SLOT_MINUTES` and `MIN_LEAD_MINUTES` already have the right defaults. Add them under **Settings → Environment Variables** only if you want to change them.

### 12.4 Run the migrations against Neon (first time)

The app won't work until the tables and seeded doctors exist. With your venv active:

```bash
cd ~/clinic-booking-system/clinic-booking
source .venv/bin/activate
vercel env pull .env.production.local --environment=production   # git-ignored

# Run inside ( ... ) so the production URL does not leak into your shell
( set -a; . ./.env.production.local; set +a
  DATABASE_URL="$DATABASE_URL_UNPOOLED" alembic upgrade head )
```

You should see the `0001` and `0002` migrations run. After this, CI handles migrations.

### 12.5 First deploy, by hand

```bash
vercel deploy --prod
```

The last line printed is your URL, for example `https://clinic-booking-api.vercel.app`. The first request after a quiet period is slower, because the function and the free Neon database both wake up on demand.

### 12.6 Test the live API

```bash
curl -s https://clinic-booking-api.vercel.app/health; echo
# {"status":"ok","database":"ok","commit":"..."}
```

Then run **all of Part 8** with one change:

```bash
BASE=https://clinic-booking-api.vercel.app
```

Swagger UI is at `https://clinic-booking-api.vercel.app/docs`.

### 12.7 Automatic deploys from GitHub

The workflow is at the **repo root** in `.github/workflows/ci-cd.yml`. GitHub only reads workflows from there.

| Trigger | Job | What it does |
|---|---|---|
| Pull request into `main` | **Tests** | Postgres 16 service, `pytest -v`, Docker image build |
| Push or merge to `main` | **Tests**, then **Deploy to Vercel** | Migrates Neon with `DATABASE_URL_UNPOOLED`, runs `vercel deploy --prod`, then polls `/health` until it reports the new commit SHA |

One-time GitHub setup: in your repo, go to **Settings → Secrets and variables → Actions**.

| Kind | Name | Where to get it |
|---|---|---|
| Secret | `VERCEL_TOKEN` | https://vercel.com/account/tokens → Create |
| Secret | `VERCEL_ORG_ID` | `orgId` in `clinic-booking/.vercel/project.json` |
| Secret | `VERCEL_PROJECT_ID` | `projectId` in the same file |
| Secret | `DATABASE_URL_UNPOOLED` | `grep DATABASE_URL_UNPOOLED clinic-booking/.env.production.local` |
| Variable | `APP_URL` | `https://clinic-booking-api.vercel.app` (no trailing slash) |

Then protect `main` under **Settings → Branches**. Require a pull request and require the **Tests** check to pass.

Normal workflow from then on:

```bash
git checkout -b feature/my-change
# ...edit, then run pytest...
git add -A && git commit -m "Describe the change"
git push -u origin feature/my-change
# open a PR → Tests run → merge → migrations + deploy run → /health shows the new SHA
```

### 12.8 Operating it

| Task | Command |
|---|---|
| See recent deployments | `vercel ls` |
| Live logs | `vercel logs https://clinic-booking-api.vercel.app` |
| Roll back to the previous deploy | `vercel rollback` (this does **not** undo migrations, so keep schema changes backward compatible) |
| Change an env var | `vercel env add NAME production`, then redeploy |
| Open a SQL shell on Neon | `psql "$DATABASE_URL_UNPOOLED"` (from the pulled env file) |

`render.yaml` is no longer used. You can delete it once Vercel is working.

---

## Part 13: Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `uvicorn: command not found` (or `pytest`, `alembic`) | The venv isn't active | `source .venv/bin/activate` |
| `which python` points to `/usr/bin/python` | The venv isn't active | Same as above |
| pip fails building `psycopg-binary` or `pydantic-core` | The venv was made with Python 3.13 or 3.14 | `rm -rf .venv && uv venv --python 3.12 .venv`, then redo Part 4 |
| `ModuleNotFoundError: No module named 'app'` | Command ran from the wrong folder | `cd ~/clinic-booking-system/clinic-booking` |
| `password authentication failed for user "clinic"` | The `clinic` role doesn't exist in your local Postgres | Run the Option B commands in Part 5 |
| `connection refused ... port 5432` | Postgres isn't running | `docker compose up -d db` or `sudo systemctl start postgresql` |
| `Bind for 0.0.0.0:5432 failed: port is already allocated` / `address already in use` | Local Postgres and Docker Postgres both want port 5432 | `sudo systemctl stop postgresql`, then `docker compose up` again |
| `address already in use` on port 8000 | Another uvicorn (or the Docker API) is running | Stop it (`Ctrl+C` or `docker compose stop api`), or use `uvicorn app.main:app --reload --port 8001` |
| `database "clinic_test" does not exist` (Docker) | The volume was created before the init script existed; the script only runs on a fresh volume | `docker compose down -v && docker compose up -d db` (deletes local data) |
| `docker: command not found` in WSL | Docker Desktop WSL integration is off | Docker Desktop → Settings → Resources → WSL Integration → turn on your distro |
| `relation "doctors" does not exist` | Migrations haven't run | `alembic upgrade head` |
| Availability returns `"slots": []` | The date is in the past, a day off, or the doctor doesn't work that weekday | Use `DAY=$(date -d "next tuesday" +%F)` |
| `422 BOOKING_TOO_SOON` | The time is less than 1 hour from now | Pick a later slot or a future date |
| `422 VALIDATION_ERROR` on `start_at` | The time is missing its offset | Add `+03:00` (or `Z` for UTC) |
| `/health` returns `503` | The API can't reach the database | Check `DATABASE_URL` in `.env` and that Postgres is up |
| Vercel build says it cannot find an entrypoint or app | `vercel` was run from the repo root instead of `clinic-booking/` | `cd clinic-booking`, then run it again |
| Live `/health` returns `503` | `DATABASE_URL` isn't set for Production, or Neon is in a different project | Vercel → Settings → Environment Variables; reconnect the Neon store to Production |
| Live API returns `relation "doctors" does not exist` | Migrations never ran on Neon | Part 12.4 |
| CI "Deploy to Vercel" says a secret is not set | A GitHub Actions secret is missing | Part 12.7 table |
| CI never runs at all | The workflow isn't at the repo root | It must be `.github/workflows/ci-cd.yml` at the top level, not inside `clinic-booking/` |
