from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key='KJHKHJKYGJYGBJNMK@^*&$^*#@!#*(>?<'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://admin:Chatapp123@chatdb.c5paaorryc4g.us-east-1.rds.amazonaws.com:3306/chatdb"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db=SQLAlchemy(app=app)


app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "tpn18092004@gmail.com"
app.config['MAIL_PASSWORD'] = "umbpwzggmchajxtc"
app.config['MAIL_DEFAULT_SENDER'] = "tpn18092004@gmail.com"


