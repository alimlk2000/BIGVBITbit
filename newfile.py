import telebot
from telebot import types
import json
import os
import requests

# ---------------- تنظیمات ----------------

TOKEN = "8888586418:AAGE3PHQRBVu2kN_Ngo19MCwnWZ19kmTRHk"

ADMIN_ID = 7573910509

HOTWATCHER_API = " B5A92921FD1848FC3F1E297EFF3E18C0"

bot = telebot.TeleBot(TOKEN)

DB_FILE = "users.json"

# ---------------- دیتابیس ----------------

if not os.path.exists(DB_FILE):

    with open(DB_FILE, "w") as f:
        json.dump({}, f)

def load_users():

    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_users(data):

    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# ---------------- منو ----------------

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

# ---------------- استارت ----------------

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

# ---------------- تایید کاربر ----------------

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

# ---------------- موجودی ----------------

@bot.message_handler(func=lambda m: m.text == "💰 موجودی من")
def balance(message):

    users = load_users()

    user_id = str(message.from_user.id)

    balance = users[user_id]["balance"]

    bot.send_message(
        message.chat.id,
        f"💰 موجودی شما: {balance} تومان"
    )

# ---------------- خرید ووچر ----------------

@bot.message_handler(func=lambda m: m.text == "🛒 خرید ووچر")
def buy(message):

    msg = bot.send_message(
        message.chat.id,
        "مبلغ ووچر را وارد کنید"
    )

    bot.register_next_step_handler(
        msg,
        process_buy
    )

def process_buy(message):

    try:

        amount = int(message.text)

        users = load_users()

        user_id = str(message.from_user.id)

        balance = users[user_id]["balance"]

        if balance < amount:

            bot.send_message(
                message.chat.id,
                "❌ موجودی کافی نیست"
            )

            return

        headers = {
            "Authorization": f"Bearer {HOTWATCHER_API}"
        }

        data = {
            "amount": amount
        }

        response = requests.post(
            "https://hotvoucher.com/api/buy",
            headers=headers,
            json=data
        )

        result = response.json()

        if result.get("success"):

            voucher = result["voucher"]

            users[user_id]["balance"] -= amount

            save_users(users)

            bot.send_message(
                message.chat.id,
                f"✅ ووچر خریداری شد\n\n🎫 کد:\n{voucher}"
            )

        else:

            bot.send_message(
                message.chat.id,
                "❌ خطا در خرید ووچر"
            )

    except:

        bot.send_message(
            message.chat.id,
            "❌ مبلغ اشتباه است"
        )

# ---------------- کاربران ----------------

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

# ---------------- شارژ کاربر ----------------

@bot.message_handler(func=lambda m: m.text == "💳 شارژ کاربر")
def charge_user(message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(
        message.chat.id,
        "آیدی و مبلغ را بفرست\n\nمثال:\n123456789 500"
    )

    bot.register_next_step_handler(
        msg,
        process_charge
    )

def process_charge(message):

    try:

        users = load_users()

        data = message.text.split()

        user_id = data[0]

        amount = int(data[1])

        if user_id not in users:

            bot.send_message(
                message.chat.id,
                "❌ کاربر پیدا نشد"
            )

            return

        users[user_id]["balance"] += amount

        save_users(users)

        bot.send_message(
            message.chat.id,
            "✅ کیف پول شارژ شد"
        )

        bot.send_message(
            int(user_id),
            f"💰 کیف پول شما {amount} تومان شارژ شد"
        )

    except:

        bot.send_message(
            message.chat.id,
            "❌ فرمت اشتباه است"
        )

print("BOT IS RUNNING...")

bot.infinity_polling(skip_pending=True)
