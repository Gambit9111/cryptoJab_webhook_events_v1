from datetime import datetime, timedelta
from telebot import types, TeleBot
import stripe

from flask import (
    Blueprint, request, jsonify
)

from db import Database

import os
from dotenv import load_dotenv
load_dotenv()

# Stripe
stripe.api_key = os.getenv('STRIPE_API_KEY')
STRIPE_ENDPOINT_SECRET = os.getenv('STRIPE_ENDPOINT_SECRET')

# Telegram
TELEGRAM_BOT_API_TOKEN = os.getenv("TELEGRAM_BOT_API_KEY")
bot = TeleBot(TELEGRAM_BOT_API_TOKEN, num_threads=4, parse_mode="HTML")

# register the payments blueprint
bp = Blueprint('payments', __name__, url_prefix='/payments')

@bp.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():

    # ? Stripe stuff to get the event
    event = None
    payload = request.data
    sig_header = request.headers('STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_ENDPOINT_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e
    
    # ! Handle 2 types of events, 'invoice.payment_succeeded' and 'invoice.payment_failed'

    match event['type']:
        case 'invoice.payment_succeeded':
            invoice_payment = event['data']['object']
            print(invoice_payment)




    return jsonify({'message': 'Stripe Webhook'})

@bp.route('/coinbase/webhook', methods=['GET'])
def coinbase_webhook():
    db = Database()
    print(db)





    db.close()
    return jsonify({'message': 'Coinbase Webhook'})