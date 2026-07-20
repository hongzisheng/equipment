"""Remove _equipment_instances_old_20260401 table and related foreign keys

Revision ID: c8d24b0057ff
Revises: 9c3cc3e98a5c
Create Date: 2026-07-20 12:47:09.051387

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d24b0057ff'
down_revision: Union[str, None] = '9c3cc3e98a5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('_equipment_instances_old_20260401')


def downgrade() -> None:
    op.create_table(
        '_equipment_instances_old_20260401',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('equipment_type_id', sa.VARCHAR(length=50), nullable=False),
        sa.Column('name', sa.VARCHAR(length=200), nullable=False),
        sa.Column('status', sa.VARCHAR(length=20), nullable=True),
        sa.Column('created_time', sa.TEXT(), nullable=True),
        sa.Column('category', sa.TEXT(), nullable=True),
        sa.Column('equipment_type_name', sa.TEXT(), nullable=True),
        sa.ForeignKeyConstraint(['equipment_type_id'], ['equipment_types.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )