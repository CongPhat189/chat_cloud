from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from flask_mail import Mail, Message as MailMessage

from dao import *
from datetime import datetime, timedelta, UTC
import random, uuid, os
from sqlalchemy import and_, or_, func
import json


from __init__ import app, socketio

mail = Mail(app)

# ---------------- Đăng ký ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        phone = request.form.get("phone")
        username = request.form.get("username")
        password = request.form.get("password")
        birthdate = request.form.get("birthdate")
        email = request.form.get("email")
        avatar_file = request.files.get("avatar")

        # Kiểm tra thiếu thông tin
        if not all([phone, username, password, birthdate, email]):
            flash("Vui lòng điền đầy đủ thông tin!")
            return redirect(url_for("register"))

        # Check tồn tại
        if get_user_by_phone(phone):
            flash("Số điện thoại đã được đăng ký!")
            return redirect(url_for("register"))

        if get_user_by_email(email):
            flash("Email đã được đăng ký!")
            return redirect(url_for("register"))

        # Tạo OTP
        otp = random.randint(100000, 999999)
        otp_expire = datetime.now() + timedelta(minutes=5)

        session["otp"] = otp
        session["otp_expire"] = otp_expire.strftime("%Y-%m-%d %H:%M:%S")

        # Lưu file avatar tạm
        avatar_path = None
        if avatar_file:
            temp_name = f"temp_{uuid.uuid4().hex}.jpg"
            avatar_path = os.path.join("temp_uploads", temp_name)

            os.makedirs("temp_uploads", exist_ok=True)
            avatar_file.save(avatar_path)

        # Lưu thông tin vào session
        session["reg_data"] = {
            "phone": phone,
            "username": username,
            "password": password,
            "birthdate": birthdate,
            "email": email,
            "role": "user",
            "avatar_path": avatar_path  # <--- LƯU ĐƯỜNG DẪN FILE TẠM
        }

        # Gửi OTP qua email
        try:
            msg = MailMessage("OTP Xác thực đăng ký", recipients=[email])
            msg.body = f"Mã OTP của bạn là {otp}. Hiệu lực 5 phút."
            mail.send(msg)

            flash("OTP đã được gửi tới email của bạn!")
            return redirect(url_for("verify_otp"))

        except Exception as e:
            print("Email error:", e)
            flash("Gửi email thất bại, vui lòng thử lại.")
            return redirect(url_for("register"))

    return render_template("register.html")



