"""Initial Alembic revision (empty baseline).

SQLAlchemy tables arrive in Phase 2.3; this revision keeps ``alembic upgrade head``
runnable immediately after Postgres is up.

"""

from collections.abc import Sequence

revision: str = "20260513_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No DDL yet — registry only."""
    pass


def downgrade() -> None:
    pass
