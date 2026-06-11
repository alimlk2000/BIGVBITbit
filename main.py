import telebot
from telebot import types
import json
import os
import requests
import time

# ================= تنظیمات =================

TOKEN = "8888586418:AAEp5Ozd6c2R3y75X37C7BdML6gzqGtwJk8"

ADMIN_ID = 7573910509

HOTWATCHER_API = "B5A92921FD1848FC3F1E297EFF3E18C0"

bot = telebot.TeleBot(TOKEN)

DB_FILE = "users.json"

# ================= ساخت دیتابیس =================

if not os.path.exists(DB_FILE):

    with open(DB_FILE, "w") as f:
        json.dump({}, f)

# ================= خواندن کاربران =================

def load_users():

    with open(DB_FILE, "r") as f:
        return json.load(f)

# ================= ذخیره کاربران =================

def save_users(data):

    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# ================= منوی اصلی =================

def show_menu(chat_id, name, user_id):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("💰 موجودی من")
    btn2 = types.KeyboardButton("🛒 خرید ووچر")
    btn3 = types.KeyboardButton("💸 فروش ووچر")

    markup.add(btn1, btn2)
    markup.add(btn3)

    # پنل ادمین
    if user_id == ADMIN_ID:

        btn4 = types.KeyboardButton("👥 کاربران")
        btn5 = types.KeyboardButton("💳 شارژ کاربر")

        markup.add(btn4, btn5)

    bot.send_message(
        chat_id,
        f"سلام {name} 👋",
        reply_markup=markup
    )

# ================= استارت =================

@bot.message_handler(commands=['start'])
def start(message):

    users = load_users()

    user_id = str(message.from_user.id)

    name = message.from_user.first_name

    # ثبت کاربر جدید
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

    # اگر تایید نشده
    if users[user_id]["approved"] == False:

        bot.send_message(
            message.chat.id,
            "⏳ حساب شما در انتظار تایید ادمین است"
        )

        return

    show_menu(
        message.chat.id,
        name,
        int(user_id)
    )

# ================= تایید کاربر =================

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

# ================= موجودی =================

@bot.message_handler(func=lambda m: m.text == "💰 موجودی من")
def balance(message):

    users = load_users()

    user_id = str(message.from_user.id)

    balance = users[user_id]["balance"]

    bot.send_message(
        message.chat.id,
        f"💰 موجودی شما: {balance}"
    )

# ================= خرید ووچر =================

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

        amount = float(message.text)

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
            "authorization": HOTWATCHER_API,
            "Content-Type": "application/json"
        }

        data = {
            "coin": "USDT",
            "amount": str(amount)
        }

        response = requests.post(
            "https://api.uwallet.biz/v1/voucher",
            headers=headers,
            json=data
        )

        result = response.json()

        if "code" in result:

            voucher = result["code"]

            users[user_id]["balance"] -= amount

            save_users(users)

            bot.send_message(
                message.chat.id,
                f"✅ ووچر ساخته شد\n\n🎫 کد ووچر:\n{voucher}"
            )

        else:

            bot.send_message(
                message.chat.id,
                f"❌ خطا:\n{result}"
            )

    except Exception as e:

        print(e)

        bot.send_message(
            message.chat.id,
            "❌ خطا در خرید ووچر"
        )

# ================= فروش ووچر =================

@bot.message_handler(func=lambda m: m.text == "💸 فروش ووچر")
def sell_voucher(message):

    msg = bot.send_message(
        message.chat.id,
        "کد ووچر را ارسال کنید"
    )

    bot.register_next_step_handler(
        msg,
        process_sell_voucher
    )

def process_sell_voucher(message):

    try:

        code = message.text

        headers = {
            "authorization": HOTWATCHER_API,
            "Content-Type": "application/json"
        }

        data = {
            "coin": "USDT",
            "code": code
        }

        response = requests.post(
            "https://api.uwallet.biz/v1/voucher/use",
            headers=headers,
            json=data
        )

        result = response.json()

        if result.get("status") == "confirm":

            amount = float(result["receive"])

            users = load_users()

            user_id = str(message.from_user.id)

            users[user_id]["balance"] += amount

            save_users(users)

            bot.send_message(
                message.chat.id,
                f"✅ ووچر نقد شد\n\n💰 مبلغ: {amount}"
            )

        else:

            bot.send_message(
                message.chat.id,
                "❌ ووچر نامعتبر است"
            )

    except Exception as e:

        print(e)

        bot.send_message(
            message.chat.id,
            "❌ خطا در فروش ووچر"
        )

# ================= کاربران =================

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

# ================= شارژ کاربر =================

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

        amount = float(data[1])

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
            f"💰 کیف پول شما {amount} شارژ شد"
        )

    except Exception as e:

        print(e)

        bot.send_message(
            message.chat.id,
            "❌ فرمت اشتباه است"
        )

# ================= اجرای دائمی =================

print("BOT IS RUNNING...")

while True:

    try:

        bot.infinity_polling(
            skip_pending=True,
            timeout=60,
            long_polling_timeout=60
        )

    except Exception as e:

        print(e)

        time.sleep(5)
