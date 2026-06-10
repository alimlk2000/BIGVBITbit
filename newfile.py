bot.register_next_step_handler(
        msg,
        process_charge
    )

# پردازش شارژ
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