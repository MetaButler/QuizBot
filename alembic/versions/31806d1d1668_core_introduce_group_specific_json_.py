"""[Core] Introduce group specific JSON preferences

Revision ID: 31806d1d1668
Revises: 
Create Date: 2023-10-08 00:27:29.332950

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '31806d1d1668'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('group_preferences',
                  sa.Column('settings', sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column('group_preferences', column_name='settings')
