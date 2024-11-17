from flask import Flask, redirect, url_for
from config import Config
from linkedpaper_app.import_data import import_data
from models import db
from auth_routes import auth_routes
from paper_routes import paper_routes

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

@app.route('/')
def home():
    return redirect(url_for('auth_routes.login'))

# 注册蓝图
app.register_blueprint(auth_routes, url_prefix='/auth')
app.register_blueprint(paper_routes, url_prefix='/paper')

# 数据库初始化
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
