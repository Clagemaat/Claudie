"""seed one default user per role

Revision ID: 9a1c2e4f7b3d
Revises: 4c4b1fb3294f
Create Date: 2026-07-21 19:30:00.000000

"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import insert as pg_insert

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9a1c2e4f7b3d'
down_revision: Union[str, Sequence[str], None] = '4c4b1fb3294f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed IDs/emails so this migration is idempotent (safe to run against a
# database that already has these rows) and so the seeded users are
# recognizable/stable across environments - the "pick your user" login
# screen has nothing to select on a brand-new database otherwise.
# The 4th column is the Postgres "role" enum's stored representation -
# SQLAlchemy's Enum type persists the Python enum member's *name*
# (upper snake case), not its .value, unless configured otherwise.
DEFAULT_USERS = [
    ("11111111-0000-0000-0000-000000000001", "Default Sales Rep", "sales@claudie.demo", "SALES"),
    ("11111111-0000-0000-0000-000000000002", "Default Traffic Manager", "traffic-manager@claudie.demo", "TRAFFIC_MANAGER"),
    ("11111111-0000-0000-0000-000000000003", "Default Lead Designer", "lead-designer@claudie.demo", "LEAD_DESIGNER"),
    ("11111111-0000-0000-0000-000000000004", "Default DTP Designer", "dtp-designer@claudie.demo", "DTP_DESIGNER"),
    ("11111111-0000-0000-0000-000000000005", "Default Costing", "costing@claudie.demo", "COSTING"),
    ("11111111-0000-0000-0000-000000000006", "Default Sales Director", "sales-director@claudie.demo", "SALES_DIRECTOR"),
    ("11111111-0000-0000-0000-000000000007", "Default Item Creator", "item-creator@claudie.demo", "ITEM_CREATOR"),
    ("11111111-0000-0000-0000-000000000008", "Default Admin", "admin@claudie.demo", "ADMIN"),
]

users_table = sa.table(
    "users",
    sa.column("id", sa.Uuid()),
    sa.column("name", sa.String()),
    sa.column("email", sa.String()),
)
user_roles_table = sa.table(
    "user_roles",
    sa.column("id", sa.Uuid()),
    sa.column("user_id", sa.Uuid()),
    sa.column("role", PGEnum(name="role", create_type=False)),
)


def upgrade() -> None:
    for user_id, name, email, role in DEFAULT_USERS:
        op.execute(
            pg_insert(users_table)
            .values(id=uuid.UUID(user_id), name=name, email=email)
            .on_conflict_do_nothing(index_elements=["email"])
        )
        op.execute(
            pg_insert(user_roles_table)
            .values(id=uuid.uuid4(), user_id=uuid.UUID(user_id), role=role)
            .on_conflict_do_nothing(constraint="uq_user_role")
        )


def downgrade() -> None:
    ids = [uuid.UUID(user_id) for user_id, *_ in DEFAULT_USERS]
    op.execute(user_roles_table.delete().where(user_roles_table.c.user_id.in_(ids)))
    op.execute(users_table.delete().where(users_table.c.id.in_(ids)))
