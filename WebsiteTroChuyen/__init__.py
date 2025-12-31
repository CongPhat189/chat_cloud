import cloudinary
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import boto3
import os
from flask_socketio import SocketIO

app = Flask(__name__, template_folder='templates')
app.secret_key = 'KJHKHJKYGJYGBJNMK@^*&$^*#@!#*(>?<'
app.config[
    'SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://admin:Chatapp123@chatdb.c5paaorryc4g.us-east-1.rds.amazonaws.com:3306/chatdb"
# app.config['SQLALCHEMY_DATABASE_URI'] = \
#     "mysql+pymysql://root:123456@127.0.0.1:3306/chatdb"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db = SQLAlchemy(app=app)

app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "tpn18092004@gmail.com"
app.config['MAIL_PASSWORD'] = "umbpwzggmchajxtc"
app.config['MAIL_DEFAULT_SENDER'] = "tpn18092004@gmail.com"

cloudinary.config(
    cloud_name="dvlwb6o7e",
    api_key="315637758944728",
    api_secret="A34d8SUWJZnBLiGAgOPEIhqRB_c",
    secure=True
)

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "chat-cloud-project")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

s3_client = boto3.client("s3", region_name=AWS_REGION)
socketio = SocketIO(app, cors_allowed_origins="*")
