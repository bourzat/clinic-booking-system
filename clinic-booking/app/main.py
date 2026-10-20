from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from app.api import appointments, doctors, health, patients
from app.core.errors import DomainError


def create_app() -> FastAPI:
    app = FastAPI(
        title="Clinic Booking API",
        version="1.0.0",
        description="Book, cancel and reschedule 30-minute appointments with the clinic's doctors.",
    )

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        fields = [
            {"field": ".".join(str(p) for p in err["loc"] if p != "body"), "problem": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "VALIDATION_ERROR", "message": "The request is not valid.", "details": {"fields": fields}}},
        )

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse("/docs")

    app.include_router(health.router)
    app.include_router(doctors.router)
    app.include_router(patients.router)
    app.include_router(appointments.router)
    return app


app = create_app()
