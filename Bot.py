import telebot
import threading
from flask import Flask
import os

# ១. ដាក់ Token របស់ Main Bot របស់អ្នកនៅទីនេះដោយផ្ទាល់
MAIN_BOT_TOKEN = "8902367212:AAEU8M5nnVPvnk30SkJk1iioMMhbX9_Gooc"

# ចាប់ផ្តើម Main Bot និង Web Server
main_bot = telebot.TeleBot(MAIN_BOT_TOKEN)
app = Flask(__name__)

# កន្លែងផ្ទុក Bots ដែលកំពុងដំណើរការ (ក្នុង Memory)
hosted_bots = {}

# អនុគមន៍សម្រាប់ដំណើរការ Child Bot នីមួយៗ
def run_child_bot(token):
    try:
        child_bot = telebot.TeleBot(token)
        
        @child_bot.message_handler(commands=['start'])
        def start_msg(message):
            child_bot.reply_to(message, "សួស្តី! ខ្ញុំគឺជា Bot ដែលកំពុងត្រូវបាន Host ដោយស្វ័យប្រវត្តិនៅលើ Render។ 🚀")
            
        @child_bot.message_handler(func=lambda m: True)
        def echo_all(message):
            child_bot.reply_to(message, f"អ្នកបានផ្ញើថា: {message.text}")
            
        print(f"✅ កំពុងដំណើរការ Bot: {token[:10]}...")
        child_bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ Error hosting bot {token}: {e}")

# បញ្ជា /start សម្រាប់ Main Bot
@main_bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "សួស្តី! ខ្ញុំគឺជា Hosting Bot 🤖\n\n"
        "សូមផ្ញើ Token របស់អ្នកមកកាន់ខ្ញុំតាមទម្រង់ខាងក្រោម ដើម្បីឲ្យខ្ញុំ Host វា៖\n"
        "`/host <BOT_TOKEN_របស់អ្នក>`"
    )
    main_bot.reply_to(message, text, parse_mode='Markdown')

# បញ្ជា /host សម្រាប់ទទួលយក Token ថ្មីពីអ្នកប្រើប្រាស់
@main_bot.message_handler(commands=['host'])
def host_new_bot(message):
    try:
        # ទាញយក Token ពីសារដែលគេផ្ញើមក
        token = message.text.split()[1]
        
        # ឆែកមើលថាតើ Token នេះកំពុងដើរស្រាប់ឬអត់
        if token in hosted_bots:
            main_bot.reply_to(message, "⚠️ Bot នេះកំពុងដំណើរការរួចហើយ!")
            return
        
        # បង្កើត Thread ថ្មីដើម្បីឲ្យ Bot នេះដំណើរការ
        thread = threading.Thread(target=run_child_bot, args=(token,))
        thread.start()
        
        # រក្សាទុកក្នុងបញ្ជី
        hosted_bots[token] = thread
        
        main_bot.reply_to(message, "✅ Bot របស់អ្នកកំពុងដំណើរការដោយជោគជ័យ! សូមចូលទៅកាន់ Bot របស់អ្នកហើយចុច /start។")
    except IndexError:
        main_bot.reply_to(message, "❌ សូមប្រើទម្រង់បញ្ជាអោយបានត្រឹមត្រូវ៖\n`/host <BOT_TOKEN_របស់អ្នក>`", parse_mode='Markdown')
    except Exception as e:
        main_bot.reply_to(message, f"❌ មានបញ្ហា៖ {str(e)}")

# Web Route សម្រាប់ Render ធ្វើការ Health Check (កុំឲ្យ Render បិទ Server)
@app.route('/')
def index():
    return "Hosting Bot is Running Perfectly with Hardcoded Token!"

# អនុគមន៍សម្រាប់ដំណើរការ Main Bot
def run_main_bot():
    print("🤖 Main Bot កំពុងដំណើរការ...")
    main_bot.polling(none_stop=True)

if __name__ == "__main__":
    # ដំណើរការ Main Bot នៅក្នុង Background Thread
    threading.Thread(target=run_main_bot).start()
    
    # ដំណើរការ Flask Web Server សម្រាប់ Render (ប្រើ Port 5000 ឬ Port របស់ Render)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
