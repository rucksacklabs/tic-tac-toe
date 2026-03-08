"""moves: replace x, y coordinates with position index

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-08 00:00:00.000000

Purpose: Replace the x and y coordinate columns on the moves table with a flat
         position integer (0–8) where position = y * 3 + x.
Architecture: Persistence Layer (Migrations).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add position column derived from x and y, then drop x and y."""
    op.add_column("moves", sa.Column("position", sa.Integer(), nullable=True))

    # Back-fill: position = y * 3 + x
    op.execute("UPDATE moves SET position = y * 3 + x")

    with op.batch_alter_table("moves") as batch_op:
        batch_op.alter_column("position", nullable=False)
        batch_op.drop_column("x")
        batch_op.drop_column("y")


def downgrade() -> None:
    """Restore x and y columns from position, then drop position."""
    op.add_column("moves", sa.Column("x", sa.Integer(), nullable=True))
    op.add_column("moves", sa.Column("y", sa.Integer(), nullable=True))

    # Back-fill: x = position % 3, y = position / 3
    op.execute("UPDATE moves SET x = position % 3, y = position / 3")

    with op.batch_alter_table("moves") as batch_op:
        batch_op.alter_column("x", nullable=False)
        batch_op.alter_column("y", nullable=False)
        batch_op.drop_column("position")
