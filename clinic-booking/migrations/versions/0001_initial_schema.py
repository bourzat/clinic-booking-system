"""Initial schema

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "doctors",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("specialty", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "working_hours",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("doctor_id", sa.Uuid(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_working_hours_weekday"),
        sa.CheckConstraint("start_time < end_time", name="ck_working_hours_order"),
    )
    op.create_index("ix_working_hours_doctor_id", "working_hours", ["doctor_id"])

    op.create_table(
        "patients",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("doctor_id", sa.Uuid(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('booked', 'cancelled')", name="ck_appointments_status"),
        sa.CheckConstraint("end_at > start_at", name="ck_appointments_order"),
        sa.CheckConstraint(
            "(status = 'cancelled' AND cancel_reason IS NOT NULL AND cancelled_at IS NOT NULL)"
            " OR (status = 'booked' AND cancelled_at IS NULL)",
            name="ck_appointments_cancel_fields",
        ),
    )
    # The double-booking guarantee: one active booking per doctor per start time.
    op.create_index(
        "uq_doctor_active_slot", "appointments", ["doctor_id", "start_at"],
        unique=True, postgresql_where=sa.text("status = 'booked'"),
    )
    # A patient cannot be in two places at once. Also serves "upcoming appointments for a patient".
    op.create_index(
        "uq_patient_active_slot", "appointments", ["patient_id", "start_at"],
        unique=True, postgresql_where=sa.text("status = 'booked'"),
    )

    op.create_table(
        "appointment_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("appointment_id", sa.Uuid(), sa.ForeignKey("appointments.id"), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_appointment_events_appointment_id", "appointment_events", ["appointment_id"])


def downgrade() -> None:
    op.drop_table("appointment_events")
    op.drop_table("appointments")
    op.drop_table("patients")
    op.drop_table("working_hours")
    op.drop_table("doctors")
