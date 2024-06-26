import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.decorators import check_authorization

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    cors = CORS(app, resources={r"*": {"origins": "*"}})

    db.init_app(app)

    # Импортируем и регистрируем Blueprint
    from app.chat.routes import chat_print
    from app.message.routes import message_print
    from app.user.routes import user_print
    app.register_blueprint(message_print, url_prefix='/message')
    app.register_blueprint(chat_print, url_prefix='/chat')
    app.register_blueprint(user_print, url_prefix='/user')

    with app.app_context():
        db.create_all()

    return app
