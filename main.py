import telebot
from telebot import types
import requests
import json
import time
import threading
import random

# --- KONFIGURASYON ---
API_TOKEN = '8335704519:AAGEOdWFuXWS-qnlHOMF_zJI42Xd3Bc_tGI'
GEMINI_API_KEY = "" # Sistem tarafindan otomatik doldurulur
ADMIN_ID = 1748533804
ADMIN_USERNAME = "@Alfa_onlyy"

bot = telebot.TeleBot(API_TOKEN)

# Veritabani (Bellek uzerinde)
users_db = {} 
active_tasks = {} # {user_id: stop_event}
user_lang = {}

# --- AI MESAJ GENERATORU ---
def generate_ai_sms(prompt_type, last_messages=""):
    """Gemini API kullanarak gercekci Turkmençe SMS uretir"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    
    system_prompt = (
        "Sen bir Turkmence SMS simulasyon botusun. Görevin, Turkmen halkinin gunluk hayatta kullandigi dogal, "
        "samimi ve bazen argolu Turkmençe (Latin alfabesi) ile SMS mesajlari uretmek. "
        "Mesajlar su formatta olmali: 'Gelen: [Mesaj]' veya 'Giden: [Mesaj]'. "
        "Konular: Borç isteme, arkadaslarla bulusma, sevgili kavgalari, is gorusmeleri, ailevi meseleler. "
        "Kullaniciya sadece 1 adet mesaj dondur. Mesaj cok gercekci olsun (örnegin: 'Otyryn neme edeyin', 'Jan edesene birje')."
    )
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"{system_prompt}\n\nOnceki mesajlar: {last_messages}\nSimdi yeni bir mesaj uret:"
            }]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        text = result['candidates'][0]['content']['parts'][0]['text']
        return text.strip()
    except:
        # Fallback (AI hata verirse yedek mesajlar)
        fallbacks = [
            "Gelen: Bolya dos oye barayyn jan edeyn",
            "Giden: Ay bolyaday nm edjk saglyk bolsn sagamanja sovduñ",
            "Gelen: Nm un jan edmedn nirde sen?",
            "Giden: O gunki adresleri tazden ugradayda"
        ]
        return random.choice(fallbacks)

# --- ANA DONGU (SMS AKISI) ---
def sms_stream_worker(uid, number, lang):
    history = ""
    while uid in active_tasks:
        sms = generate_ai_sms("normal", history)
        history += f"\n{sms}"
        
        # Sadece son 5 mesaji hafizada tut (AI'yi yormamak icin)
        history = "\n".join(history.split("\n")[-5:])
        
        # Mesaji gonder
        prefix = "📩 " if "Gelen" in sms else "📤 "
        bot.send_message(uid, f"{prefix} *{number}*\n\n{sms}", parse_mode="Markdown")
        
        # 5 saniye bekle
        time.sleep(5)

# --- BOT KOMUTLARI ---
@bot.message_handler(commands=['start'])
def welcome(message):
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Türkmençe 🇹🇲", callback_data="lang_tk"),
               types.InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"))
    bot.send_message(uid, "Diliňizi saýlaň / Выберите язык:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_lang(call):
    uid = call.from_user.id
    lang = call.data.split('_')[1]
    user_lang[uid] = lang
    
    # Yetki kontrolu
    if uid == ADMIN_ID or (uid in users_db and users_db[uid]['status']):
        show_main_menu(uid)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Admin @Alfa_onlyy", url="https://t.me/Alfa_onlyy"))
        bot.send_message(uid, "Hasabyňyz tassyklanmady. Admin bilen habarlaşyň." if lang=='tk' else "Аккаунт не подтвержден. Свяжитесь с админом.", reply_markup=markup)
        bot.send_message(ADMIN_ID, f"🔔 Onay Bekleyen: @{call.from_user.username} (ID: {uid})")

def show_main_menu(uid):
    lang = user_lang.get(uid, 'tk')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_text = "Täze belgi gözegçilik" if lang == 'tk' else "Мониторинг нового номера"
    markup.add(btn_text)
    if uid == ADMIN_ID: markup.add("Admin Panel 🛠")
    bot.send_message(uid, "Sargyt kabul edildi. Belgi ýazyň." if lang == 'tk' else "Заказ принят. Введите номер.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text.startswith('+993') or m.text.isdigit())
def start_monitor(message):
    uid = message.from_user.id
    # Onay kontrolu (Basitlestirilmis)
    if uid != ADMIN_ID and uid not in users_db: return
    
    # Varsa eski gorevi durdur
    if uid in active_tasks:
        del active_tasks[uid]
        time.sleep(1)

    active_tasks[uid] = True
    lang = user_lang.get(uid, 'tk')
    num = message.text
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Başga belgi saýla" if lang == 'tk' else "Выбрать другой номер")
    bot.send_message(uid, f"🔍 {num} gözegçilik edilýär... SMS akymy başlady.", reply_markup=markup)
    
    # Arka planda SMS akisini baslat
    threading.Thread(target=sms_stream_worker, args=(uid, num, lang), daemon=True).start()

@bot.message_handler(func=lambda m: m.text in ["Başga belgi saýla", "Выбрать другой номер", "Täze belgi gözegçilik", "Мониторинг nowego номера"])
def stop_monitor(message):
    uid = message.from_user.id
    if uid in active_tasks:
        del active_tasks[uid]
    lang = user_lang.get(uid, 'tk')
    bot.send_message(uid, "Täze belgiňizi giriziň:" if lang == 'tk' else "Введите новый номер:")

# --- ADMIN PANELI ---
@bot.message_handler(func=lambda m: m.text == "Admin Panel 🛠")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    # Burada kullanicilari onaylama arayuzu olacak (Onceki kodla ayni mantik)
    bot.send_message(ADMIN_ID, "Admin paneli aktif. Onay bekleyenleri yukaridan secin.")

print("AI SMS Botu Calisiyor...")
bot.infinity_polling()
