import telebot
from telebot import types
import threading
from flask import Flask
import os
import subprocess

MAIN_BOT_TOKEN = "8902367212:AAEU8M5nnVPvnk30SkJk1iioMMhbX9_Gooc"
bot = telebot.TeleBot(MAIN_BOT_TOKEN)
app = Flask(__name__)

# កន្លែងផ្ទុកទិន្នន័យបណ្តោះអាសន្ន (Memory)
user_states = {} # សម្រាប់តាមដានថា User កំពុង Host ឬ Edit
running_processes = {} # ផ្ទុក Subprocess របស់ Bot នីមួយៗ
hosted_files = {} # ផ្ទុកទីតាំង File ដែលបាន Upload

# បង្កើតថតសម្រាប់ផ្ទុកកូដដែលគេ Upload
if not os.path.exists('hosted_bots_dir'):
    os.makedirs('hosted_bots_dir')

# មុខងារបង្កើត Main Menu Keyboard
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🚀 Host Bot"),
        types.KeyboardButton("📊 Status"),
        types.KeyboardButton("💎 Plan Host Bot"),
        types.KeyboardButton("☎️ Support")
    )
    return markup

# ពេលចុច /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "សួស្តី! សូមស្វាគមន៍មកកាន់ប្រព័ន្ធ Hosting Bot 🤖", reply_markup=main_menu())

# គ្រប់គ្រងពេល User ចុចប៊ូតុងនៅលើ Keyboard
@bot.message_handler(func=lambda message: message.text in ["🚀 Host Bot", "📊 Status", "💎 Plan Host Bot", "☎️ Support"])
def handle_menu(message):
    chat_id = message.chat.id
    text = message.text

    if text == "💎 Plan Host Bot":
        # បង្កើត Inline Button សម្រាប់ Owner
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("👨‍💻 Owner", url="https://t.me/gito_kanxo"))
        
        plan_text = (
            "📋 **តារាងតម្លៃ Hosting Bot:**\n\n"
            "🔹 Hosting 1 bot = 1.25$\n"
            "🔹 Hosting 5 bots = 4.50$\n"
            "🔹 Hosting 10 bots = 8$\n\n"
            "សូមទាក់ទង Owner ដើម្បីទិញកញ្ចប់ ⬇️"
        )
        bot.send_message(chat_id, plan_text, reply_markup=markup, parse_mode='Markdown')

    elif text == "☎️ Support":
        bot.send_message(chat_id, "សម្រាប់ការគាំទ្រ និងជំនួយ សូមទាក់ទងមកកាន់ @gito_kanxo អរគុណ!")

    elif text == "🚀 Host Bot":
        user_states[chat_id] = "waiting_for_host_file"
        bot.send_message(chat_id, "📂 សូមផ្ញើ File កូដ Bot របស់អ្នក (`.py`) មកកាន់ខ្ញុំ ដើម្បីធ្វើការ Hosting។", parse_mode='Markdown')

    elif text == "📊 Status":
        if chat_id in running_processes or chat_id in hosted_files:
            markup = types.InlineKeyboardMarkup(row_width=2)
            # ប៊ូតុង Start, Stop, Edit
            btn_start = types.InlineKeyboardButton("▶️ Start", callback_data="start_bot")
            btn_stop = types.InlineKeyboardButton("⏹ Stop", callback_data="stop_bot")
            btn_edit = types.InlineKeyboardButton("✏️ Edit", callback_data="edit_bot")
            markup.add(btn_start, btn_stop, btn_edit)
            
            status_text = "🟢 កំពុងដំណើរការ" if chat_id in running_processes else "🔴 បានបញ្ឈប់"
            bot.send_message(chat_id, f"📊 **ស្ថានភាព Bot របស់អ្នក:**\nស្ថានភាព: {status_text}", reply_markup=markup, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "⚠️ អ្នកមិនទាន់មាន Bot កំពុង Host នៅឡើយទេ។ សូមចុច 🚀 Host Bot។")

# គ្រប់គ្រងពេល User Upload File (.py)
@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    if state in ["waiting_for_host_file", "waiting_for_edit_file"]:
        try:
            # ពិនិត្យមើលថាតើវាជា file Python ដែរឬទេ
            file_name = message.document.file_name
            if not file_name.endswith('.py'):
                bot.reply_to(message, "❌ សូមផ្ញើតែ File ដែលមានកន្ទុយ `.py` ប៉ុណ្ណោះ!")
                return

            bot.reply_to(message, "⏳ កំពុងពិនិត្យ និងទាញយក File របស់អ្នក...")
            
            # ទាញយក File
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # រក្សាទុក File ចូលក្នុង Server
            save_path = f"hosted_bots_dir/{chat_id}_{file_name}"
            with open(save_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            hosted_files[chat_id] = save_path
            
            # បើកំពុង Edit ត្រូវ Stop Bot ចាស់សិន
            if state == "waiting_for_edit_file" and chat_id in running_processes:
                running_processes[chat_id].terminate()
                del running_processes[chat_id]
            
            # រត់ (Run) File កូដថ្មីដោយប្រើ Subprocess
            process = subprocess.Popen(['python', save_path])
            running_processes[chat_id] = process
            
            user_states[chat_id] = None # លុប State ចោលវិញ
            
            bot.send_message(chat_id, "✅ File ត្រូវបាន Upload និងដំណើរការដោយជោគជ័យ! ចុច 📊 Status ដើម្បីគ្រប់គ្រងវា។")
            
        except Exception as e:
            bot.reply_to(message, f"❌ មានបញ្ហាក្នុងការ Upload/Run: {str(e)}")
    else:
        bot.reply_to(message, "តើអ្នកចង់ធ្វើអ្វី? សូមចុចប៊ូតុងនៅលើ Menu សិន។")

# គ្រប់គ្រង Inline Buttons (Start, Stop, Edit)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if call.data == "stop_bot":
        if chat_id in running_processes:
            running_processes[chat_id].terminate()
            del running_processes[chat_id]
            bot.answer_callback_query(call.id, "✅ Bot ត្រូវបានបញ្ឈប់!")
            bot.edit_message_text("🔴 Bot របស់អ្នកត្រូវបានបញ្ឈប់។", chat_id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "⚠️ Bot មិនកំពុងដំណើរការទេ។", show_alert=True)
            
    elif call.data == "start_bot":
        if chat_id not in running_processes and chat_id in hosted_files:
            file_path = hosted_files[chat_id]
            process = subprocess.Popen(['python', file_path])
            running_processes[chat_id] = process
            bot.answer_callback_query(call.id, "✅ Bot ចាប់ផ្តើមដំណើរការវិញហើយ!")
            bot.edit_message_text("🟢 Bot របស់អ្នកកំពុងដំណើរការឡើងវិញ។", chat_id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "⚠️ Bot កំពុងដំណើរការស្រាប់ ឬគ្មាន File ទេ។", show_alert=True)
            
    elif call.data == "edit_bot":
        user_states[chat_id] = "waiting_for_edit_file"
        bot.answer_callback_query(call.id, "ត្រៀម Edit Bot")
        bot.send_message(chat_id, "✏️ សូមផ្ញើ File កូដ (`.py`) ថ្មីរបស់អ្នកមកកាន់ខ្ញុំ ដើម្បីធ្វើការជំនួស (Auto Replace & Restart)។")

# Web Route សម្រាប់ Render ធ្វើការ Health Check
@app.route('/')
def index():
    return "Pro Hosting Bot is Running!"

def run_main_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_main_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
