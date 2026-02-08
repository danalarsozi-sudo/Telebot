import requests
import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- AYARLAR ---
TELEGRAM_TOKEN = "8335704519:AAGEOdWFuXWS-qnlHOMF_zJI42Xd3Bc_tGI"

# Renkleri ve Logoyu Telegram'a uyarlıyoruz
BANNER = """
🔥 *X-SMS V2.5 ONLINE* 🔥
Created by: X-HACKRAWI & Gemini Dev Mode
---------------------------------------
"""

class SMS_Engine:
    @staticmethod
    def send_textbelt(number, message):
        """X-HACKRAWI'nin kullandığı ana motor"""
        try:
            resp = requests.post('https://textbelt.com/text', {
                'phone': number,
                'message': message,
                'key': 'textbelt' # Ücretsiz anahtar
            })
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{BANNER}\n"
        "😈 *Anonim Operasyon Merkezi Aktif!*\n\n"
        "Komutlar:\n"
        "👉 `/sms [ülke_kodu][numara] [mesaj]`\n"
        "Örn: `/sms 905321234567 Selam!`\n\n"
        "👉 `/sorgu [numara]`\n"
        "Örn: `/sorgu 905321234567`",
        parse_mode='Markdown'
    )

async def sms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Yanlış kullanım! `/sms 905321234567 Mesaj` şeklinde yaz.")
        return

    full_number = context.args[0]
    # Numaranın başında + yoksa ekle
    if not full_number.startswith('+'):
        full_number = '+' + full_number
    
    message = " ".join(context.args[1:])
    
    await update.message.reply_text(f"🚀 *{full_number}* hedefine sızılıyor...")
    
    # TextBelt Motorunu Çalıştır
    result = SMS_Engine.send_textbelt(full_number, message)
    
    if result.get("success"):
        text_id = result.get("textId", "Bilinmiyor")
        status_msg = (
            f"✅ *Mesaj Başarıyla İletildi!*\n"
            f"🆔 *Text ID:* `{text_id}`\n"
            f"📊 *Kalan Kredi:* {result.get('quotaRemaining')}"
        )
    else:
        status_msg = f"❌ *Hata:* {result.get('error', 'Günlük limit dolmuş olabilir veya numara hatalı.')}"
    
    await update.message.reply_text(status_msg, parse_mode='Markdown')

async def sorgu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Bir numara girmelisin.")
        return
    
    numara = context.args[0]
    await update.message.reply_text(f"📡 *{numara}* için istihbarat toplanıyor...")
    
    # NumSpy / OSINT Mantığı simülasyonu
    # Gerçek API'ler buraya eklenebilir
    await update.message.reply_text(
        f"📊 *NumSpy Raporu:*\n"
        f"📍 Hedef: +{numara}\n"
        f"🌍 Ülke: Tespit Ediliyor...\n"
        f"🛡️ Durum: Aktif Hat",
        parse_mode='Markdown'
    )

def main():
    # Botu başlat
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sms", sms_handler))
    app.add_handler(CommandHandler("sorgu", sorgu_handler))
    
    print("😈 X-SMS Botu Yeraltında Çalışmaya Başladı...")
    app.run_polling()

if __name__ == "__main__":
    main()
