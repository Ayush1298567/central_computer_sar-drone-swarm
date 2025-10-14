"""init P9 models

Revision ID: 20251012_000001
Revises: 
Create Date: 2025-10-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251012_000001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # mission_logs
    op.create_table(
        'mission_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('mission_id', sa.Integer(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text()),
        sa.Column('payload', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_mission_logs_mission_id', 'mission_logs', ['mission_id'])

    # drone_state_history
    op.create_table(
        'drone_state_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('mission_id', sa.Integer(), sa.ForeignKey('missions.id'), nullable=True),
        sa.Column('drone_id', sa.Integer(), sa.ForeignKey('drones.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50)),
        sa.Column('connection_status', sa.String(length=50)),
        sa.Column('position_lat', sa.Float()),
        sa.Column('position_lng', sa.Float()),
        sa.Column('position_alt', sa.Float()),
        sa.Column('heading', sa.Float()),
        sa.Column('speed', sa.Float()),
        sa.Column('battery_level', sa.Float()),
        sa.Column('signal_strength', sa.Integer()),
        sa.Column('extra', sa.JSON()),
    )
    op.create_index('ix_drone_state_history_mission', 'drone_state_history', ['mission_id'])
    op.create_index('ix_drone_state_history_drone', 'drone_state_history', ['drone_id'])
    op.create_index('ix_drone_state_history_ts', 'drone_state_history', ['timestamp'])


def downgrade() -> None:
    op.drop_index('ix_drone_state_history_ts', table_name='drone_state_history')
    op.drop_index('ix_drone_state_history_drone', table_name='drone_state_history')
    op.drop_index('ix_drone_state_history_mission', table_name='drone_state_history')
    op.drop_table('drone_state_history')
    op.drop_index('ix_mission_logs_mission_id', table_name='mission_logs')
    op.drop_table('mission_logs')


