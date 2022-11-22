"""Fix NULL values considered as distinct for postgres < 15

Revision ID: bf9ea2a38b01
Revises: 7f7411e247d6
Create Date: 2022-11-22 08:09:49.556833+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bf9ea2a38b01"
down_revision = "7f7411e247d6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("has_symbol", "software_environment_id", existing_type=sa.INTEGER(), nullable=False)
    op.alter_column("has_symbol", "versioned_symbol_id", existing_type=sa.INTEGER(), nullable=False)
    op.create_unique_constraint(None, "python_package_version_entity_rule", ["id"])
    op.drop_index("thoth_s2i_image_name", table_name="software_environment")
    op.create_index("thoth_image_name", "software_environment", ["thoth_image_version"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("thoth_image_name", table_name="software_environment")
    op.create_index("thoth_s2i_image_name", "software_environment", ["thoth_image_version"], unique=False)
    op.drop_constraint(None, "python_package_version_entity_rule", type_="unique")
    op.alter_column("has_symbol", "versioned_symbol_id", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column("has_symbol", "software_environment_id", existing_type=sa.INTEGER(), nullable=True)
    # ### end Alembic commands ###
