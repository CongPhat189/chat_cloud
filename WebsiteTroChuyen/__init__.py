from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://admin:Chatapp123@chatdb.c5paaorryc4g.us-east-1.rds.amazonaws.com:3306/chatdb"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db=SQLAlchemy(app=app)