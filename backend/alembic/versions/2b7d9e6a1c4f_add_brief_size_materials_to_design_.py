"""add brief, product_size, materials to design_requests

Revision ID: 2b7d9e6a1c4f
Revises: 9a1c2e4f7b3d
Create Date: 2026-07-21 20:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2b7d9e6a1c4f'
down_revision: Union[str, Sequence[str], None] = '9a1c2e4f7b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('design_requests', sa.Column('brief', sa.Text(), nullable=True))
    op.add_column('design_requests', sa.Column('product_size', sa.String(length=255), nullable=True))
    op.add_column('design_requests', sa.Column('materials', sa.ARRAY(sa.String()), nullable=True))


def downgrade() -> None:
    op.drop_column('design_requests', 'materials')
    op.drop_column('design_requests', 'product_size')
    op.drop_column('design_requests', 'brief')
