import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from config import POSITIONS, MESSAGES, UserState, OPERATION_RATES, TOKEN, OPERATIONS
from calculator import calculate_bonus
import logging

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Состояния разговора
CHOOSING_POSITION, ENTERING_OPERATIONS, ENTERING_KPI = range(3)

# Словарь для хранения состояний пользователей
user_states = {}

class UserState:
    def __init__(self):
        self.position = None
        self.operations = {}
        self.kpi = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало разговора и выбор должности"""
    user_id = update.effective_user.id
    user_states[user_id] = UserState()
    
    logging.info(f"User {user_id} started conversation")
    
    # Создаем клавиатуру с должностями
    keyboard = []
    row = []
    for i, (pos_id, pos_data) in enumerate(POSITIONS.items(), 1):
        emoji = pos_data.get('emoji', '👤')
        button = InlineKeyboardButton(f"{emoji} {pos_data['name']}", callback_data=f"pos_{pos_id}")
        row.append(button)
        if i % 2 == 0 or i == len(POSITIONS):  # 2 кнопки в ряд
            keyboard.append(row)
            row = []
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 *Добро пожаловать в калькулятор премий\\!*\n\n"
        "Я помогу вам рассчитать премию за выполненные операции\\.\n"
        "Выберите вашу должность:",
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )
    
    return CHOOSING_POSITION

async def position_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора должности"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    position_id = query.data.replace("pos_", "")
    user_states[user_id].position = position_id
    
    logging.info(f"User {user_id} chose position: {position_id}")
    
    await query.edit_message_text(
        f"*{POSITIONS[position_id]['name']}* выбран\\!\n\n"
        "Теперь отправьте мне КПЭ показатели через пробел:\n\n"
        "*1\\.* CSI \\(0\\-100\\)\n"
        "*2\\.* Выручка \\(0\\-100\\)\n"
        "*3\\.* Скорость приема \\(0\\-100\\)\n"
        "*4\\.* Скорость доставки \\(0\\-100\\)\n\n"
        "_Пример: 95 85 98 97_",
        parse_mode='MarkdownV2'
    )
    
    return ENTERING_KPI

async def process_kpi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода КПЭ"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    logging.info(f"User {user_id} entered KPI: {text}")
    
    try:
        values = text.split()
        if len(values) != 4:
            raise ValueError(
                "Необходимо ввести ровно 4 числа\\!\n\n"
                "📊 *Формат ввода \\(все значения в %\\):*\n"
                "*1\\.* CSI \\(0\\-100\\)\n"
                "*2\\.* Выручка \\(0\\-100\\)\n"
                "*3\\.* Скорость приема \\(0\\-100\\)\n"
                "*4\\.* Скорость доставки \\(0\\-100\\)\n\n"
                "_Пример: 95 85 98 97_"
            )
            
        csi, revenue, speed_accept, speed_delivery = map(float, values)
        
        # Проверка значений - все должны быть в процентах
        for name, value in [
            ("CSI", csi),
            ("Выручка", revenue),
            ("Скорость приема", speed_accept),
            ("Скорость доставки", speed_delivery)
        ]:
            if not (0 <= value <= 100):
                raise ValueError(f"{name} должен быть от 0 до 100%")
            
        user_states[user_id].kpi = {
            "csi": csi,
            "revenue": revenue,
            "speed_accept": speed_accept,
            "speed_delivery": speed_delivery
        }
        
        # Простой расчет премии (пока без операций)
        base_bonus = 5000  # Базовая премия
        kpi_bonus = 0
        
        # Бонус за CSI
        if csi >= 95:
            kpi_bonus += 5000
        elif csi >= 90:
            kpi_bonus += 3000
        elif csi >= 85:
            kpi_bonus += 1000
            
        total_bonus = base_bonus + kpi_bonus
        
        # Формируем сообщение с результатами
        message = (
            f"📊 *Результаты расчета премии*\n\n"
            f"👔 Должность: {POSITIONS[user_states[user_id].position]['name']}\n\n"
            f"💰 *Бонусы:*\n"
            f"• Базовый бонус: {base_bonus}₽\n"
            f"• КПЭ бонус: {kpi_bonus}₽\n\n"
            f"💵 *Итоговая премия:* {total_bonus}₽\n\n"
            f"📈 *КПЭ показатели:*\n"
            f"• CSI: {csi}%\n"
            f"• Выручка: {revenue}%\n"
            f"• Скорость приема: {speed_accept}%\n"
            f"• Скорость доставки: {speed_delivery}%\n\n"
            f"🔄 Для нового расчета используйте /start"
        )
        
        # Добавляем кнопку для нового расчета
        keyboard = [[InlineKeyboardButton("🔄 Новый расчет", callback_data="new_calculation")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
        
        return ConversationHandler.END
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Ошибка ввода: {str(e)}\n\n"
            "Попробуйте еще раз или используйте /cancel для отмены",
            parse_mode='MarkdownV2'
        )
        return ENTERING_KPI

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена операции и сброс состояния"""
    user_id = update.effective_user.id
    if user_id in user_states:
        del user_states[user_id]
    
    await update.message.reply_text(
        "❌ Операция отменена\\.\n"
        "Используйте /start для начала нового расчета\\.",
        parse_mode='MarkdownV2'
    )
    
    return ConversationHandler.END

async def new_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатия кнопки 'Новый расчет'"""
    query = update.callback_query
    await query.answer()
    
    # Перезапускаем процесс с начала
    return await start(update, context)

def main() -> None:
    """Запуск бота"""
    print(f"Starting bot with token: {TOKEN[:10]}...")
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('calculate', start)
        ],
        states={
            CHOOSING_POSITION: [
                CallbackQueryHandler(position_chosen, pattern='^pos_')
            ],
            ENTERING_KPI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_kpi)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(new_calculation, pattern='^new_calculation$')
        ]
    )
    
    application.add_handler(conv_handler)
    
    print("Bot is starting...")
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
