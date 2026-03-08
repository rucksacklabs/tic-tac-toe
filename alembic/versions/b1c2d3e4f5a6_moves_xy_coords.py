"""moves: replace position with x, y coordinates

Revision ID: b1c2d3e4f5a6
Revises: 09794d5025fc
Create Date: 2026-03-07 22:00:00.000000

Purpose: Replace the flat position integer (0–8) on the moves table with explicit
         x and y coordinate columns (both 0–2).
Architecture: Persistence Layer (Migrations).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "09794d5025fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add x and y columns derived from position, then drop position."""
    # Add x and y columns, temporarily nullable to back-fill existing rows.
    op.add_column("moves", sa.Column("x", sa.Integer(), nullable=True))
    op.add_column("moves", sa.Column("y", sa.Integer(), nullable=True))

    # Back-fill: x = position % 3, y = position // 3
    op.execute("UPDATE moves SET x = position % 3, y = position / 3")

    # Make x and y non-nullable now that all rows have values.
    with op.batch_alter_table("moves") as batch_op:
        batch_op.alter_column("x", nullable=False)
        batch_op.alter_column("y", nullable=False)
        batch_op.drop_column("position")


def downgrade() -> None:
    """Restore position column from x and y, then drop x and y."""
    op.add_column("moves", sa.Column("position", sa.Integer(), nullable=True))
    op.execute("UPDATE moves SET position = y * 3 + x")

    with op.batch_alter_table("moves") as batch_op:
        batch_op.alter_column("position", nullable=False)
        batch_op.drop_column("x")
        batch_op.drop_column("y")
