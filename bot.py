import os
import telebot
import requests
import json

# 🔑 المفاتيح
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

chat_histories = {}  # تخزين تاريخ المحادثة لكل دردشة

def get_chat_history(chat_id):
    if chat_id not in chat_histories:
        chat_histories[chat_id] = [
            {
                "role": "system",
                "content": (
                    "You are Jamal's personal assistant. "
                    "Your job is to help Jamal in everything he needs. "
                    "You never share personal information. "
                    "You help with studying, programming, and daily questions. "
                    "You are friendly, supportive, and encouraging. "
                    "You always try to make people happy and motivated."
                )
            }
        ]
    return chat_histories[chat_id]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "🤖 أهلاً! أنا مساعد جمال. كيف يمكنني مساعدتك؟"
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help', 'مساعدة'])
def send_help(message):
    help_text = """
🤖 *أوامر البوت:*
/start - بدء التشغيل
/help - عرض المساعدة

*للاستخدام في المجموعات:*
- اذكر البوت @{} في رسالتك
- أو رد على رسالة البوت
""".format(bot.get_me().username)
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    chat_history = get_chat_history(chat_id)
    
    # التحقق إذا كان في مجموعة وتم ذكر البوت
    bot_username = f"@{bot.get_me().username}"
    if message.chat.type in ["group", "supergroup"]:
        if bot_username not in message.text and not message.reply_to_message:
            return  # لا يرد إذا لم يذكر
    
    user_input = message.text.replace(bot_username, "").strip()
    
    chat_history.append({"role": "user", "content": user_input})
    
    # تقليل طول المحادثة
    if len(chat_history) > 11:
        chat_history[1:] = chat_history[-9:]
    
    try:
        reply = get_groq_response(chat_history)
        chat_history.append({"role": "assistant", "content": reply})
        bot.reply_to(message, reply)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "❌ حدث خطأ في المعالجة")

def get_groq_response(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

print("🚀 البوت شغال وجاهز للمجموعات...")
bot.infinity_polling()