"""empty message

Revision ID: 001
Revises: 
Create Date: 2025-12-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE category_enum AS ENUM ('shared', 'reseller', 'vps', 'dedicated', 'cloud', 'colo', 'other')")
    op.execute("CREATE TYPE billing_period_enum AS ENUM ('month', 'year', 'one_time')")
    op.execute("CREATE TYPE fingerprint_type_enum AS ENUM ('strict', 'fuzzy')")

    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('base_url', sa.String(length=500), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create deal_posts table
    op.create_table(
        'deal_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('source_thread_id', sa.String(length=100), nullable=True),
        sa.Column('canonical_url', sa.String(length=1000), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('author', sa.String(length=200), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('category', sa.Enum('shared', 'reseller', 'vps', 'dedicated', 'cloud', 'colo', 'other', name='category_enum'), nullable=True),
        sa.Column('raw_html', sa.Text(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_id', 'canonical_url', name='uq_source_url')
    )

    # Create indexes for deal_posts
    op.create_index('ix_deal_posts_posted_at', 'deal_posts', ['posted_at'])
    op.create_index('ix_deal_posts_category', 'deal_posts', ['category'])
    op.create_index('ix_deal_posts_is_duplicate', 'deal_posts', ['is_duplicate'])

    # Create deal_items table
    op.create_table(
        'deal_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_post_id', sa.Integer(), nullable=False),
        sa.Column('provider_name', sa.String(length=200), nullable=True),
        sa.Column('provider_domain', sa.String(length=200), nullable=True),
        sa.Column('price_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('price_currency', sa.String(length=3), nullable=True),
        sa.Column('billing_period', sa.Enum('month', 'year', 'one_time', name='billing_period_enum'), nullable=True),
        sa.Column('price_monthly_normalized', sa.Numeric(10, 2), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('cpu', sa.String(length=100), nullable=True),
        sa.Column('ram_mb', sa.Integer(), nullable=True),
        sa.Column('storage_gb', sa.Integer(), nullable=True),
        sa.Column('bandwidth_gb', sa.Integer(), nullable=True),
        sa.Column('order_url', sa.String(length=1000), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['deal_post_id'], ['deal_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for deal_items
    op.create_index('ix_deal_items_price_monthly_normalized', 'deal_items', ['price_monthly_normalized'])
    op.create_index('ix_deal_items_billing_period', 'deal_items', ['billing_period'])
    op.create_index('ix_deal_items_price_currency', 'deal_items', ['price_currency'])
    op.create_index('ix_deal_items_provider_domain', 'deal_items', ['provider_domain'])

    # Create deal_fingerprints table
    op.create_table(
        'deal_fingerprints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_post_id', sa.Integer(), nullable=False),
        sa.Column('fingerprint', sa.String(length=64), nullable=False),
        sa.Column('fingerprint_type', sa.Enum('strict', 'fuzzy', name='fingerprint_type_enum'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['deal_post_id'], ['deal_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for fingerprints
    op.create_index('ix_deal_fingerprints_fingerprint', 'deal_fingerprints', ['fingerprint'])
    op.create_index('ix_deal_fingerprints_type', 'deal_fingerprints', ['fingerprint_type'])

    # Insert initial sources
    op.execute("""
        INSERT INTO sources (name, base_url, enabled) VALUES
        ('hostingdiscussion', 'https://hostingdiscussion.com', true),
        ('lowendtalk', 'https://lowendtalk.com', true),
        ('webhostingtalk', 'https://www.webhostingtalk.com', false)
    """)


def downgrade() -> None:
    op.drop_table('deal_fingerprints')
    op.drop_table('deal_items')
    op.drop_table('deal_posts')
    op.drop_table('sources')
    op.execute("DROP TYPE fingerprint_type_enum")
    op.execute("DROP TYPE billing_period_enum")
    op.execute("DROP TYPE category_enum")
