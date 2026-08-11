"""add escalation policy

Revision ID: 0001
Revises: 
Create Date: 2026-08-11 17:46:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('alert_rules', sa.Column('escalation_policy', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('alert_rules', 'escalation_policy')
