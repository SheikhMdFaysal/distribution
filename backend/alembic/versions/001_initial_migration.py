"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-02-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create attack_scenarios table
    op.create_table(
        'attack_scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.String(length=100), nullable=False),
        sa.Column('scenario_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('target_model_type', sa.Enum('enterprise', 'public', 'local', name='modeltype'), nullable=True),
        sa.Column('data_classification', sa.Enum('public', 'internal', 'confidential', 'restricted', name='dataclassification'), nullable=True),
        sa.Column('compliance_frameworks', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('severity_threshold', sa.String(length=50), nullable=True),
        sa.Column('attack_techniques', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('vendor_promise_tested', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scenario_id')
    )
    op.create_index(op.f('ix_attack_scenarios_id'), 'attack_scenarios', ['id'], unique=False)
    op.create_index(op.f('ix_attack_scenarios_scenario_id'), 'attack_scenarios', ['scenario_id'], unique=True)

    # Create security_tests table
    op.create_table(
        'security_tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('attack_scenario_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('queued', 'running', 'completed', 'failed', name='teststatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('techniques', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('target_models', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('variants_per_technique', sa.Integer(), nullable=True),
        sa.Column('total_variants', sa.Integer(), nullable=True),
        sa.Column('total_runs', sa.Integer(), nullable=True),
        sa.Column('runs_completed', sa.Integer(), nullable=True),
        sa.Column('vulnerabilities_found', sa.Integer(), nullable=True),
        sa.Column('avg_risk_score', sa.Float(), nullable=True),
        sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risklevel'), nullable=True),
        sa.ForeignKeyConstraint(['attack_scenario_id'], ['attack_scenarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_tests_id'), 'security_tests', ['id'], unique=False)

    # Create baseline_prompts table
    op.create_table(
        'baseline_prompts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('security_test_id', sa.Integer(), nullable=True),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['security_test_id'], ['security_tests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_baseline_prompts_id'), 'baseline_prompts', ['id'], unique=False)

    # Create style_variants table
    op.create_table(
        'style_variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('baseline_prompt_id', sa.Integer(), nullable=True),
        sa.Column('technique', sa.String(length=50), nullable=False),
        sa.Column('variant_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['baseline_prompt_id'], ['baseline_prompts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_style_variants_id'), 'style_variants', ['id'], unique=False)

    # Create model_runs table
    op.create_table(
        'model_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('style_variant_id', sa.Integer(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_type', sa.Enum('enterprise', 'public', 'local', name='modeltype'), nullable=False),
        sa.Column('model_vendor', sa.String(length=50), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('response_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['style_variant_id'], ['style_variants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_runs_id'), 'model_runs', ['id'], unique=False)

    # Create evaluation_scores table
    op.create_table(
        'evaluation_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_run_id', sa.Integer(), nullable=True),
        sa.Column('leakage_detected', sa.Boolean(), nullable=True),
        sa.Column('leakage_categories', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risklevel'), nullable=True),
        sa.Column('data_classification', sa.String(length=50), nullable=True),
        sa.Column('compliance_violations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('vendor_promise', sa.Text(), nullable=True),
        sa.Column('promise_held', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['model_run_id'], ['model_runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluation_scores_id'), 'evaluation_scores', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_evaluation_scores_id'), table_name='evaluation_scores')
    op.drop_table('evaluation_scores')
    op.drop_index(op.f('ix_model_runs_id'), table_name='model_runs')
    op.drop_table('model_runs')
    op.drop_index(op.f('ix_style_variants_id'), table_name='style_variants')
    op.drop_table('style_variants')
    op.drop_index(op.f('ix_baseline_prompts_id'), table_name='baseline_prompts')
    op.drop_table('baseline_prompts')
    op.drop_index(op.f('ix_security_tests_id'), table_name='security_tests')
    op.drop_table('security_tests')
    op.drop_index(op.f('ix_attack_scenarios_scenario_id'), table_name='attack_scenarios')
    op.drop_index(op.f('ix_attack_scenarios_id'), table_name='attack_scenarios')
    op.drop_table('attack_scenarios')
