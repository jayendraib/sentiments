"""
Initial migration for call transcription and analysis system

Revision ID: 001_initial_schema
down_revision: None
Create Date: 2026-04-08 18:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Create all tables for the call transcription and analysis system.
    """
    # TABLE: agents_numbers
    op.create_table(
        'agents_numbers',
        sa.Column('agent_id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('phone_number', sa.String(15), nullable=False, unique=True),
    )
    
    op.create_index('idx_agents_numbers_phone', 'agents_numbers', ['phone_number'])
    op.create_index('idx_agents_numbers_name', 'agents_numbers', ['agent_name'])
    
    # TABLE: call_records_test
    op.create_table(
        'call_records_test',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('source_pbx_call_id', sa.Text(), nullable=False, unique=True),
        sa.Column('agent_id', sa.Text(), nullable=True),
        sa.Column('calling_number', sa.Text(), nullable=True),
        sa.Column('called_number', sa.Text(), nullable=True),
        sa.Column('call_type', sa.Text(), nullable=True),
        sa.Column('call_connected', sa.Text(), nullable=True),
        sa.Column('conversation_duration', sa.Integer(), nullable=True),
        sa.Column('call_start_time', sa.DateTime(), nullable=True),
        sa.Column('call_end_time', sa.DateTime(), nullable=True),
        sa.Column('call_status', sa.Text(), nullable=True),
        sa.Column('voice_file_path_local', sa.Text(), nullable=True),
        sa.Column('station_id', sa.Text(), nullable=True),
        sa.Column('s3_file_path', sa.Text(), nullable=True),
        sa.Column('processed_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    op.create_index('idx_call_records_source_pbx_id', 'call_records_test', ['source_pbx_call_id'])
    op.create_index('idx_call_records_agent_id', 'call_records_test', ['agent_id'])
    op.create_index('idx_call_records_start_time', 'call_records_test', ['call_start_time'])
    op.create_index('idx_call_records_created', 'call_records_test', ['created_at'])
    
    # TABLE: call_audio
    op.create_table(
        'call_audio',
        sa.Column('call_audio_id', sa.Text(), primary_key=True),
        sa.Column('user_name', sa.Text(), nullable=True),
        sa.Column('audio_path', sa.Text(), nullable=True),
        sa.Column('call_recording_link', sa.Text(), nullable=False),
        sa.Column('transcribed_text', sa.Text(), nullable=True),
        sa.Column('analysis_done', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('call_duration_sec', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('idx_call_audio_analysis_done', 'call_audio', ['analysis_done'])
    op.create_index('idx_call_audio_user_name', 'call_audio', ['user_name'])
    
    # TABLE: call_analysis
    op.create_table(
        'call_analysis',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('agent_name', sa.Text(), nullable=False),
        sa.Column('call_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    op.create_index('idx_call_analysis_agent_name', 'call_analysis', ['agent_name'])
    op.create_index('idx_call_analysis_created', 'call_analysis', ['created_at'])
    op.create_index('idx_call_analysis_json_gin', 'call_analysis', ['call_json'], postgresql_using='gin')


def downgrade():
    
    
    op.drop_table('call_analysis')
    op.drop_table('call_audio')
    op.drop_table('call_records_test')
    op.drop_table('agents_numbers')
    
