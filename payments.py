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

from telegram_handler import is_channel_member, generate_invite_link, join_channel_keyboard

# Load variables
import os
from dotenv import load_dotenv
load_dotenv()

# *Telegram
TELEGRAM_BOT_API_TOKEN = os.getenv("TELEGRAM_BOT_API_KEY")
TELEGRAM_PREMIUM_CHANNEL_ID = int(os.getenv("TELEGRAM_PREMIUM_CHANNEL_ID"))
bot = TeleBot(TELEGRAM_BOT_API_TOKEN, num_threads=4, parse_mode="HTML")

# *Stripe
stripe.api_key = os.getenv('STRIPE_API_KEY')
STRIPE_ENDPOINT_SECRET = os.getenv('STRIPE_ENDPOINT_SECRET')

# *Coinbase
COINBASE_ENDPOINT_SECRET = os.getenv('COINBASE_ENDPOINT_SECRET')

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
    

    # ? Handle our events --------------
    if event and event['type'] == 'invoice.payment_succeeded':
        invoice_payment = event['data']['object']
        print("payment succeeded", invoice_payment)

        # ! get variables from invoice_payment
        user_telegram_id = invoice_payment['subscription_details']['metadata']['telegram_id']
        subscription_duration = int(invoice_payment['subscription_details']['metadata']['duration'])
        subscription_id = invoice_payment['subscription']
        user_email = invoice_payment['customer_email']
        # * calculate valid until date based on duration
        subscription_valid_until_date = datetime.now() + (datetime.now() + timedelta(days=subscription_duration)).replace(microsecond=0)

        # * connect to db
        db = Database()

        # * check if user exists in the database
        user = db.fetchone("SELECT * FROM users WHERE telegram_id = %s", (user_telegram_id, ))
        print("fetching from db", user)

        # ! if user exists, update his subscription valid until date
        # ? This is reocurring payment
        if user is not None:
            # * check if user is a member of premium channel
            is_member = is_channel_member(bot, TELEGRAM_PREMIUM_CHANNEL_ID, user_telegram_id)
            print("user reocurring ", user, "is_member ", is_member)

            if is_member == True: #? update db
                db.execute("UPDATE users SET valid_until = %s WHERE telegram_id = %s", (subscription_valid_until_date, user_telegram_id, ))
                print("User exists, subscription_valid_until_date updated")
                return jsonify(success=True)
            else:
                # ? This will fire if the user is not a member of the premium channel but he is in the database
                # !something is wrong send a message to the user saying to contact the admin
                bot.send_message(user_telegram_id, "Stripe Error code 1. Please contact the admin.")
                return jsonify(success=False)
        
        # ! if user doesn't exist, create a new user and send him the invite link
        # ? This is new payment
        elif user is None:
            # * check if user is not a member of premium channel
            is_member = is_channel_member(bot, TELEGRAM_PREMIUM_CHANNEL_ID, user_telegram_id)
            print("user new ", user, "is_member ", is_member)

            if is_member == False: #? insert new user into db
                db.execute("INSERT INTO users (telegram_id, email, payment_method, subscription_id, valid_until) VALUES (%s, %s, %s, %s, %s)", (user_telegram_id, user_email, "stripe", subscription_id, subscription_valid_until_date, ))
                print("New user created")

                # *send user invite link button
                invite_link = generate_invite_link(bot, TELEGRAM_PREMIUM_CHANNEL_ID, user_telegram_id)
                bot.send_message(user_telegram_id, "Welcome to the premium channel. Please join the channel by clicking the button below.", reply_markup=join_channel_keyboard(invite_link))
                return jsonify(success=True)
            else:
                # ? This will fire if the user is a member of the premium channel but he is not in the database
                # !something is wrong send a message to the user saying to contact the admin
                bot.send_message(user_telegram_id, "Stripe Error code 2. Please contact the admin.")
                return jsonify(success=False)


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