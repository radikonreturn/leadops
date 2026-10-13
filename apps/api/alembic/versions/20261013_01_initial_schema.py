"""Create the LeadOps domain schema.

Revision ID: 20261013_01
Revises:
Create Date: 2026-10-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261013_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=False),
        sa.Column("contact_name", sa.String(length=150), nullable=False, server_default=""),
        sa.Column("industry", sa.String(length=100), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column("employee_range", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_companies_name", "companies", ["name"])
    op.create_index("ix_companies_industry", "companies", ["industry"])
    op.create_index("ix_companies_location", "companies", ["location"])
    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_industries", sa.JSON(), nullable=True),
        sa.Column("problems_solved", sa.JSON(), nullable=True),
        sa.Column("price_min", sa.Float(), nullable=False),
        sa.Column("price_max", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fit_score", sa.Integer(), nullable=True),
        sa.Column("opportunity_score", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("recommended_offer_id", sa.Integer(), sa.ForeignKey("offers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("score_breakdown", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_leads_status", "leads", ["status"])
    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("company_summary", sa.Text(), nullable=False),
        sa.Column("observed_facts", sa.JSON(), nullable=True),
        sa.Column("inferred_pain_points", sa.JSON(), nullable=True),
        sa.Column("automation_opportunities", sa.JSON(), nullable=True),
        sa.Column("sales_angle", sa.Text(), nullable=False),
        sa.Column("confidence", sa.String(length=50), nullable=True),
        sa.Column("fit_score", sa.Integer(), nullable=True),
        sa.Column("opportunity_score", sa.Integer(), nullable=True),
        sa.Column("raw_output", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "emails",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("style", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("why_generated", sa.Text(), nullable=True),
        sa.Column("external_draft_id", sa.String(length=255), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=True),
        sa.Column("plan", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("offer_id", sa.Integer(), sa.ForeignKey("offers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("target_industry", sa.String(length=100), nullable=True),
        sa.Column("target_company_size", sa.String(length=100), nullable=True),
        sa.Column("target_location", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("campaigns")
    op.drop_table("users")
    op.drop_table("activities")
    op.drop_table("emails")
    op.drop_table("ai_analyses")
    op.drop_index("ix_leads_status", table_name="leads")
    op.drop_table("leads")
    op.drop_table("offers")
    op.drop_index("ix_companies_location", table_name="companies")
    op.drop_index("ix_companies_industry", table_name="companies")
    op.drop_index("ix_companies_name", table_name="companies")
    op.drop_table("companies")
