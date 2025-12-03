from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_mail import Mail, Message
from models import *
from dao import *
from datetime import datetime, timedelta
import random

from __init__ import app

mail = Mail(app)

# ---------------- Đăng ký ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']
        birthdate = request.form['birthdate']
        avatar = request.form['avatar']
        email = request.form['email']

        if not all([phone, username, password, birthdate, email]):
            flash("Vui lòng điền đầy đủ thông tin!")
            return redirect(url_for("register"))

        if get_user_by_phone(phone):
            flash("Số điện thoại đã được đăng ký!")
            return redirect(url_for("register"))
        if get_user_by_email(email):
            flash("Email đã được đăng ký!")
            return redirect(url_for("register"))

        # Sinh OTP
        otp = random.randint(100000, 999999)
        otp_expire = datetime.now() + timedelta(minutes=5)  # OTP chỉ có hiệu lực 5 phút

        session['otp'] = otp
        session['otp_expire'] = otp_expire.strftime("%Y-%m-%d %H:%M:%S")
        session['reg_data'] = {
            'phone': phone,
            'username': username,
            'password': password,
            'birthdate': birthdate,
            'avatar': avatar,
            'email': email
        }

        # Gửi OTP qua Gmail
        try:
            msg = Message("OTP Xác thực đăng ký", recipients=[email])
            msg.body = f"Mã OTP của bạn là: {otp}. Hết hạn sau 5 phút."
            mail.send(msg)
            flash("OTP đã được gửi tới email của bạn!")
            return redirect(url_for("verify_otp"))
        except Exception as e:
            print(e)
            flash("Gửi email thất bại, vui lòng thử lại.")
            return redirect(url_for("register"))

    return render_template("register.html")


# ---------------- Xác thực OTP ----------------
@app.route("/verify-otp", methods=["GET", "POST"])
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
                data['avatar'],
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
            return redirect(url_for("dashboard"))
        else:
            flash("Số điện thoại hoặc mật khẩu không đúng.")
            return redirect(url_for("login"))
    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)