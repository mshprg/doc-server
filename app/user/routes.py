from flask import Blueprint, request
from app.models.user import User
from app import db
import uuid

user_print = Blueprint('user', __name__)


@user_print.route('/create', methods=['POST'])
def create_user():
    data = request.get_json()
    email = data['email']
    password = data['password']
    tokens = 0
    images = 0
    hid = str(uuid.uuid4())
    new_user = User(hid=hid, email=email, password=password, tokens=tokens, images=images)

    db.session.add(new_user)
    db.session.commit()

    return new_user.to_dict()


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
