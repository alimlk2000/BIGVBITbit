import telebot
from telebot import types
import json
import os
import requests
import time
import hashlib

# ================= تنظیمات =================

TOKEN = "8888586418:AAEp5Ozd6c2R3y75X37C7BdML6gzqGtwJk8"

ADMIN_ID = 7573910509

# ================= هات ووچر =================

HOTVOUCHER_SECURITY = "B5A92921FD1848FC3F1E297EFF3E18C0"

HOTVOUCHER_PASSWORD = "@As1380ba"

# ================= موبکش =================

MOBICASH_API_KEY = "bb45891242ffede6e08607a0898679524a62edad4b7aae5335723e6488316388"

# ================= ربات =================

bot = telebot.TeleBot(TOKEN)

DB_FILE = "users.json"

# ================= ساخت دیتابیس =================

if not os.path.exists(DB_FILE):

    with open(DB_FILE, "w") as f:

        json.dump({}, f)

# ================= خواندن دیتابیس =================

def load_users():

    with open(DB_FILE, "r") as f:

        return json.load(f)

# ================= ذخیره دیتابیس =================

def save_users(data):

    with open(DB_FILE, "w") as f:

        json.dump(data, f)

# ================= امضا =================

def generate_sha256(data):

    return hashlib.sha256(data.encode()).hexdigest()

def generate_md5(data):

    return hashlib.md5(data.encode()).hexdigest()

# ================= قفل خرید =================

BUY_LOCK = False

# ================= منو =================

