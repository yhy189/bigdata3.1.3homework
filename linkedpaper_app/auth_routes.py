from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from models import db, User

auth_routes = Blueprint('auth_routes', __name__)  # 定义蓝图

# 注册页面
@auth_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        # 检查用户名和邮箱是否已经存在
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 409
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        # 创建并保存新用户
        user = User(username=username, email=email)
        user.password = password  # 此处应对密码进行哈希处理
        db.session.add(user)
        db.session.commit()

        # 存储用户名和密码到 session
        session['username'] = username
        session['password'] = password  # 注意：不应直接存储密码

        return redirect(url_for('auth_routes.login'))

    return render_template('register.html')

# 登录页面
@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    # 从 session 中获取用户名和密码
    username = session.get('username', '')
    password = session.get('password', '')

    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')

        # 验证用户和密码
        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            # session['user_id'] = user.id  # 存储用户ID到session
            # flash('登录成功！', 'info')

            # 登录成功后清除 session 中的用户名和密码
            session.pop('password', None)

            return redirect(url_for('paper_routes.mainpage'))

        return jsonify({"error": "Invalid username or password"}), 401

    return render_template('login.html', username=username, password=password)