from flask import Flask

from WebsiteTroChuyen import app


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__=="__main__":
    with app.app_context():
        app.run(debug=True, port=5000)
