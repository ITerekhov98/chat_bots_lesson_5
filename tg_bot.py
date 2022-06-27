from functools import partial
from urllib import response

import redis
from environs import Env
from enum import Enum
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, \
    Filters, ConversationHandler, RegexHandler, CallbackQueryHandler
from functools import partial
from main import get_all_products, get_access_token, get_product_by_id, get_photo_by_id


def start(update, context, cms_token):
    keyboard = []
    greeting = 'Хочешь рыбы?'
    products_info = get_all_products(cms_token)
    for product in products_info['data']:
        keyboard.append([InlineKeyboardButton(product['name'], callback_data=product['id'])])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text=greeting,
        reply_markup=reply_markup
    )
    return 'HANDLE_MENU'


def handle_menu(update, context, cms_token):
    query = update.callback_query
    query.answer()
    product_info = get_product_by_id(cms_token, query.data)['data']
    photo = get_photo_by_id(cms_token, product_info['relationships']['main_image']['data']['id'])
    response_to_user = f"{product_info['name']}\r\n{product_info['meta']['display_price']['with_tax']['formatted']} per kg \r\n {product_info['description']}"
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo, caption=response_to_user)
    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=query.message.message_id)
    return 'START'


def handle_users_reply(update, context, redis_db, cms_token=None):
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = redis_db.get(chat_id)
    
    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context, cms_token)
        redis_db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def main():
    env = Env()
    env.read_env()
    redis_db = redis.StrictRedis(
        host=env.str('REDIS_HOST'),
        port=env.int('REDIS_PORT'),
        password=env.str('REDIS_PASSWORD'),
        charset="utf-8",
        decode_responses=True
    )
    client_id = env.str('ELASTIC_PATH_CLIENT_ID')
    client_secret = env.str('ELASTIC_PATH_CLIENT_SECRET')
    cms_token = get_access_token(client_id, client_secret)

    updater = Updater(env.str('TG_BOT_TOKEN'))
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(partial(handle_users_reply, redis_db=redis_db, cms_token=cms_token)))
    dispatcher.add_handler(CommandHandler('start', partial(handle_users_reply, redis_db=redis_db, cms_token=cms_token)))
    dispatcher.add_handler(CallbackQueryHandler(partial(handle_users_reply, redis_db=redis_db)))
    dispatcher.add_handler(MessageHandler(Filters.text, partial(handle_users_reply, redis_db=redis_db)))

    updater.start_polling()


if __name__ == '__main__':
    main()