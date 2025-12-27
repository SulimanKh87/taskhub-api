# alembic/versions/0001_init_schema.py

from alembic import op
import sqlalchemy as sa


# ------------------------------------------------------------
# Revision identifiers
# ------------------------------------------------------------
revision = "0001_init_schema"
down_revision = None
branch_labels = None
depends_on = None


# ------------------------------------------------------------
# Upgrade
# ------------------------------------------------------------
def upgrade() -> None:
    # ----------------------------
    # USERS TABLE
    # ----------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "idx_users_username",
        "users",
        ["username"],
        unique=True,
    )

    # ----------------------------
    # TASKS TABLE
    # ----------------------------
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "idx_tasks_owner_created_at",
        "tasks",
        ["owner_id", sa.text("created_at DESC")],
    )

    # ----------------------------
    # JOB LOG TABLE (IDEMPOTENCY)
    # ----------------------------
    op.create_table(
        "job_log",
        sa.Column("job_id", sa.String(), primary_key=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


# ------------------------------------------------------------
# Downgrade
# ------------------------------------------------------------
def downgrade() -> None:
    op.drop_table("job_log")
    op.drop_index("idx_tasks_owner_created_at", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("idx_users_username", table_name="users")
    op.drop_table("users")
