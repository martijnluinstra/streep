"""empty message

Revision ID: 5fe157e974b3
Revises: 208180c6d195
Create Date: 2016-08-26 23:00:58.170000

"""

# revision identifiers, used by Alembic.
revision = '5fe157e974b3'
down_revision = '208180c6d195'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('activity_participant')
    op.add_column('participant', sa.Column('activity_id', sa.Integer(), nullable=False))
    op.add_column('participant', sa.Column('cover_id', sa.Integer(), nullable=True))
    op.add_column('participant', sa.Column('has_agreed_to_terms', sa.Boolean(), nullable=False))
    op.drop_index('name', table_name='participant')
    op.create_unique_constraint(None, 'participant', ['name', 'activity_id'])
    op.create_unique_constraint(None, 'participant', ['cover_id', 'activity_id'])
    op.create_foreign_key(None, 'participant', 'activity', ['activity_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'participant', type_='foreignkey')
    op.drop_constraint(None, 'participant', type_='unique')
    op.drop_constraint(None, 'participant', type_='unique')
    op.create_index('name', 'participant', ['name'], unique=True)
    op.drop_column('participant', 'has_agreed_to_terms')
    op.drop_column('participant', 'cover_id')
    op.drop_column('participant', 'activity_id')
    op.create_table('activity_participant',
    sa.Column('participant_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('activity_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('agree_to_terms', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['activity_id'], [u'activity.id'], name=u'activity_participant_ibfk_1'),
    sa.ForeignKeyConstraint(['participant_id'], [u'participant.id'], name=u'activity_participant_ibfk_2'),
    sa.PrimaryKeyConstraint('participant_id', 'activity_id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    ### end Alembic commands ###
