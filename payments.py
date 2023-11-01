from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


from flask import (
    Blueprint, request, jsonify
)

from db import Database

bp = Blueprint('payments', __name__, url_prefix='/payments')

@bp.route('/stripe/webhook', methods=['GET'])
def stripe_webhook():
    db = Database()
    print(db)









    db.close()
    return jsonify({'message': 'Stripe Webhook'})

@bp.route('/coinbase/webhook', methods=['GET'])
def coinbase_webhook():
    db = Database()
    print(db)





    db.close()
    return jsonify({'message': 'Coinbase Webhook'})