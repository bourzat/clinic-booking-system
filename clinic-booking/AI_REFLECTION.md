# AI reflection

> Draft for you to finish. The facts below are what actually happened in the Claude session that produced this repository. Edit them to match your own experience, delete anything you did not do, and write section 4 yourself. Remove this note before submitting.

## 1. What I used AI for across the four sections

- **Section 1, design:** I asked Claude for a system design for the clinic scenario, then asked it to cut the draft down to the design and the process flows only. <!-- Add: what you changed, kept, or pushed back on. -->
- **Section 2, API:** Claude generated the FastAPI code, the Alembic migrations and the test suite, and ran the tests against a local PostgreSQL. <!-- Add: what you reviewed line by line, what you rewrote. -->
- **Section 3, deployment:** Claude wrote the Dockerfile, `docker-compose.yml`, `render.yaml` and the GitHub Actions workflow. <!-- Add: what you had to fix when you actually deployed. -->
- **Section 4:** Claude drafted the factual parts of this file from the session. The judgments in section 4 are mine.

## 2. One example where an AI suggestion improved the work

<!-- Pick one that is true for you. A candidate from the session: -->

- **Prompt:** "Please give me a very good system design" with the assessment PDF attached.
- **What it changed:** the design moved double-booking protection out of application code and into a PostgreSQL partial unique index on `(doctor_id, start_at) WHERE status = 'booked'`. A check-then-insert in Python is not safe when two requests arrive together or when there is more than one API instance. The index also frees a slot automatically on cancel and reschedule, which removed a whole category of "forgot to release the slot" bugs.
- **How I confirmed it:** `tests/integration/test_concurrency.py` fires 10 simultaneous bookings for one slot and asserts exactly one succeeds.

## 3. One example where AI output was wrong or incomplete, and how it was caught

<!-- These happened in the session. Say honestly who caught each one. They were caught by running the test suite during generation, not by reading the code. -->

- **Wrong test expectation.** A unit test claimed a 09:45 start in a 09:15 to 10:15 block "runs past the end of the block". It does not: 09:45 plus 30 minutes is exactly 10:15. The test failed on the first run and the test was corrected, not the code.
- **A concurrency test that silently tested the wrong thing.** The cancel-versus-reschedule race test loaded the appointment in a second session but did not keep a reference to it. SQLAlchemy's identity map holds objects weakly, so the object was garbage-collected and the "stale" session quietly reloaded fresh data. The test got `APPOINTMENT_CANCELLED` instead of the expected `CONCURRENT_MODIFICATION`. Fixed by holding the reference and asserting the stale state before the race.
- **The full test run hung.** Because that failing test never closed its second session, its open transaction held a lock, and the next test's `TRUNCATE` waited forever. Running the test files one at a time with a timeout isolated it. The fix wraps the session in `try/finally`.

## 4. Two decisions I made without AI, and why I trusted my own judgment

<!-- Write these yourself. They need to be real decisions you made and can defend in an interview. Examples of the kind of thing that fits: choosing Render over another host because of what you have run before; deciding to keep tests on real Postgres instead of SQLite; overriding a rule from the design; choosing the deploy branch protection setup. -->

1. 
2. 
