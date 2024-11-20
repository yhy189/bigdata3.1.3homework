from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from models import db, User
from flask_bcrypt import Bcrypt

auth_routes = Blueprint('auth_routes', __name__)
bcrypt = Bcrypt()  # Initialize bcrypt

# Registration page
@auth_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        # Check if username and email already exist
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 409
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        # Create and save new user
        user = User(username=username, email=email)
        user.password = password  # This should hash the password automatically via the User model setter
        db.session.add(user)
        db.session.commit()

        # Store username in session (do not store password)
        session['username'] = username

        flash('Registration successful! You can now log in.', 'info')
        return redirect(url_for('auth_routes.login'))

    return render_template('register.html')

# Login page
@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')

        # 查找用户
        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            # 将用户信息存入 session
            session['username'] = username
            session['role'] = user.role  # 存储角色信息

            flash('Login successful!', 'info')
            return redirect(url_for('paper_routes.mainpage'))

        # 用户名或密码无效
        return jsonify({"error": "Invalid username or password"}), 401

    # 如果是 GET 请求，返回登录页面
    return render_template('login.html')