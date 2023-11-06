from telebot import TeleBot, types
from datetime import datetime, timedelta

# Load variables
import os
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_INVITE_LINK_EXPIRATION_TIME = int(os.getenv("TELEGRAM_INVITE_LINK_EXPIRATION_TIME"))

def is_channel_member(bot: TeleBot, chat_id: int | str, user_id: int):
    chat_member = bot.get_chat_member(chat_id, user_id)
    print(chat_member)
    match chat_member.status:
        case 'member':
            return True
        case _:
            return False

def generate_invite_link(bot: TeleBot, chat_id: int | str, user_telegram_id: str, member_limit: int = 1, expire_date: int | datetime = (datetime.now() + timedelta(minutes=TELEGRAM_INVITE_LINK_EXPIRATION_TIME)).replace(microsecond=0)):

    #! kick the user from the channel before we generate a new link for him to make sure there is no duplicate links
    bot.unban_chat_member(chat_id, user_telegram_id)

    # generate a new invite link
    invite = bot.create_chat_invite_link(chat_id, name=user_telegram_id, member_limit=member_limit, expire_date=expire_date)
    # get the actual link from Invite class
    invite_link = invite.invite_link

    print("invite link generated", invite_link, "for user", user_telegram_id)
    return invite_link


# ! JOIN CHANNEL KEYBOARD
def join_channel_keyboard(invite_link: str):
    return types.InlineKeyboardMarkup(
        keyboard=[
            [
                types.InlineKeyboardButton(
                    text='🚀   ---   Join Our Group   ---   🚀',
                    url=invite_link

                )
            ]
        ]
    )