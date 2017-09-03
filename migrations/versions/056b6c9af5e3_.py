"""empty message

Revision ID: 056b6c9af5e3
Revises: 5fe157e974b3
Create Date: 2017-09-03 22:04:34.873000

"""

# revision identifiers, used by Alembic.
revision = '056b6c9af5e3'
down_revision = '5fe157e974b3'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('activity', 'credit_value')
    op.drop_column('activity', 'trade_credits')
    op.create_foreign_key(None, 'auction_purchase', 'participant', ['participant_id'], ['id'])
    op.create_foreign_key(None, 'auction_purchase', 'activity', ['activity_id'], ['id'])
    op.create_foreign_key(None, 'participant', 'activity', ['activity_id'], ['id'])
    op.create_foreign_key(None, 'product', 'activity', ['activity_id'], ['id'])
    op.create_foreign_key(None, 'purchase', 'product', ['product_id'], ['id'])
    op.create_foreign_key(None, 'purchase', 'participant', ['participant_id'], ['id'])
    op.create_foreign_key(None, 'purchase', 'activity', ['activity_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'purchase', type_='foreignkey')
    op.drop_constraint(None, 'purchase', type_='foreignkey')
    op.drop_constraint(None, 'purchase', type_='foreignkey')
    op.drop_constraint(None, 'product', type_='foreignkey')
    op.drop_constraint(None, 'participant', type_='foreignkey')
    op.drop_constraint(None, 'auction_purchase', type_='foreignkey')
    op.drop_constraint(None, 'auction_purchase', type_='foreignkey')
    op.add_column('activity', sa.Column('trade_credits', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False))
    op.add_column('activity', sa.Column('credit_value', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    ### end Alembic commands ###
