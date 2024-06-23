from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from app.decorators import check_authorization

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    cors = CORS(app, resources={r"*": {"origins": "*"}})

    db.init_app(app)

    # Импортируем и регистрируем Blueprint
    from app.chat.routes import chat
    from app.message.routes import message
    app.register_blueprint(message, url_prefix='/message')
    app.register_blueprint(chat, url_prefix='/chat')

    with app.app_context():
        db.create_all()

    return app
