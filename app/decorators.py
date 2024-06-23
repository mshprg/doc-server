from functools import wraps
from flask import request, jsonify
import os
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()


@auth.verify_password
def check_auth_token(auth_header):
    if auth_header == os.environ.get('SECRET_API_KEY'):
        return True
    return False


# Декоратор для проверки авторизации
def check_authorization(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not check_auth_token(auth_header):
            return jsonify({"message": "Authorization required"}), 401
        return f(*args, **kwargs)
    return decorated_function
