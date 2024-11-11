import base64

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    _email = db.Column("email", db.String(120), nullable=False, unique=True)  # 加密 email
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), default='common')

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def email(self):
        return base64.b64decode(self._email).decode('utf-8')

    @email.setter
    def email(self, email):
        self._email = base64.b64encode(email.encode('utf-8')).decode('utf-8')

    def __repr__(self):
        return f'<User {self.username}>'
class Paper(db.Model):
    __tablename__ = 'papers'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    abstract = db.Column(db.Text)
    category = db.Column(db.String(50))
    year = db.Column(db.Integer)

class NodeFeat(db.Model):
    __tablename__ = 'node_feat'
    id = db.Column(db.Integer, primary_key=True)
    # 动态创建 feature_1 到 feature_128 的列
    for i in range(1, 129):
        vars()[f'feature_{i}'] = db.Column(db.Float)

class Citation(db.Model):
    __tablename__ = 'citations'
    id = db.Column(db.Integer, primary_key=True)
    citing_paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=False)
    cited_paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=False)