def show_menu(chat_id, name, user_id):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("💰 موجودی من")
    btn2 = types.KeyboardButton("🛒 خرید ووچر")
    btn3 = types.KeyboardButton("💸 فروش ووچر")
    btn4 = types.KeyboardButton("💳 شارژ وانیکس")

    markup.add(btn1, btn2)
    markup.add(btn3, btn4)

    if user_id == ADMIN_ID:

        btn5 = types.KeyboardButton("👥 کاربران")
        btn6 = types.KeyboardButton("💳 شارژ کاربر")
        btn7 = types.KeyboardButton("🚫 مسدود کردن")
        btn8 = types.KeyboardButton("✅ رفع مسدودیت")
        btn9 = types.KeyboardButton("🧪 تست موبکش")

        markup.add(btn5, btn6)
        markup.add(btn7, btn8)
        markup.add(btn9)

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

    if user_id not in users:

        users[user_id] = {
            "name": name,
            "balance": 0,
            "approved": False,
            "blocked": False
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

    if users[user_id]["blocked"]:

        bot.send_message(
            message.chat.id,
            "⛔ حساب شما مسدود شده است"
        )

        return

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

# ================= تایید =================

@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    users = load_users()

    if call.data.startswith("approve_"):

        user_id = call.data.split("_")[1]

        users[user_id]["approved"] = True

        save_users(users)

        bot.send_message(
            int(user_id),
            "✅ حساب شما تایید شد"
        )

        bot.answer_callback_query(
            call.id,
            "کاربر تایید شد"
        )

# ================= موجودی =================

@bot.message_handler(func=lambda m: m.text == "💰 موجودی من")
def balance(message):

    users = load_users()

    user_id = str(message.from_user.id)

    balance = users[user_id]["balance"]

    bot.send_message(
        message.chat.id,
        f"💰 موجودی شما:\n\n{int(balance):,} ریال"
    )

# ================= خرید ووچر =================

@bot.message_handler(func=lambda m: m.text == "🛒 خرید ووچر")
def buy_voucher(message):

    global BUY_LOCK

    if BUY_LOCK:

        bot.send_message(
            message.chat.id,
            "⏳ در حال پردازش درخواست‌های قبلی هستیم.\nلطفاً کمی بعد دوباره تلاش کنید."
        )

        return

    msg = bot.send_message(
        message.chat.id,
        "💰 مبلغ ووچر را به ریال وارد کنید"
    )

    bot.register_next_step_handler(
        msg,
        process_buy
    )

def process_buy(message):

    global BUY_LOCK

    try:

        BUY_LOCK = True

        amount = int(message.text)

        users = load_users()

        user_id = str(message.from_user.id)

        if users[user_id]["balance"] < amount:

            BUY_LOCK = False

            bot.send_message(
                message.chat.id,
                "❌ موجودی کافی نیست"
            )

            return

        final_amount = int(amount * 0.95)

        credit_url = f"http://amitex.biz/delegateapi/credit?SecurityCode={HOTVOUCHER_SECURITY}&Password={HOTVOUCHER_PASSWORD}"

        credit_response = requests.get(credit_url).json()

        if not credit_response["IsSuccess"]:

            BUY_LOCK = False

            bot.send_message(
                message.chat.id,
                "⚠️ سرویس صدور ووچر موقتاً در دسترس نیست.\nلطفاً چند دقیقه دیگر دوباره تلاش کنید."
            )

            return

        hot_balance = int(credit_response["Data"])

        if hot_balance < final_amount:

            BUY_LOCK = False

            bot.send_message(
                message.chat.id,
                "⚠️ سرویس صدور ووچر موقتاً در دسترس نیست.\nلطفاً چند دقیقه دیگر دوباره تلاش کنید."
            )

            return

        create_url = f"http://amitex.biz/delegateapi/createhotvoucher?SecurityCode={HOTVOUCHER_SECURITY}&Password={HOTVOUCHER_PASSWORD}&HotVoucherAmount={final_amount}"

        create_response = requests.get(create_url).json()

        if not create_response["IsSuccess"]:

            BUY_LOCK = False

            bot.send_message(
                message.chat.id,
                "⚠️ سرویس صدور ووچر موقتاً در دسترس نیست.\nلطفاً چند دقیقه دیگر دوباره تلاش کنید."
            )

            return

        tracking_code = create_response["Data"]

        time.sleep(10)

        check_url = f"http://amitex.biz/delegateapi/checkhotvoucherstatus?SecurityCode={HOTVOUCHER_SECURITY}&Password={HOTVOUCHER_PASSWORD}&TrackingCode={tracking_code}"

        check_response = requests.get(check_url).json()

        if check_response["IsSuccess"]:

            voucher = check_response["Data"][0]["HotVoucher"]

            users[user_id]["balance"] -= amount

            save_users(users)

            bot.send_message(
                message.chat.id,
                f"✅ ووچر صادر شد\n\n💰 مبلغ پرداختی:\n{amount:,} ریال\n\n🎫 کد ووچر:\n\n{voucher}"
            )

        else:

            bot.send_message(
                message.chat.id,
                "⚠️ سرویس صدور ووچر موقتاً در دسترس نیست.\nلطفاً چند دقیقه دیگر دوباره تلاش کنید."
            )

        BUY_LOCK = False

    except Exception as e:

        print(e)

        BUY_LOCK = False

        bot.send_message(
            message.chat.id,
            "❌ خطا در خرید ووچر"
        )

# ================= فروش ووچر =================

@bot.message_handler(func=lambda m: m.text == "💸 فروش ووچر")
def sell_voucher(message):

    msg = bot.send_message(
        message.chat.id,
        "🎫 کد ووچر را ارسال کنید"
    )

    bot.register_next_step_handler(
        msg,
        process_sell
    )

def process_sell(message):

    try:

        voucher = message.text

        check_url = f"http://amitex.biz/delegateapi/voucherstatus?SecurityCode={HOTVOUCHER_SECURITY}&Password={HOTVOUCHER_PASSWORD}&HotVoucher={voucher}"

        response = requests.get(check_url).json()

        if response["IsSuccess"]:

            data = response["Data"]

            amount = int(data["Amount"])

            final_amount = int(amount * 0.928)

            users = load_users()

            user_id = str(message.from_user.id)

            users[user_id]["balance"] += final_amount

            save_users(users)

            bot.send_message(
                message.chat.id,
                f"✅ ووچر ثبت شد\n\n💰 مبلغ دریافتی:\n{final_amount:,} ریال"
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

# ================= شارژ وانیکس =================

@bot.message_handler(func=lambda m: m.text == "💳 شارژ وانیکس")
def vanix_charge(message):

    msg = bot.send_message(
        message.chat.id,
        "آیدی وانیکس و مبلغ را ارسال کنید\n\nمثال:\n123456 500000"
    )

    bot.register_next_step_handler(
        msg,
        process_vanix
    )

def process_vanix(message):

    try:

        data = message.text.split()

        vanix_id = data[0]

        amount = int(data[1])

        users = load_users()

        user_id = str(message.from_user.id)

        if users[user_id]["balance"] < amount:

            bot.send_message(
                message.chat.id,
                "❌ موجودی کافی نیست"
            )

            return

        url = f"https://partners.servcul.com/CashdeskBotAPI/Deposit/{vanix_id}/Add"

        headers = {
            "Authorization": MOBICASH_API_KEY
        }

        payload = {
            "summa": amount
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers
        )

        result = response.text

        if response.status_code == 200:

            users[user_id]["balance"] -= amount

            save_users(users)

            bot.send_message(
                message.chat.id,
                f"✅ درخواست شارژ ارسال شد\n\n📨 پاسخ سرور:\n{result}"
            )

        else:

            bot.send_message(
                message.chat.id,
                f"❌ خطا در اتصال موبکش\n\n{result}"
            )

    except Exception as e:

        bot.send_message(
            message.chat.id,
            str(e)
        )

# ================= کاربران =================

@bot.message_handler(func=lambda m: m.text == "👥 کاربران")
def users_list(message):

    if message.from_user.id != ADMIN_ID:
        return

    users = load_users()

    text = "👥 کاربران:\n\n"

    for uid in users:

        user = users[uid]

        text += f"👤 {user['name']}\n🆔 {uid}\n💰 {int(user['balance']):,} ریال\n\n"

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
        "آیدی و مبلغ را بفرست\n\nمثال:\n123456789 500000"
    )

    bot.register_next_step_handler(
        msg,
        process_charge
    )

def process_charge(message):

    try:

        data = message.text.split()

        user_id = data[0]

        amount = int(data[1])

        users = load_users()

        users[user_id]["balance"] += amount

        save_users(users)

        bot.send_message(
            message.chat.id,
            "✅ کیف پول شارژ شد"
        )

    except Exception as e:

        print(e)

# ================= مسدود =================

@bot.message_handler(func=lambda m: m.text == "🚫 مسدود کردن")
def block_user(message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(
        message.chat.id,
        "آیدی کاربر را ارسال کنید"
    )

    bot.register_next_step_handler(
        msg,
        process_block
    )

def process_block(message):

    users = load_users()

    user_id = message.text

    if user_id in users:

        users[user_id]["blocked"] = True

        save_users(users)

        bot.send_message(
            message.chat.id,
            "✅ کاربر مسدود شد"
        )

# ================= رفع مسدود =================

@bot.message_handler(func=lambda m: m.text == "✅ رفع مسدودیت")
def unblock_user(message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(
        message.chat.id,
        "آیدی کاربر را ارسال کنید"
    )

    bot.register_next_step_handler(
        msg,
        process_unblock
    )

def process_unblock(message):

    users = load_users()

    user_id = message.text

    if user_id in users:

        users[user_id]["blocked"] = False

        save_users(users)

        bot.send_message(
            message.chat.id,
            "✅ رفع مسدودیت شد"
        )

# ================= تست موبکش =================

@bot.message_handler(func=lambda m: m.text == "🧪 تست موبکش")
def test_mobicash(message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        url = "https://partners.servcul.com/CashdeskBotAPI/Credit"

        headers = {
            "Authorization": MOBICASH_API_KEY
        }

        response = requests.get(
            url,
            headers=headers
        )

        bot.send_message(
            message.chat.id,
            f"{response.status_code}\n\n{response.text}"
        )

    except Exception as e:

        bot.send_message(
            message.chat.id,
            str(e)
        )

# ================= اجرا =================

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
