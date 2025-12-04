import os
import logging
import requests
import tempfile
import speech_recognition as sr
from pathlib import Path  # 👈 Добавили
from pydub import AudioSegment
from telegram import Update, Voice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# Загружаем токены
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("❌ Проверь TELEGRAM_TOKEN и OPENAI_API_KEY в key.env")

# OpenAI клиент
client = OpenAI(api_key=OPENAI_API_KEY)


# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Генерация изображения
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str = None):
    if prompt is None:
        prompt = update.message.text
    logger.info(f"Генерация изображения по запросу: {prompt}")
    try:
        response = client.images.generate(prompt=prompt, n=1, size="512x512")
        image_url = response.data[0].url
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Открыть изображение", url=image_url)]
        ])
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_url,
                                     caption="🖼️ Вот что получилось!", reply_markup=keyboard)
    except Exception as e:
        logger.exception("Ошибка генерации изображения:")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Ошибка при генерации изображения.")
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice: Voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    ogg_path = tempfile.mktemp(suffix=".ogg")
    wav_path = ogg_path.replace(".ogg", ".wav")

    try:
        await file.download_to_drive(ogg_path)
        sound = AudioSegment.from_ogg(ogg_path)
        sound.export(wav_path, format="wav")
    except:
        await update.message.reply_text("❌ Не удалось обработать голос.")
        return

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.listen(source, phrase_time_limit=10)
            text = recognizer.recognize_google(audio, language="ru-RU")
            logger.info(f"🎤 Распознанный текст: {text}")
        await update.message.reply_text(f"🎤 Вы сказали: {text}")
    except:
        await update.message.reply_text("🛑 Речь не распознана.")
        return

    # Картинка по ключевым словам
    if "фото" in text.lower():
        photo_url = await fetch_real_photo(text)
        if photo_url:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption="📸 Фото из интернета")
        else:
            await update.message.reply_text("❌ Фото не найдено.")
        return

    if "картинк" in text.lower() or "изображени" in text.lower():
        await generate_image(update, context, prompt=text)
        return

    # Ответ от AI
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text}]
        )
        answer = response.choices[0].message.content.strip()
        await update.message.reply_text(f"💬 {answer}")  # ← текстовый ответ
    except:
        await update.message.reply_text("❌ Ошибка AI.")
        return

    # Голосовой ответ
    try:
        tts = gTTS(answer, lang="ru")
        ogg_reply = tempfile.mktemp(suffix=".ogg")
        tts.save("temp.mp3")
        sound = AudioSegment.from_mp3("temp.mp3")
        sound.export(ogg_reply, format="ogg", codec="libopus")
        await update.message.reply_voice(voice=open(ogg_reply, "rb"))  # ← голосовой ответ
    except:
        await update.message.reply_text("🔇 Не удалось озвучить ответ.")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋 Отправь мне:\n\n"
        "📝 Текст — я сгенерирую изображение\n"
        "🎤 Голос — я распознаю его и, если ты попросишь картинку, нарисую её 🖼️"
    )

# Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    logger.info("✅ Бот запущен.")
    app.run_polling()
