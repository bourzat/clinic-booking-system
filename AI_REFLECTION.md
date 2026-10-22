# AI Reflection

## 1. How I utilized AI across the project
I leveraged Claude strictly as an execution engine to accelerate development, while retaining full ownership of all architectural and engineering decisions.

* **Design:** I defined the system architecture and clinic process flows, directing Claude only to format my decisions into structured documentation.
* **API:** I established the data models and endpoint contracts. Claude scaffolded the repetitive FastAPI boilerplate, Alembic migrations, and initial test suite, which I manually audited and refined.
* **Deployment:** I determined the containerization strategy. Claude executed this by writing the Dockerfile, `docker-compose.yml`, `render.yaml`, and GitHub Actions workflow based on my exact specifications.
* **Reflection:** Claude generated the raw session timeline; all analytical judgments and evaluations are entirely my own.

## 2. An AI suggestion that improved implementation

* **The implementation:** When addressing double-booking protection, Claude suggested enforcing it via a PostgreSQL partial unique index on `(doctor_id, start_at) WHERE status = 'booked'`.
* **My evaluation:** I approved and adopted this approach because application-level check-then-insert logic is fundamentally unsafe under concurrent load. Pushing this constraint to the database guarantees atomicity and automatically frees slots on cancellation.
* **Verification:** I validated this by engineering a concurrency test (`tests/integration/test_concurrency.py`) that fires 10 simultaneous bookings for one slot, asserting exactly one succeeds.

## 3. Catching AI errors and incomplete logic

* **Test logic errors:** Claude generated a unit test claiming a 09:45 start in a 09:15-10:15 block "runs past the block." I caught this basic arithmetic error during review and corrected the test expectation.
* **ORM lifecycle flaws:** Claude wrote a concurrency test that loaded an appointment but failed to maintain a strong reference to it. SQLAlchemy's weak identity map garbage-collected the object, causing the session to quietly reload fresh data. I diagnosed the ORM behavior and fixed the assertion to properly catch the `CONCURRENT_MODIFICATION`.
* **Database deadlocks:** The faulty test never closed its session, holding a lock that caused the next test's `TRUNCATE` to hang forever. I isolated the hanging test using timeouts and implemented a `try/finally` block to guarantee strict session teardown.

## 4. Engineering decisions I made independently

1. **Defining the concurrency testing strategy:** I explicitly chose to prioritize database integration tests over mocked unit tests for the core booking logic, knowing that mocked ORM objects cannot accurately simulate transaction isolation and real-world race conditions.
2. **Architecting the deployment topology:** I designed the containerized multi-tier architecture to ensure strict parity between local development and the Render production environment, instructing Claude only on the syntax of the config files rather than the infrastructure design.
