"""initial schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(255), nullable=False), sa.Column("full_name", sa.String(160), nullable=False), sa.Column("password_hash", sa.String(512), nullable=False), sa.Column("role", sa.String(50), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("sources", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("kind", sa.String(50), nullable=False), sa.Column("name", sa.String(160), nullable=False), sa.Column("status", sa.String(50), nullable=False), sa.Column("last_synced_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_sources_kind", "sources", ["kind"])
    op.create_table("observations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")), sa.Column("source_url", sa.String(1000)), sa.Column("content_type", sa.String(40), nullable=False), sa.Column("raw_text", sa.Text(), nullable=False), sa.Column("seller_name", sa.String(160)), sa.Column("brand", sa.String(100)), sa.Column("model_name", sa.String(160)), sa.Column("size", sa.String(30)), sa.Column("price", sa.Float()), sa.Column("city", sa.String(120)), sa.Column("availability", sa.String(40), nullable=False), sa.Column("status", sa.String(40), nullable=False), sa.Column("confidence", sa.Float()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("signals", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("observation_id", sa.Integer(), sa.ForeignKey("observations.id"), nullable=False), sa.Column("kind", sa.String(60), nullable=False), sa.Column("intensity", sa.String(30), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))


def downgrade() -> None:
    op.drop_table("signals")
    op.drop_table("observations")
    op.drop_index("ix_sources_kind", table_name="sources")
    op.drop_table("sources")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

