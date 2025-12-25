from models import *
from werkzeug.security import generate_password_hash, check_password_hash
import cloudinary.uploader
import os
from __init__ import db, s3_client, AWS_S3_BUCKET, AWS_REGION
import uuid
from datetime import datetime
from sqlalchemy import or_, and_




def create_user(phone, username, password, birthdate, avatar_path, email):
    hashed_password = generate_password_hash(password)

    avatar_url = None
    if avatar_path:
        # Upload bằng đường dẫn
        upload_result = cloudinary.uploader.upload(
            avatar_path,
            folder="chat_app_avatars"
        )
        avatar_url = upload_result["secure_url"]

        # XÓA FILE TẠM SAU KHI UPLOAD
        if os.path.exists(avatar_path):
            os.remove(avatar_path)
            print("Đã xóa file tạm:", avatar_path)

    user = User(
        phone=phone,
        username=username,
        password=hashed_password,
        birthdate=birthdate,
        avatar=avatar_url,
        email=email,
        role="user"
    )

    db.session.add(user)
    db.session.commit()
    return user

def get_user_by_phone(phone):
    return User.query.filter_by(phone=phone).first()

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()
 # lay id user theo id user hiện tại đăng nhập
def get_user_by_id(user_id):
    return User.query.get(user_id)



def check_login(phone, password):
    user = get_user_by_phone(phone)
    if user and check_password_hash(user.password, password):
        return user
    return None


# ---- User search ----
def find_user_by_phone(phone):
    return User.query.filter_by(phone=phone).first()

def search_users_by_phone_like(q):
    # trả về list user có phone chứa q (for search)
    return User.query.filter(User.phone.like(f"%{q}%")).all()

# ---- Friends ----
def send_friend_request(from_user_id, to_user_id):
    # nếu đã có bản ghi (pending/accepted) thì return error
    existing = Friend.query.filter(
        or_(
            and_(Friend.user_id1==from_user_id, Friend.user_id2==to_user_id),
            and_(Friend.user_id1==to_user_id, Friend.user_id2==from_user_id)
        )
    ).first()
    if existing:
        return None, "Existing friend relation"
    fr = Friend(user_id1=from_user_id, user_id2=to_user_id, status="pending")
    db.session.add(fr)
    db.session.commit()
    return fr, None

def respond_friend_request(friend_id, action):
    # action: 'accept' or 'reject' or 'block'
    f = Friend.query.get(friend_id)
    if not f:
        return None, "Not found"
    if action == "accept":
        f.status = "accepted"
    elif action == "reject":
        db.session.delete(f)
    elif action == "block":
        f.status = "blocked"
    db.session.commit()
    return f, None

def are_friends(user_a, user_b):
    f = Friend.query.filter(
        or_(
            and_(Friend.user_id1==user_a, Friend.user_id2==user_b, Friend.status=="accepted"),
            and_(Friend.user_id1==user_b, Friend.user_id2==user_a, Friend.status=="accepted")
        )
    ).first()
    return bool(f)


#
# # ---- Conversations ----
# def get_or_create_private_conversation(user_a, user_b):
#     # private conversation between two users: we can search participants pair
#     # Simplify: search conversation type private which has exactly these two participants
#     convs = Conversation.query.filter_by(type="private").all()
#     for c in convs:
#         part_user_ids = [p.user_id for p in c.participants]
#         if set(part_user_ids) == set([user_a, user_b]):
#             return c
#     # not found -> create
#     c = Conversation(type="private", name=None, created_at=datetime.utcnow(), last_message_at=None)
#     db.session.add(c)
#     db.session.flush()
#     p1 = Participant(conversation_id=c.conversation_id, user_id=user_a, role="member")
#     p2 = Participant(conversation_id=c.conversation_id, user_id=user_b, role="member")
#     db.session.add_all([p1,p2])
#     db.session.commit()
#     return c
#
# def create_group_conversation(creator_id, name, member_ids):
#     c = Conversation(type="group", name=name, created_at=datetime.utcnow())
#     db.session.add(c)
#     db.session.flush()
#     # add creator as admin
#     participants = [Participant(conversation_id=c.conversation_id, user_id=creator_id, role="admin")]
#     # only add members who are friends with creator OR allow (we'll enforce invite rule in route)
#     for mid in member_ids:
#         participants.append(Participant(conversation_id=c.conversation_id, user_id=mid, role="member"))
#     db.session.add_all(participants)
#     db.session.commit()
#     return c
#
# def add_participant(conversation_id, user_id, role="member"):
#     # avoid duplicate
#     exist = Participant.query.filter_by(conversation_id=conversation_id, user_id=user_id).first()
#     if exist:
#         return exist, "already"
#     p = Participant(conversation_id=conversation_id, user_id=user_id, role=role)
#     db.session.add(p)
#     db.session.commit()
#     return p, None
#
# # ---- Messaging ----
# def send_text_message(conversation_id, sender_id, content):
#     m = Message(conversation_id=conversation_id, sender_id=sender_id, content=content, type="text", sent_at=datetime.utcnow())
#     db.session.add(m)
#     # update conversation last_message_at
#     conv = Conversation.query.get(conversation_id)
#     if conv:
#         conv.last_message_at = datetime.utcnow()
#     db.session.commit()
#     return m
#
# def send_file_message(conversation_id, sender_id, file_name, file_url, file_size):
#     m = Message(conversation_id=conversation_id, sender_id=sender_id, content=file_url, type="file", sent_at=datetime.utcnow())
#     db.session.add(m)
#     db.session.flush()
#     f = File(message_id=m.message_id, file_name=file_name, file_url=file_url, file_size=file_size, uploaded_at=datetime.utcnow())
#     db.session.add(f)
#     conv = Conversation.query.get(conversation_id)
#     if conv:
#         conv.last_message_at = datetime.utcnow()
#     db.session.commit()
#     return m
#
# def get_messages(conversation_id, limit=50, before_id=None):
#     q = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.sent_at.desc())
#     if before_id:
#         # get messages older than message with id before_id
#         m = Message.query.get(before_id)
#         if m:
#             q = q.filter(Message.sent_at < m.sent_at)
#     return q.limit(limit).all()
#
# # ---- Files presign ----
# def generate_presigned_upload(filename, content_type, folder="uploads"):
#     key = f"{folder}/{uuid.uuid4().hex}_{filename}"
#     url = s3_client.generate_presigned_url(
#         ClientMethod='put_object',
#         Params={'Bucket': AWS_S3_BUCKET, 'Key': key, 'ContentType': content_type},
#         ExpiresIn=300
#     )
#     public_url = f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
#     return {"upload_url": url, "key": key, "file_url": public_url}
#
