"""empty message

Revision ID: badb776d038b
Revises: 2ef3ff74cb5c
Create Date: 2017-09-04 02:54:54.777000

"""

# revision identifiers, used by Alembic.
revision = 'badb776d038b'
down_revision = '2ef3ff74cb5c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('activity', sa.Column('faq', sa.String(length=4096), nullable=True))
    op.create_foreign_key(None, 'auction_purchase', 'participant', ['participant_id'], ['id'])
    op.create_foreign_key(None, 'auction_purchase', 'activity', ['activity_id'], ['id'])
    op.create_foreign_key(None, 'participant', 'activity', ['activity_id'], ['id'])
    op.create_foreign_key(None, 'product', 'activity', ['activity_id'], ['id'])
    op.create_foreign_key(None, 'purchase', 'product', ['product_id'], ['id'])
    op.create_foreign_key(None, 'purchase', 'participant', ['participant_id'], ['id'])
    op.create_foreign_key(None, 'purchase', 'activity', ['activity_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'purchase', type_='foreignkey')
    op.drop_constraint(None, 'purchase', type_='foreignkey')
    op.drop_constraint(None, 'purchase', type_='foreignkey')
    op.drop_constraint(None, 'product', type_='foreignkey')
    op.drop_constraint(None, 'participant', type_='foreignkey')
    op.drop_constraint(None, 'auction_purchase', type_='foreignkey')
    op.drop_constraint(None, 'auction_purchase', type_='foreignkey')
    op.drop_column('activity', 'faq')
    # ### end Alembic commands ###