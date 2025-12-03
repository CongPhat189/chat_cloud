from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON

from WebsiteTroChuyen import db, app




class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    birthdate = db.Column(db.Date, nullable=True)
    avatar = db.Column(db.String(255), nullable=True)

    # Quan hệ
    sent_messages = db.relationship("Message", backref="sender", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


class Friend(db.Model):
    __tablename__ = "friends"

    friend_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id1 = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    user_id2 = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    status = db.Column(db.Enum("pending", "accepted", "blocked"), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Conversation(db.Model):
    __tablename__ = "conversations"

    conversation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.Enum("private", "group"), nullable=False)
    name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, nullable=True)

    # Quan hệ
    participants = db.relationship("Participant", backref="conversation", lazy=True)
    messages = db.relationship("Message", backref="conversation", lazy="dynamic")


class Participant(db.Model):
    __tablename__ = "participants"

    participant_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversations.conversation_id"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    role = db.Column(db.Enum("admin", "member"), default="member")
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")


class Message(db.Model):
    __tablename__ = "messages"

    message_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversations.conversation_id"), nullable=False
    )
    sender_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), nullable=False
    )
    content = db.Column(db.Text, nullable=True)
    type = db.Column(db.Enum("text", "image", "file"), default="text")
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_by = db.Column(JSON, nullable=True)  # MySQL JSON

    # Quan hệ file
    files = db.relationship("File", backref="message", lazy=True)


class File(db.Model):
    __tablename__ = "files"

    file_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(
        db.Integer, db.ForeignKey("messages.message_id"), nullable=False
    )
    file_name = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<File {self.file_name}>"
if __name__=='__main__':
    with app.app_context():

        db.drop_all()
        db.create_all()