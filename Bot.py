import telebot
from telebot import types
import sqlite3

TOKEN = "8902367212:AAEU8M5nnVPvnk30SkJk1iioMMhbX9_Gooc"

ADMIN_IDS = [
    7820849894
]

bot = telebot.TeleBot(TOKEN)

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    plan INTEGER DEFAULT 0
)
""")

conn.commit()

# =========================
# FUNCTIONS
# =========================

def register_user(user):

    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id, username, first_name)
        VALUES (?, ?, ?)
        """,
        (
            user.id,
            user.username,
            user.first_name
        )
    )

    conn.commit()


def get_plan(user_id):

    cursor.execute(
        "SELECT plan FROM users WHERE user_id=?",
        (user_id,)
    )

    data = cursor.fetchone()

    if data:
        return data[0]

    return 0


def set_plan(user_id, amount):

    cursor.execute(
        """
        UPDATE users
        SET plan=?
        WHERE user_id=?
        """,
        (
            amount,
            user_id
        )
    )

    conn.commit()


def menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(
        "💰 Balance",
        "💎 My Plan"
    )

    markup.add(
        "📊 Statistics"
    )

    return markup


# =========================
# START
# =========================

@bot.message_handler(commands=['start'])
def start(message):

    register_user(message.from_user)

    text = f"""
👋 Welcome {message.from_user.first_name}

🤖 Plan Manager Bot

សូមជ្រើសរើស Menu ខាងក្រោម
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=menu()
    )


# =========================
# BALANCE
# =========================

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):

    plan = get_plan(
        message.from_user.id
    )

    text = f"""
👤 Name : {message.from_user.first_name}

🆔 ID : {message.from_user.id}

💎 Plan : {plan}
"""

    bot.send_message(
        message.chat.id,
        text
    )


# =========================
# MY PLAN
# =========================

@bot.message_handler(func=lambda m: m.text == "💎 My Plan")
def myplan(message):

    plan = get_plan(
        message.from_user.id
    )

    if plan <= 0:

        bot.send_message(
            message.chat.id,
            "❌ You don't have any plan."
        )

        return

    bot.send_message(
        message.chat.id,
        f"✅ Your Plan = {plan}"
    )


# =========================
# STATS
# =========================

@bot.message_handler(func=lambda m: m.text == "📊 Statistics")
def stats(message):

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = cursor.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"👥 Total Users : {total_users}"
    )


# =========================
# ADMIN ADD PLAN
# =========================

@bot.message_handler(commands=['addplan'])
def addplan(message):

    if message.from_user.id not in ADMIN_IDS:

        bot.reply_to(
            message,
            "❌ Admin Only"
        )

        return

    try:

        args = message.text.split()

        if len(args) != 3:

            bot.reply_to(
                message,
                """
Usage:

/addplan USER_ID AMOUNT

Example:

/addplan 123456789 5
"""
            )

            return

        user_id = int(args[1])
        amount = int(args[2])

        current = get_plan(
            user_id
        )

        new_plan = current + amount

        set_plan(
            user_id,
            new_plan
        )

        bot.reply_to(
            message,
            f"""
✅ Plan Added

👤 User : {user_id}

💎 Added : {amount}

📦 Total : {new_plan}
"""
        )

        try:

            bot.send_message(
                user_id,
                f"""
🎉 Admin Added Plan

💎 Added : {amount}

📦 Total : {new_plan}
"""
            )

        except:
            pass

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Error\n{e}"
        )


# =========================
# ADMIN REMOVE PLAN
# =========================

@bot.message_handler(commands=['removeplan'])
def removeplan(message):

    if message.from_user.id not in ADMIN_IDS:
        return

    try:

        args = message.text.split()

        if len(args) != 3:
            return

        user_id = int(args[1])
        amount = int(args[2])

        current = get_plan(user_id)

        new_plan = max(
            0,
            current - amount
        )

        set_plan(
            user_id,
            new_plan
        )

        bot.reply_to(
            message,
            f"""
✅ Plan Removed

👤 User : {user_id}

💎 Total : {new_plan}
"""
        )

    except Exception as e:

        bot.reply_to(
            message,
            str(e)
        )


# =========================
# ADMIN USERS
# =========================

@bot.message_handler(commands=['users'])
def users(message):

    if message.from_user.id not in ADMIN_IDS:
        return

    cursor.execute(
        """
        SELECT
        user_id,
        first_name,
        username,
        plan
        FROM users
        """
    )

    rows = cursor.fetchall()

    if not rows:

        bot.send_message(
            message.chat.id,
            "No Users"
        )

        return

    text = "👥 USERS LIST\n\n"

    for row in rows:

        user_id = row[0]
        name = row[1]
        username = row[2]
        plan = row[3]

        text += f"""
👤 {name}

🆔 {user_id}

📛 @{username}

💎 {plan}

----------------
"""

    if len(text) > 4000:
        text = text[:4000]

    bot.send_message(
        message.chat.id,
        text
    )


# =========================
# ADMIN PLANS
# =========================

@bot.message_handler(commands=['plans'])
def plans(message):

    if message.from_user.id not in ADMIN_IDS:
        return

    cursor.execute(
        """
        SELECT
        COUNT(*)
        FROM users
        WHERE plan > 0
        """
    )

    total = cursor.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"💎 Users With Plan : {total}"
    )


# =========================
# RUN BOT
# =========================

print("Bot Running...")

bot.infinity_polling()
