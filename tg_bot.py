from functools import partial
from urllib import response

import redis
from environs import Env
from enum import Enum
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, \
    Filters, ConversationHandler, RegexHandler, CallbackQueryHandler
from functools import partial
from main import get_all_products, get_access_token, get_product_by_id, get_photo_by_id, add_product_to_cart, get_cart_items, get_cart, remove_product_from_cart


def get_menu_keyboard(cms_token):
    keyboard = []
    products_info = get_all_products(cms_token)
    for product in products_info['data']:
        keyboard.append([InlineKeyboardButton(product['name'], callback_data=product['id'])])
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def send_user_cart(update, context, cms_token):
    keyboard = []
    text = ''
    cart_items = get_cart_items(cms_token, update.effective_chat.id)
    product_template = '{}\r\n{}\r\n{} per kg\r\n{}kg in cart for{}\r\n\r\n'
    for product in cart_items['data']:
        text += product_template.format(
            product['name'],
            product['description'],
            product['meta']['display_price']['with_tax']['unit']['formatted'],
            product['quantity'],
            product['meta']['display_price']['with_tax']['value']['formatted']
        )
        keyboard.append([InlineKeyboardButton(f" Удалить {product['name']}", callback_data=product['id'])])
    cart_info = get_cart(cms_token, update.effective_chat.id)['data']
    text += f"Total: {cart_info['meta']['display_price']['with_tax']['formatted']}"

    keyboard.append([InlineKeyboardButton('В меню', callback_data='menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup     
    )
    return 'HANDLE_CART'


def start(update, context, cms_token):
    greeting = 'Хочешь рыбы?'
    reply_markup = get_menu_keyboard(cms_token)
    update.message.reply_text(
        text=greeting,
        reply_markup=reply_markup
    )
    return 'HANDLE_MENU'


def handle_cart(update, context, cms_token):
    query = update.callback_query
    query.answer()
    if query.data == 'menu':
        greeting = 'Хочешь рыбы?'
        reply_markup = get_menu_keyboard(cms_token)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=greeting,
            reply_markup=reply_markup
        )  
        return 'HANDLE_MENU'
    else:
        product_id = query.data
        remove_product_from_cart(cms_token, update.effective_chat.id, product_id)
        return send_user_cart(update, context, cms_token)


def handle_menu(update, context, cms_token):
    query = update.callback_query
    query.answer()
    if query.data == 'cart':
        return send_user_cart(update, context, cms_token)

    keyboard = [
        [
            InlineKeyboardButton('1кг', callback_data=f'{query.data}, 1'),
            InlineKeyboardButton('5кг', callback_data=f'{query.data}, 5'),
            InlineKeyboardButton('10кг', callback_data=f'{query.data}, 10')
        ],
        [InlineKeyboardButton('Назад', callback_data='back_to_menu')],
        [InlineKeyboardButton('Корзина', callback_data='cart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    product_info = get_product_by_id(cms_token, query.data)['data']
    photo = get_photo_by_id(cms_token, product_info['relationships']['main_image']['data']['id'])
    response_to_user = f"{product_info['name']}\r\n{product_info['meta']['display_price']['with_tax']['formatted']} per kg \r\n {product_info['description']}"
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo, caption=response_to_user, reply_markup=reply_markup)
    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=query.message.message_id)
    return 'HANDLE_DESCRIPTION'

def handle_description(update, context, cms_token):
    query = update.callback_query
    query.answer()
    if query.data == 'back_to_menu':
        greeting = 'Хочешь рыбы?'
        reply_markup = get_menu_keyboard(cms_token)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=greeting,
            reply_markup=reply_markup            
        )
        return 'HANDLE_MENU'
    elif query.data == 'cart':
        return send_user_cart(update, context, cms_token)
    else:
        product_id, quantity = query.data.split(', ') 
        add_product_to_cart(cms_token, update.effective_chat.id, product_id, int(quantity))
    return 'HANDLE_DESCRIPTION'


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
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart
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