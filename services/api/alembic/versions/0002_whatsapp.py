"""WhatsApp Business Cloud API storage."""
from alembic import op
import sqlalchemy as sa

revision = "0002_whatsapp"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("waba_id", sa.String(100), nullable=False),
        sa.Column("phone_number_id", sa.String(100), nullable=False),
        sa.Column("display_phone_number", sa.String(40)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_whatsapp_accounts_owner_user_id", "whatsapp_accounts", ["owner_user_id"])
    op.create_index("ix_whatsapp_accounts_phone_number_id", "whatsapp_accounts", ["phone_number_id"], unique=True)
    op.create_table(
        "whatsapp_contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("whatsapp_accounts.id"), nullable=False),
        sa.Column("wa_id", sa.String(128), nullable=False),
        sa.Column("phone_number", sa.String(40)),
        sa.Column("display_name", sa.String(160)),
        sa.UniqueConstraint("account_id", "wa_id", name="uq_whatsapp_contact_account_wa"),
    )
    op.create_index("ix_whatsapp_contacts_account_id", "whatsapp_contacts", ["account_id"])
    op.create_table(
        "whatsapp_conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("whatsapp_accounts.id"), nullable=False),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("whatsapp_contacts.id"), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True)),
        sa.Column("last_customer_message_at", sa.DateTime(timezone=True)),
        sa.Column("unread_count", sa.Integer(), nullable=False),
        sa.UniqueConstraint("account_id", "contact_id", name="uq_whatsapp_conversation_contact"),
    )
    op.create_index("ix_whatsapp_conversations_account_id", "whatsapp_conversations", ["account_id"])
    op.create_index("ix_whatsapp_conversations_contact_id", "whatsapp_conversations", ["contact_id"])
    op.create_table(
        "whatsapp_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("whatsapp_accounts.id"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("whatsapp_conversations.id"), nullable=False),
        sa.Column("meta_message_id", sa.String(160), nullable=False),
        sa.Column("direction", sa.String(12), nullable=False),
        sa.Column("message_type", sa.String(30), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("media_id", sa.String(160)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("account_id", "meta_message_id", name="uq_whatsapp_message_meta_id"),
    )
    op.create_index("ix_whatsapp_messages_account_id", "whatsapp_messages", ["account_id"])
    op.create_index("ix_whatsapp_messages_conversation_id", "whatsapp_messages", ["conversation_id"])
    op.create_index("ix_whatsapp_messages_timestamp", "whatsapp_messages", ["timestamp"])
    op.create_table(
        "whatsapp_media",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("whatsapp_accounts.id"), nullable=False),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("whatsapp_messages.id"), nullable=False),
        sa.Column("meta_media_id", sa.String(160), nullable=False),
        sa.Column("media_type", sa.String(30), nullable=False),
        sa.Column("mime_type", sa.String(120)),
        sa.Column("file_name", sa.String(255)),
        sa.Column("caption", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_whatsapp_media_account_id", "whatsapp_media", ["account_id"])
    op.create_index("ix_whatsapp_media_message_id", "whatsapp_media", ["message_id"])
    op.create_index("ix_whatsapp_media_meta_media_id", "whatsapp_media", ["meta_media_id"])
    op.create_table(
        "whatsapp_message_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("whatsapp_accounts.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("language_code", sa.String(20), nullable=False),
        sa.Column("category", sa.String(40)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("account_id", "name", "language_code", name="uq_whatsapp_template_account_name_language"),
    )
    op.create_index("ix_whatsapp_message_templates_account_id", "whatsapp_message_templates", ["account_id"])
    op.create_table(
        "whatsapp_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_key", sa.String(128), nullable=False, unique=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("whatsapp_message_templates")
    op.drop_table("whatsapp_media")
    op.drop_table("whatsapp_webhook_events")
    op.drop_table("whatsapp_messages")
    op.drop_table("whatsapp_conversations")
    op.drop_table("whatsapp_contacts")
    op.drop_table("whatsapp_accounts")
