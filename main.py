import telebot
from telebot import types
import datetime
import time

# --- KONFIGURASYON ---
API_TOKEN = '8335704519:AAGEOdWFuXWS-qnlHOMF_zJI42Xd3Bc_tGI'
ADMIN_ID = 1748533804
ADMIN_USERNAME = "@Alfa_onlyy"
bot = telebot.TeleBot(API_TOKEN)

# Veritabani simulasyonu (Gercek projede SQL kullanilmalidir)
users_db = {} # {user_id: {'username': str, 'status': bool, 'expiry': timestamp}}
pending_approvals = {} # {user_id: username}
active_monitoring = {} # {user_id: target_number}

# --- DIL DESTEGI ---
STRINGS = {
    'tk': {
        'welcome': "SMS Monitoring Botuna hoş geldiňiz! 🇹🇲\nBu bot diňe tassyklanan ulanyjylar üçindir.",
        'admin_contact': "Admin bilen habarlaşmak",
        'status_pending': "Hasabyňyz heniz tassyklanmady. Admin bilen habarlaşyň.",
        'enter_num': "Gözegçilik etmek isleýän Türkmenistan belgiňizi ýazyň (Mysal: +99361234567):",
        'monitoring': "Belgi gözegçilikde: ",
        'change_num': "Başga belgi saýla",
        'sms_report': "📩 Täze SMS!\nKimden: {sender}\nSagat: {time}\nTekst: {text}",
        'admin_panel': "Admin Paneli 🛠",
        'lang_select': "Dili saýlaň / Выберите язык"
    },
    'ru': {
        'welcome': "Добро пожаловать в SMS Monitoring Bot! 🇷🇺\nЭтот бот только для одобренных пользователей.",
        'admin_contact': "Связаться с админом",
        'status_pending': "Ваш аккаунт еще не одобрен. Свяжитесь с админом.",
        'enter_num': "Введите туркменский номер для мониторинга (Пример: +99361234567):",
        'monitoring': "Номер на мониторинге: ",
        'change_num': "Выбрать другой номер",
        'sms_report': "📩 Новое СМС!\nОт: {sender}\nВремя: {time}\nТекст: {text}",
        'admin_panel': "Админ Панель 🛠",
        'lang_select': "Выберите язык"
    }
}

user_lang = {} # {user_id: 'tk' or 'ru'}

# --- YARDIMCI FONKSIYONLAR ---
def is_approved(user_id):
    if user_id == ADMIN_ID: return True
    user = users_db.get(user_id)
    if user and user['status']:
        if time.time() < user['expiry']:
            return True
    return False

# --- ANA MENÜ ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    username = message.from_user.username or "NoUser"
    
    # Dil secimi baslat
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Türkmençe 🇹🇲", callback_data="lang_tk"),
               types.InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"))
    bot.send_message(uid, "Please select your language / Diliňizi saýlaň:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    uid = call.from_user.id
    lang = call.data.split('_')[1]
    user_lang[uid] = lang
    
    if is_approved(uid):
        show_main_menu(uid)
    else:
        pending_approvals[uid] = call.from_user.username or str(uid)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(STRINGS[lang]['admin_contact'], url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}"))
        bot.send_message(uid, STRINGS[lang]['status_pending'], reply_markup=markup)
        # Admine bildir
        bot.send_message(ADMIN_ID, f"🔔 Yeni Kullanıcı Onay Bekliyor:\nID: {uid}\nUser: @{call.from_user.username}")

def show_main_menu(uid):
    lang = user_lang.get(uid, 'tk')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(STRINGS[lang]['enter_num'])
    if uid == ADMIN_ID:
        markup.add(STRINGS[lang]['admin_panel'])
    bot.send_message(uid, STRINGS[lang]['welcome'], reply_markup=markup)

# --- ADMIN KOMUTLARI ---
@bot.message_handler(func=lambda m: m.text in [STRINGS['tk']['admin_panel'], STRINGS['ru']['admin_panel']])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    
    markup = types.InlineKeyboardMarkup()
    for uid, uname in pending_approvals.items():
        markup.add(types.InlineKeyboardButton(f"Onayla: @{uname} ({uid})", callback_data=f"approve_{uid}"))
    
    bot.send_message(ADMIN_ID, "Onay bekleyen kullanıcılar ve yönetim:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def approve_user(call):
    if call.from_user.id != ADMIN_ID: return
    uid = int(call.data.split('_')[1])
    
    # Varsayilan 30 gunluk onay
    expiry = time.time() + (30 * 24 * 3600)
    users_db[uid] = {'username': pending_approvals.get(uid), 'status': True, 'expiry': expiry}
    
    if uid in pending_approvals: del pending_approvals[uid]
    
    bot.answer_callback_query(call.id, "Kullanıcı onaylandı (30 Gün)")
    bot.send_message(uid, "✅ Hesabyňyz tassyklanyldy! Boty ulanyp bilersiňiz.")
    bot.send_message(ADMIN_ID, f"Kullanıcı {uid} onaylandı.")

# --- SMS SIMULASYON VE IZLEME ---
@bot.message_handler(func=lambda m: m.text.startswith('+993'))
def start_monitoring(message):
    uid = message.from_user.id
    if not is_approved(uid): return
    
    num = message.text
    active_monitoring[uid] = num
    lang = user_lang.get(uid, 'tk')
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(STRINGS[lang]['change_num'])
    
    bot.send_message(uid, f"{STRINGS[lang]['monitoring']} {num}\n\n⏳ Garaşyň, SMS-ler çekilýär...", reply_markup=markup)
    
    # Simulasyon: 5 saniye sonra hayali bir SMS gonder
    time.sleep(5)
    fake_sms = STRINGS[lang]['sms_report'].format(
        sender="+99365112233",
        time=datetime.datetime.now().strftime("%H:%M:%S"),
        text="Salam, gowumy ýagdaýlaryň? Agşam görüşýärismi?"
    )
    bot.send_message(uid, fake_sms)

@bot.message_handler(func=lambda m: m.text in [STRINGS['tk']['change_num'], STRINGS['ru']['change_num']])
def change_num(message):
    uid = message.from_user.id
    lang = user_lang.get(uid, 'tk')
    bot.send_message(uid, STRINGS[lang]['enter_num'])

# Botu baslat
print("Bot baslatildi...")
bot.infinity_polling()
