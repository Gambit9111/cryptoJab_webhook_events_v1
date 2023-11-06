from datetime import datetime, timedelta
import json

from telebot import types, TeleBot

import stripe

from coinbase_commerce.webhook import Webhook
from coinbase_commerce.error import SignatureVerificationError, WebhookInvalidPayload

from flask import (
    Blueprint, request, jsonify
)


# import scripts
from db import Database

# Load variables
import os
from dotenv import load_dotenv
load_dotenv()

# *Stripe
stripe.api_key = os.getenv('STRIPE_API_KEY')
STRIPE_ENDPOINT_SECRET = os.getenv('STRIPE_ENDPOINT_SECRET')

# *Coinbase
COINBASE_ENDPOINT_SECRET = os.getenv('COINBASE_ENDPOINT_SECRET')

# *Telegram
TELEGRAM_BOT_API_TOKEN = os.getenv("TELEGRAM_BOT_API_KEY")
bot = TeleBot(TELEGRAM_BOT_API_TOKEN, num_threads=4, parse_mode="HTML")

# register the payments blueprint with flask app
bp = Blueprint('payments', __name__, url_prefix='/payments')


# ! stripe webhook
@bp.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():

    # ? stripe stuff
    event = None
    payload = request.data

    try:
        event = json.loads(payload)
    except json.decoder.JSONDecodeError as e:
        print('⚠️  Webhook error while parsing basic request.' + str(e))
        return jsonify(success=False)

    if STRIPE_ENDPOINT_SECRET:
        # Only verify the event if there is an endpoint secret defined
        # Otherwise use the basic event deserialized with json
        sig_header = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_ENDPOINT_SECRET
            )
        except stripe.error.SignatureVerificationError as e:
            print('⚠️  Webhook signature verification failed.' + str(e))
            return jsonify(success=False)
    

    # ? Handle our events
    if event and event['type'] == 'invoice.payment_succeeded':
        invoice_payment = event['data']['object']
        print(invoice_payment)

    else:
        # Unexpected event type
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)




# ! coinbase webhook
@bp.route('/coinbase/webhook', methods=['POST'])
def coinbase_webhook():

    # coinbase stuff
    request_data = request.data.decode('utf-8')
    # webhook signature verification
    request_sig = request.headers.get('X-CC-Webhook-Signature', None)

    try:
        # signature verification and event object construction
        event = Webhook.construct_event(request_data, request_sig, COINBASE_ENDPOINT_SECRET)
    except (WebhookInvalidPayload, SignatureVerificationError) as e:
        return str(e), 400

    print("Received event: id={id}, type={type}".format(id=event.id, type=event.type))
    # print(event["data"]["description"])

    # # event once the payment is confirmed

    if event.type == 'charge:confirmed':
        print(event["data"])
        telegram_id = event["data"]["description"]
        print(telegram_id, "telegram_id just bought a sub")

    return 'success', 200