from flask import Flask
app = Flask(__name__)

import payments
app.register_blueprint(payments.bp)

@app.route('/')
def hello_world():
    return 'CryptoJab'


if __name__ == '__main__':
    app.run()