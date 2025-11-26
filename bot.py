import os
import telebot
import requests
import json

# 🔑 جلب المفاتيح من Environment Variables
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 0))  # رقم Telegram الخاص بك
CHANNEL_ID = os.getenv('CHANNEL_ID')      # @اسم_القناة أو رقم القناة الخاص -1001234567890

# التأكد من وجود المفاتيح
if not GROQ_API_KEY or not TELEGRAM_BOT_TOKEN or not OWNER_ID or not CHANNEL_ID:
    print("❌ تأكد من تعيين جميع المتغيرات: GROQ_API_KEY, TELEGRAM_BOT_TOKEN, OWNER_ID, CHANNEL_ID")
    exit(1)
else:
    print("✅ تم تحميل المفاتيح بنجاح!")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# حفظ تاريخ المحادثة لكل دردشة على حدة
chat_histories = {}

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
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"❌ Groq API Connection Error: {e}")
        return "❌ حدث خطأ في الاتصال بالذكاء الاصطناعي"

# رسالة الترحيب
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 أهلاً جمال! البوت شغال الآن ❤️")

# الرد على كل رسالة
@bot.message_handler(func=lambda message: True)
def reply_to_user(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text

    # إنشاء تاريخ محادثة خاص بهذه الدردشة
    if chat_id not in chat_histories:
        chat_histories[chat_id] = [
            {"role": "system",
             "content": (
                 "You are Jamal's personal assistant. "
                 "You help the admin (Jamal) manage the group and channel. "
                 "You never respond to anyone else."
             )}
        ]
    
    # إضافة الرسالة لتاريخ المحادثة
    chat_histories[chat_id].append({"role": "user", "content": text})
    if len(chat_histories[chat_id]) > 11:
        chat_histories[chat_id][1:] = chat_histories[chat_id][-9:]

    # الحصول على الرد من Groq API
    reply = get_groq_response(chat_histories[chat_id])
    chat_histories[chat_id].append({"role": "assistant", "content": reply})

    # ✅ إذا كان المرسل هو المالك (Owner) في الخاص → ينشر في القناة
    if user_id == OWNER_ID and message.chat.type == "private":
        bot.send_message(CHANNEL_ID, f"📢 رسالة من المالك:\n{text}")
        bot.send_message(chat_id, "✔ تم نشر رسالتك في القناة")
    else:
        # الرد في نفس مكان الرسالة (مجموعة أو رسالة خاصة من شخص آخر)
        bot.reply_to(message, reply)

print("🚀 جاري تشغيل البوت...")
bot.infinity_polling()
