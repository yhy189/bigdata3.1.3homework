from flask import Blueprint, request, jsonify, render_template, redirect, url_for
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
        user.password = password
        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201

    return render_template('register.html')


# 登录页面
@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')

        # 验证用户和密码
        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            return jsonify({"message": "Login successful"}), 200

        return jsonify({"error": "Invalid username or password"}), 401

    return render_template('login.html')

