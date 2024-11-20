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
    favorite_papers = db.Column(db.Text, default="")  # 存储收藏的论文 ID，逗号分隔

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

    def add_favorite_paper(self, paper_id):
        """收藏一篇论文"""
        if not self.favorite_papers:
            self.favorite_papers = str(paper_id)
        else:
            favorites = set(self.favorite_papers.split(','))
            favorites.add(str(paper_id))
            self.favorite_papers = ','.join(favorites)

    def remove_favorite_paper(self, paper_id):
        """取消收藏一篇论文"""
        if not self.favorite_papers:
            return
        favorites = set(self.favorite_papers.split(','))
        favorites.discard(str(paper_id))
        self.favorite_papers = ','.join(favorites)

    def get_favorite_papers(self):
        """获取用户收藏的论文 ID 列表"""
        return list(map(int, self.favorite_papers.split(','))) if self.favorite_papers else []

    def get_role(self):
        """获取用户角色"""
        return self.role
    def __repr__(self):
        return f'<User {self.username}>'


class Paper(db.Model):
    __tablename__ = 'papers'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    abstract = db.Column(db.Text)
    category = db.Column(db.String(50))
    year = db.Column(db.Integer)
    frequency = db.Column(db.Integer, default=0)  # 被查看次数，默认为 0

    def increment_frequency(self):
        """增加被查看次数"""
        self.frequency += 1
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'abstract': self.abstract,
            'category': self.category,
            'year': self.year,
            'frequency': self.frequency
        }


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
