"""add deleted_at to reports

Revision ID: 20260412_000002
Revises: 20260412_000001
Create Date: 2026-04-12 00:00:02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260412_000002"
down_revision: Union[str, None] = "20260412_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "deleted_at")
