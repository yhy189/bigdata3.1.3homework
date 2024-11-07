from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from linkedpaper_app.import_data import import_data
from models import db  # 假设模型在 models.py 文件中
from config import Config
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
with app.app_context():
    db.create_all()
    import_data()
if __name__ == '__main__':
    app.run(debug=True)