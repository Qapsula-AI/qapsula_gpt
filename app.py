import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from llama_cpp import Llama
from dotenv import load_dotenv

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных
load_dotenv()

# Токен бота
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")
    exit(1)

# Загрузка модели
MODEL_PATH = os.getenv("MODEL_PATH", "./models/gpt4all-falcon.Q4_0.gguf")
logger.info(f"Загружаю модель: {MODEL_PATH}")

try:
    model = Llama(
        model_path=MODEL_PATH,
        n_ctx=1024,
        n_threads=2,
        verbose=False
    )
    logger.info("✅ Модель загружена!")
except Exception as e:
    logger.error(f"❌ Ошибка загрузки модели: {e}")
    model = None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Привет! Я тестовый бот Qapsula с GPT.\n\n"
        "Задавайте вопросы, и я постараюсь помочь!\n"
        "⚠️ Ответ может занять 15-30 секунд"
    )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if model is None:
        await update.message.reply_text("⚠️ Модель не загружена. Попробуйте позже.")
        return
    
    user_text = update.message.text
    user_id = update.effective_user.id
    logger.info(f"👤 User {user_id}: {user_text[:50]}...")
    
    # Отправляем "печатает..." статус
    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
    except:
        pass
    
    # Отправляем сообщение о времени обработки
    processing_msg = await update.message.reply_text(
        "⏳ Обрабатываю запрос... (это займет 15-30 секунд)"
    )
    
    try:
        # Промпт на русском для лучших ответов
        prompt = f"""Ты - полезный AI ассистент Qapsula. Отвечай на русском языке.
        
Вопрос: {user_text}

Ответ (на русском, кратко и по делу):"""
        
        logger.info("Генерирую ответ...")
        
        # Генерация ответа
        output = model(
            prompt,
            max_tokens=300,
            temperature=0.7,
            top_p=0.9,
            echo=False,
            stop=["###", "Вопрос:", "Question:"]
        )
        
        # Извлекаем ответ
        answer = output['choices'][0]['text'].strip()
        
        # Очищаем ответ
        if "Ответ:" in answer:
            answer = answer.split("Ответ:")[-1].strip()
        if "ответ:" in answer:
            answer = answer.split("ответ:")[-1].strip()
        
        # Удаляем маркеры
        answer = answer.replace("###", "").strip()
        
        # Если ответ пустой или слишком короткий
        if len(answer) < 5:
            answer = "Извините, не могу сгенерировать подходящий ответ на этот вопрос."
        
        # Удаляем сообщение "Обрабатываю..."
        try:
            await processing_msg.delete()
        except:
            pass
        
        # Отправляем ответ
        logger.info(f"✅ Ответ готов ({len(answer)} символов)")
        await update.message.reply_text(answer[:4000])
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        
        # Удаляем сообщение "Обрабатываю..."
        try:
            await processing_msg.delete()
        except:
            pass
        
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке запроса.\n"
            "Попробуйте задать вопрос иначе или попозже."
        )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Доступные команды:\n"
        "/start - начать диалог\n"
        "/help - эта справка\n\n"
        "💡 Советы:\n"
        "• Ответы генерируются 15-30 секунд\n"
        "• Задавайте вопросы на русском\n"
        "• Бот работает на модели GPT4All Falcon"
    )

# Команда /status
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = "✅ Бот работает нормально" if model else "⚠️ Модель не загружена"
    await update.message.reply_text(
        f"📊 Статус системы:\n"
        f"{status}\n"
        f"Модель: GPT4All Falcon\n"
        f"Контекст: 1024 токенов"
    )

# Главная функция
def main():
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("🤖 Бот запускается...")
    logger.info("Модель: GPT4All Falcon")
    logger.info("Язык: Русский")
    
    try:
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()