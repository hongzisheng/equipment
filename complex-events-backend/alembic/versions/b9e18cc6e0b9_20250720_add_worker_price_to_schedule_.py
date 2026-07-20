"""20250720_add_worker_price_to_schedule_tasks

Revision ID: b9e18cc6e0b9
Revises: 090d5bc6a73e
Create Date: 2026-07-20 15:38:59.452108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'b9e18cc6e0b9'
down_revision: Union[str, None] = '090d5bc6a73e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('schedule_tasks', sa.Column('worker_price', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('schedule_tasks', 'worker_price')
