import telebot
from telebot import types
import json
import os

TOKEN = "8888586418:AAGE3PHQRBVu2kN_Ngo19MCwnWZ19kmTRHk"

ADMIN_ID = 7573910509

bot = telebot.TeleBot(TOKEN)

DB_FILE = "users.json"

# ساخت فایل دیتابیس
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

# خواندن کاربران
def load_users():
    with open(DB_FILE, "r") as f:
        return json.load(f)

# ذخیره کاربران
def save_users(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# منوی اصلی
def show_menu(chat_id, name, user_id):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("💰 موجودی من")
    btn2 = types.KeyboardButton("🛒 خرید ووچر")

    markup.add(btn1, btn2)

    if user_id == ADMIN_ID:
        btn3 = types.KeyboardButton("👥 کاربران")
        btn4 = types.KeyboardButton("💳 شارژ کاربر")

        markup.add(btn3, btn4)

    bot.send_message(
        chat_id,
        f"سلام {name} 👋",
        reply_markup=markup
    )

# استارت
@bot.message_handler(commands=['start'])
def start(message):

    users = load_users()

    user_id = str(message.from_user.id)
    name = message.from_user.first_name

    if user_id not in users:

        users[user_id] = {
            "name": name,
            "balance": 0,
            "approved": False
        }

        save_users(users)

        markup = types.InlineKeyboardMarkup()

        btn = types.InlineKeyboardButton(
            "✅ تایید کاربر",
            callback_data=f"approve_{user_id}"
        )

        markup.add(btn)

        bot.send_message(
            ADMIN_ID,
            f"🆕 کاربر جدید\n\n👤 {name}\n🆔 {user_id}",
            reply_markup=markup
        )

    users = load_users()

    if users[user_id]["approved"] == False:

        bot.send_message(
            message.chat.id,
            "⏳ حساب شما در انتظار تایید ادمین است"
        )

        return

    show_menu(message.chat.id, name, int(user_id))

# تایید کاربر
@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    users = load_users()

    if call.data.startswith("approve_"):

        user_id = call.data.split("_")[1]

        users[user_id]["approved"] = True

        save_users(users)

        name = users[user_id]["name"]

        bot.send_message(
            int(user_id),
            "✅ حساب شما تایید شد"
        )

        show_menu(
            int(user_id),
            name,
            int(user_id)
        )

        bot.answer_callback_query(
            call.id,
            "کاربر تایید شد ✅"
        )

# موجودی
@bot.message_handler(func=lambda m: m.text == "💰 موجودی من")
def balance(message):

    users = load_users()

    user_id = str(message.from_user.id)

    balance = users[user_id]["balance"]

    bot.send_message(
        message.chat.id,
        f"💰 موجودی شما: {balance} تومان"
    )

# خرید ووچر
@bot.message_handler(func=lambda m: m.text == "🛒 خرید ووچر")
def buy(message):

    users = load_users()

    user_id = str(message.from_user.id)

    balance = users[user_id]["balance"]

    if balance <= 0:

        bot.send_message(
            message.chat.id,
            "❌ موجودی کافی نیست"
        )

        return

    bot.send_message(
        message.chat.id,
        "🚧 اتصال API هنوز انجام نشده"
    )

# کاربران
@bot.message_handler(func=lambda m: m.text == "👥 کاربران")
def users_list(message):

    if message.from_user.id != ADMIN_ID:
        return

    users = load_users()

    text = "👥 کاربران:\n\n"

    for user_id in users:

        name = users[user_id]["name"]
        balance = users[user_id]["balance"]
        approved = users[user_id]["approved"]

        text += f"👤 {name}\n🆔 {user_id}\n💰 {balance}\n✅ تایید: {approved}\n\n"

    bot.send_message(
        message.chat.id,
        text
    )

# شارژ کاربر
@bot.message_handler(func=lambda m: m.text == "💳 شارژ کاربر")
def charge_user(message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(
        message.chat.id,
        "آیدی و مبلغ را بفرست\n\nمثال:\n123456789 500"
    )
