from flask import Response, Blueprint, request
import bcrypt
from app.models.user import User
import uuid

user_print = Blueprint('user', __name__)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


@user_print.route('/create', methods=['POST'])
def create_user():
    data = request.get_json()
    email = data['email']
    password = data['password']
    tokens = 100
    hid = str(uuid.uuid4())
    new_user = User(hid=hid, email=email, password=hash_password(password), tokens=tokens)

    # TODO: Регистарция


@user_print.route('/login', methods=['POST'])
def login():
    # TODO: Авторизация
    ...


@user_print.route('/get/all', methods=['GET'])
def get_all_users():
    users = User.query.all()
    response = []
    for user in users:
        response.append(user.to_dict())

    return response


@user_print.route('/get/<hid>', methods=['GET'])
def get_user(hid: str):
    user = User.query.filter(User.hid == hid).first()

    return user.to_dict()
