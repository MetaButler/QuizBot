"""Change UserPreferences user_id from Integer to BigInteger

Revision ID: 24f7964a757d
Revises: 31806d1d1668
Create Date: 2023-11-06 00:36:09.470599

"""
from enum import unique
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '24f7964a757d'
down_revision: Union[str, None] = '31806d1d1668'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_preferences_new',
        sa.Column('user_id',
                  sa.BigInteger,
                  primary_key=True,
                  unique=True,
                  nullable=False),
        sa.Column('settings', sa.JSON, nullable=True),
    )
    op.execute(
        "INSERT INTO user_preferences_new (user_id, settings) SELECT user_id, settings FROM user_preferences"
    )
    op.drop_table('user_preferences')
    op.execute("ALTER TABLE user_preferences_new RENAME TO user_preferences")


def downgrade() -> None:
    op.create_table(
        'user_preferences_new',
        sa.Column('user_id',
                  sa.Integer,
                  primary_key=True,
                  unique=True,
                  nullable=False),
        sa.Column('settings', sa.JSON, nullable=True),
    )
    op.execute(
        "INSERT INTO user_preferences_new (user_id, settings) SELECT user_id, settings FROM user_preferences"
    )
    op.drop_table('user_preferences')
    op.execute("ALTER TABLE user_preferences_new RENAME TO user_preferences")
