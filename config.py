import os
basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = '-I\xc1me\x91\xd5\xfcQ\xd2V:\xc2W\xba3\xb18d\x08\xa4\x80\xe6E'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.db')

MULTIPLE_ENABLE = True

MULTIPLE_AGE_LIMIT = True

AGE_LIMIT = 18