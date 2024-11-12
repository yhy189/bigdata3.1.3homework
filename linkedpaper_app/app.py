from flask import Flask, redirect, url_for
from config import Config
from models import db
from auth_routes import auth_routes  # 引入auth_routes蓝图
from paper_routes import paper_routes  # 导入 `paper_routes`
app = Flask(__name__)

app.config.from_object(Config)
db.init_app(app)
@app.route('/')
def home():
    return redirect(url_for('auth_routes.login'))  # 重定向到auth_routes蓝图中的login路由
# 注册蓝图
app.register_blueprint(auth_routes, url_prefix='/auth')  # 设置蓝图的前缀为'/auth'
app.register_blueprint(paper_routes,url_prefix='/paper')
# 初始化数据库
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
