"""Data sources table — CSV and API data sources for projects.

Revision ID: 002
Revises: 001
Create Date: 2026-06-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ──
    data_source_type = postgresql.ENUM(
        "csv", "api", name="data_source_type", create_type=False
    )
    data_source_type.create(op.get_bind(), checkfirst=True)

    data_source_status = postgresql.ENUM(
        "pending", "uploaded", "previewed", "ready", "error",
        name="data_source_status", create_type=False,
    )
    data_source_status.create(op.get_bind(), checkfirst=True)

    # ── Data Sources ──
    op.create_table(
        "data_sources",
        sa.Column(
            "id", sa.UUID(), nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", data_source_type, nullable=False),
        sa.Column(
            "status", data_source_status, nullable=False,
            server_default="pending",
        ),
        # CSV fields
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        # API fields
        sa.Column("api_url", sa.String(2048), nullable=True),
        sa.Column("api_method", sa.String(10), nullable=True, server_default="GET"),
        sa.Column("api_headers", sa.JSON(), nullable=True),
        # Column metadata & preview
        sa.Column("columns", sa.JSON(), nullable=True),
        sa.Column("preview_data", sa.JSON(), nullable=True),
        # Error tracking
        sa.Column("error_message", sa.Text(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_data_sources_project_id", "data_sources", ["project_id"]
    )
    op.create_index(
        "ix_data_sources_organization_id", "data_sources", ["organization_id"]
    )


def downgrade() -> None:
    op.drop_table("data_sources")
    op.execute("DROP TYPE IF EXISTS data_source_status")
    op.execute("DROP TYPE IF EXISTS data_source_type")
