import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:205305@localhost/mylinked_papers'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)
