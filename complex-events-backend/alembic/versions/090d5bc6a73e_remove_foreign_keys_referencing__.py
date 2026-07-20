"""Remove foreign keys referencing _equipment_instances_old_20260401

Revision ID: 090d5bc6a73e
Revises: c8d24b0057ff
Create Date: 2026-07-20 13:01:28.676500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '090d5bc6a73e'
down_revision: Union[str, None] = 'c8d24b0057ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    conn.execute(sa.text("""
        CREATE TABLE work_orders_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number VARCHAR(50),
            title VARCHAR(200),
            equipment_id INTEGER,
            equipment_name VARCHAR(100),
            status VARCHAR(20),
            created_by INTEGER,
            created_at DATETIME,
            scheduled_start_time INTEGER,
            scheduled_end_time INTEGER,
            actual_start_time INTEGER,
            actual_end_time INTEGER,
            priority VARCHAR(10),
            remarks TEXT,
            plan_id INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """))
    
    conn.execute(sa.text("""
        INSERT INTO work_orders_new SELECT * FROM work_orders
    """))
    
    conn.execute(sa.text("DROP TABLE work_orders"))
    conn.execute(sa.text("ALTER TABLE work_orders_new RENAME TO work_orders"))
    
    conn.execute(sa.text("""
        CREATE TABLE work_order_tasks_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_id INTEGER,
            task_code VARCHAR(50),
            process_id VARCHAR(100),
            process_name VARCHAR(200),
            equipment_id INTEGER,
            equipment_name VARCHAR(100),
            description TEXT,
            estimated_hours REAL,
            scheduled_start_time TEXT,
            scheduled_end_time TEXT,
            actual_start_time TEXT,
            actual_end_time TEXT,
            status VARCHAR(20),
            predecessor_task_ids TEXT,
            is_milestone BOOLEAN,
            workers TEXT,
            approver_id INTEGER,
            approval_comments TEXT,
            approved_at DATETIME,
            created_at DATETIME,
            updated_at DATETIME,
            attachment_path TEXT,
            process_code TEXT,
            FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE
        )
    """))
    
    conn.execute(sa.text("""
        INSERT INTO work_order_tasks_new SELECT * FROM work_order_tasks
    """))
    
    conn.execute(sa.text("DROP TABLE work_order_tasks"))
    conn.execute(sa.text("ALTER TABLE work_order_tasks_new RENAME TO work_order_tasks"))


def downgrade() -> None:
    pass