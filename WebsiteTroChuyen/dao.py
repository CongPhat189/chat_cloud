from models import *
from werkzeug.security import generate_password_hash, check_password_hash


def create_user(phone, username, password, birthdate, avatar, email):
    hashed_password = generate_password_hash(password)
    user = User(
        phone=phone,
        username=username,
        password=hashed_password,
        birthdate=birthdate,
        avatar=avatar,
        email=email
    )
    db.session.add(user)
    db.session.commit()
    return user

def get_user_by_phone(phone):
    return User.query.filter_by(phone=phone).first()

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def check_login(phone, password):
    user = get_user_by_phone(phone)
    if user and check_password_hash(user.password, password):
        return user
    return None