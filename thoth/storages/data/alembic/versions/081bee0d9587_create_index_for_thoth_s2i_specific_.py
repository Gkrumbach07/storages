"""Create index for Thoth s2i specific name and version

Revision ID: 081bee0d9587
Revises: f1824f0c1afa
Create Date: 2021-01-29 08:17:53.055331+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "081bee0d9587"
down_revision = "f1824f0c1afa"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index("thoth_s2i_image_name", "software_environment", ["thoth_s2i_image_version"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("thoth_s2i_image_name", table_name="software_environment")
    # ### end Alembic commands ###