# ---------------- Xác thực OTP ----------------
@app.route("/verify", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form['otp']
        if 'otp' not in session or 'otp_expire' not in session:
            flash("OTP không tồn tại, vui lòng đăng ký lại.")
            return redirect(url_for("register"))

        expire_time = datetime.strptime(session['otp_expire'], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expire_time:
            session.pop('otp')
            session.pop('otp_expire')
            session.pop('reg_data')
            flash("OTP đã hết hạn, vui lòng đăng ký lại.")
            return redirect(url_for("register"))

        if str(session['otp']) == entered_otp:
            data = session['reg_data']
            birthdate_obj = datetime.strptime(data['birthdate'], "%Y-%m-%d").date()
            create_user(
                data['phone'],
                data['username'],
                data['password'],
                birthdate_obj,
                data['avatar_path'],
                data['email']
            )
            session.pop('otp')
            session.pop('otp_expire')
            session.pop('reg_data')
            flash("Đăng ký thành công! Bạn có thể đăng nhập.")
            return redirect(url_for("login"))
        else:
            flash("OTP không đúng, vui lòng thử lại.")
            return redirect(url_for("verify_otp"))

    return render_template("verify_otp.html")

# ---------------- Đăng nhập ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form['phone']
        password = request.form['password']
        user = check_login(phone, password)
        if user:
            session['user_id'] = user.user_id
            flash(f"Chào mừng {user.username}!")
            return redirect(url_for("chat"))

        else:
            flash("Số điện thoại hoặc mật khẩu không đúng.")
            return redirect(url_for("login"))
    return render_template('login.html')
@app.route("/logout")
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.")
    return redirect(url_for("login"))

@app.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    return render_template("chat.html", user=user)

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("chat"))
    return redirect(url_for("login"))



# Serch fiend
@app.route("/api/search-users")
def search_users():
    phone = request.args.get("phone", "").strip()

    if not phone:
        return jsonify([])
    users = User.query.filter(
        User.phone.like(f"{phone}%")   # 👈 KHỚP TỪ ĐẦU
    ).all()

    return jsonify([
        {
            "user_id": u.user_id,
            "username": u.username,
            "phone": u.phone,
            "avatar": u.avatar
        } for u in users
    ])

# Check Friend
@app.route("/api/check-friend")
def check_friend():
    if "user_id" not in session:
        return jsonify({"error": "not_login"}), 401

    me = session["user_id"]
    other_id = int(request.args.get("user_id"))

    uid1, uid2 = sorted([me, other_id])

    relation = Friend.query.filter_by(
        user_id1=uid1,
        user_id2=uid2
    ).first()

    if not relation:
        return jsonify({"status": "none"})

    return jsonify({
        "status": relation.status,
        "is_sender": relation.sender_id == me
    })

# APi gui ket ban
@app.route("/api/send-friend", methods=["POST"])
def send_friend():
    if "user_id" not in session:
        return jsonify({"error": "not_login"}), 401

    me = session["user_id"]
    other_id = int(request.json["user_id"])

    uid1, uid2 = sorted([me, other_id])

    if Friend.query.filter_by(user_id1=uid1, user_id2=uid2).first():
        return jsonify({"error": "exists"}), 400

    db.session.add(Friend(
        user_id1=uid1,
        user_id2=uid2,
        sender_id=me,
        status="pending"
    ))
    db.session.commit()

    return jsonify({"success": True})

# Api đồng ý
@app.route("/api/accept-friend", methods=["POST"])
def accept_friend():
    if "user_id" not in session:
        return jsonify({"error": "not_login"}), 401

    me = session["user_id"]
    other_id = int(request.json.get("user_id"))

    uid1, uid2 = sorted([me, other_id])

    relation = Friend.query.filter_by(
        user_id1=uid1,
        user_id2=uid2,
        status="pending"
    ).first()

    if not relation:
        return jsonify({"error": "not_found"}), 404

    # chỉ người nhận mới được đồng ý
    if relation.sender_id == me:
        return jsonify({"error": "not_allowed"}), 403

    relation.status = "accepted"
    conv = Conversation(type="private")
    db.session.add(conv)
    db.session.flush()

    db.session.add_all([
        Participant(conversation_id=conv.conversation_id, user_id=me),
        Participant(conversation_id=conv.conversation_id, user_id=other_id)
    ])

    db.session.commit()

    return jsonify({"success": True})


# API HỦY KẾT BẠN
@app.route("/api/cancel-friend", methods=["POST"])
def cancel_friend():
    if "user_id" not in session:
        return jsonify({"error": "not_login"}), 401

    me = session["user_id"]
    other_id = int(request.json.get("user_id"))

    uid1, uid2 = sorted([me, other_id])

    relation = Friend.query.filter_by(
        user_id1=uid1,
        user_id2=uid2
    ).first()

    if not relation:
        return jsonify({"error": "not_found"}), 404

    db.session.delete(relation)
    db.session.commit()

    return jsonify({"success": True})


@app.route("/api/chat-list")
def api_chat_list():
    if "user_id" not in session:
        return jsonify([])

    me = session["user_id"]

    # 1️⃣ Lấy các quan hệ friend (pending + accepted)
    friends = Friend.query.filter(
        Friend.status.in_(["pending", "accepted"]),
        ((Friend.user_id1 == me) | (Friend.user_id2 == me))
    ).all()

    result = []

    for f in friends:
        # 2️⃣ Xác định user còn lại
        other_id = f.user_id2 if f.user_id1 == me else f.user_id1
        other_user = db.session.get(User, other_id)

        if not other_user:
            continue

        # 3️⃣ Lấy conversation 1–1
        conv = (
            db.session.query(Conversation)
            .join(Participant, Participant.conversation_id == Conversation.conversation_id)
            .filter(
                Conversation.type == "private",
                Participant.user_id.in_([me, other_id])
            )
            .group_by(Conversation.conversation_id)
            .having(db.func.count(Participant.user_id) == 2)
            .first()
        )

        last_msg = None

        if conv:
            last_msg = Message.query.filter_by(
                conversation_id=conv.conversation_id
            ).order_by(Message.sent_at.desc()).first()

        result.append({
            "user_id": other_user.user_id,
            "username": other_user.username,
            "avatar": other_user.avatar,
            "friend_status": f.status,

            "last_message": (
                "Hình ảnh" if last_msg and last_msg.type == "image"
                else last_msg.content if last_msg
                else ""
            ),

            "last_message_type": last_msg.type if last_msg else None,

            "last_timestamp": last_msg.sent_at.timestamp() if last_msg else 0
        })

    # 4️⃣ Sắp xếp theo tin nhắn mới nhất
    result.sort(key=lambda x: x["last_timestamp"], reverse=True)

    return jsonify(result)

# Lấy danh sách User trong cuộc trò chuyện
@app.route("/api/get-user/<int:user_id>")
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    return jsonify({
        "user_id": user.user_id,
        "username": user.username,
        "avatar": user.avatar
    })


@app.route("/api/send-message", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401

    conversation_id = request.form.get("conversation_id", type=int)
    msg_type = request.form.get("type", "text")
    content = request.form.get("content", "").strip()

    images = request.files.getlist("images")
    files = request.files.getlist("files")

    if not conversation_id:
        return jsonify({"error": "missing conversation"}), 400

    convo = db.session.get(Conversation, conversation_id)
    if not convo:
        return jsonify({"error": "conversation not found"}), 404

    stored_content = None

    # =====================
    # IMAGE
    # =====================
    if msg_type == "image" and images:
        image_urls = []

        for img in images[:3]:
            result = cloudinary.uploader.upload(
                img,
                folder="chat_images"
            )
            image_urls.append(result["secure_url"])

        stored_content = json.dumps(image_urls)

    # =====================
    # FILE                                                                   
    # =====================
    elif msg_type == "file" and files:
        file_infos = []

        for f in files[:3]:
            # dùng tên + đuôi làm public_id
            public_id = f.filename  # ví dụ: "Book1.xlsx"

            result = cloudinary.uploader.upload(
                f,
                resource_type="raw",
                folder="chat_files",
                public_id=public_id  # giữ luôn đuôi
            )

            file_infos.append({
                "name": f.filename,
                "url": result["secure_url"]  # giờ sẽ có đuôi
            })

        stored_content = json.dumps(file_infos)

    # =====================
    # TEXT
    # =====================
    else:
        msg_type = "text"
        stored_content = content

    # =====================
    # SAVE DB
    # =====================
    msg = Message(
        conversation_id=conversation_id,
        sender_id=session["user_id"],
        type=msg_type,
        content=stored_content
    )

    db.session.add(msg)
    convo.last_message_at = datetime.now(UTC)
    db.session.commit()

    return jsonify({
        "sender_id": msg.sender_id,
        "type": msg.type,
        "content": json.loads(msg.content) if msg.type != "text" else msg.content,
        "sent_at": msg.sent_at.isoformat()
    })



@app.route("/api/messages/<int:conversation_id>")
def get_messages(conversation_id):
    msgs = (
        Message.query
        .filter_by(conversation_id=conversation_id)
        .order_by(Message.sent_at)
        .all()
    )

    return jsonify([
        {
            "sender_id": m.sender_id,
            "type": m.type,
            "content": (
                json.loads(m.content)
                if m.type in ["image", "file"]
                else m.content
            ),
            "sent_at": m.sent_at.isoformat()
        }
        for m in msgs
    ])



@app.route("/api/conversations/private", methods=["POST"])
def get_or_create_private_conversation():
    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401

    data = request.json
    user_a = data.get("user_a")
    user_b = data.get("user_b")

    if not user_a or not user_b:
        return jsonify({"error": "missing users"}), 400

    # 🔎 TÌM conversation private có đúng 2 user này
    convo = (
        Conversation.query
        .join(Participant)
        .filter(
            Conversation.type == "private",
            Participant.user_id.in_([user_a, user_b])
        )
        .group_by(Conversation.conversation_id)
        .having(func.count(Participant.user_id) == 2)
        .first()
    )

    # ❌ CHƯA CÓ → TẠO MỚI
    if not convo:
        convo = Conversation(type="private")
        db.session.add(convo)
        db.session.flush()  # lấy conversation_id ngay

        db.session.add_all([
            Participant(conversation_id=convo.conversation_id, user_id=user_a),
            Participant(conversation_id=convo.conversation_id, user_id=user_b),
        ])

        db.session.commit()

    return jsonify({
        "conversation_id": convo.conversation_id
    })





if __name__ == "__main__":
    from __init__ import socketio
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
