"""add is_revoked to refresh_tokens

Revision ID: 66bd20d211e9
Revises: 94e9fd1f2b55
Create Date: 2025-12-14 21:54:25.335178

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66bd20d211e9'
down_revision: Union[str, Sequence[str], None] = '94e9fd1f2b55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "refresh_tokens",
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.text("0"))
    )


def downgrade() -> None:
    op.drop_column("refresh_tokens", "is_revoked")
