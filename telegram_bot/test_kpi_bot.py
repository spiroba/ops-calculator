import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from config_v2 import KPI_CONFIG

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Состояния диалога
ASKING_KPI = 1

# Хранилище состояния пользователей
user_states = {}

class UserState:
    def __init__(self):
        self.available_kpi = ['revenue', 'online_rpo', 'service_speed', 'return_rate']
        self.current_kpi_index = 0
        self.kpi = {}

class TestKPIBot:
    def __init__(self):
        pass
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Команда /start - начинаем тест КПИ"""
        user_id = update.effective_user.id
        user_states[user_id] = UserState()
        
        await update.message.reply_text(
            "🧪 <b>ТЕСТ КПИ ЛОГИКИ</b>\n\n"
            "Начинаем пошаговый ввод КПИ...",
            parse_mode=ParseMode.HTML
        )
        
        return await self.ask_next_kpi(update, context)
    
    async def ask_next_kpi(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Задать вопрос о следующем КПИ показателе"""
        print(f"[DEBUG] ask_next_kpi triggered")
        
        user_id = update.effective_user.id
        state = user_states[user_id]
        
        print(f"[DEBUG] User {user_id}, Current KPI index: {state.current_kpi_index}, Available KPI: {len(state.available_kpi)}")
        
        # Проверяем, есть ли еще КПИ
        if state.current_kpi_index >= len(state.available_kpi):
            # Все КПИ заданы
            print(f"[DEBUG] All KPIs completed!")
            
            filled_kpi = [(kpi_id, value) for kpi_id, value in state.kpi.items() if value > 0]
            result_text = f"✅ <b>ТЕСТ КПИ ЗАВЕРШЕН!</b>\n\n"
            result_text += f"⭐ <b>КПИ заполнено: {len(filled_kpi)} из {len(state.available_kpi)}</b>\n\n"
            
            if filled_kpi:
                result_text += "⭐ <b>Заполненные КПИ:</b>\n"
                for kpi_id, value in filled_kpi:
                    kpi_config = KPI_CONFIG[kpi_id]
                    emoji = kpi_config.get('emoji', '⭐')
                    result_text += f"{emoji} {kpi_config['name']}: {value}%\n"
            else:
                result_text += "⭐ <b>КПИ:</b> не заполнены\n"
            
            # Определяем откуда пришли
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(result_text, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(result_text, parse_mode=ParseMode.HTML)
            
            return ConversationHandler.END
        
        # Получаем текущий КПИ
        current_kpi_id = state.available_kpi[state.current_kpi_index]
        kpi_config = KPI_CONFIG[current_kpi_id]
        
        print(f"[DEBUG] Asking for KPI: {current_kpi_id} - {kpi_config['name']}")
        
        # Формируем кнопки для процентов
        keyboard = [
            [InlineKeyboardButton("0%", callback_data=f"kpi_{current_kpi_id}_0")],
            [
                InlineKeyboardButton("50%", callback_data=f"kpi_{current_kpi_id}_50"),
                InlineKeyboardButton("60%", callback_data=f"kpi_{current_kpi_id}_60"),
                InlineKeyboardButton("70%", callback_data=f"kpi_{current_kpi_id}_70")
            ],
            [
                InlineKeyboardButton("80%", callback_data=f"kpi_{current_kpi_id}_80"),
                InlineKeyboardButton("90%", callback_data=f"kpi_{current_kpi_id}_90"),
                InlineKeyboardButton("95%", callback_data=f"kpi_{current_kpi_id}_95")
            ],
            [
                InlineKeyboardButton("100%", callback_data=f"kpi_{current_kpi_id}_100"),
                InlineKeyboardButton("105%", callback_data=f"kpi_{current_kpi_id}_105"),
                InlineKeyboardButton("110%", callback_data=f"kpi_{current_kpi_id}_110")
            ],
            [InlineKeyboardButton("⏭️ Пропустить", callback_data=f"kpi_{current_kpi_id}_skip")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        progress = f"({state.current_kpi_index + 1}/{len(state.available_kpi)})"
        
        text = (
            f"⭐ <b>КПИ показатель {progress}:</b>\n\n"
            f"{kpi_config.get('emoji', '⭐')} <b>{kpi_config['name']}</b>\n"
            f"📝 {kpi_config.get('description', '')}\n\n"
            f"❓ <b>Какой процент выполнения?</b>"
        )
        
        # Отправляем новое сообщение для КПИ
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text(
                text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
        
        return ASKING_KPI
    
    async def kpi_answer_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ответа на КПИ показатель"""
        print(f"[DEBUG] kpi_answer_received triggered")
        
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        state = user_states[user_id]
        
        print(f"[DEBUG] User {user_id}, callback data: {query.data}")
        print(f"[DEBUG] Current KPI index: {state.current_kpi_index}")
        print(f"[DEBUG] Available KPI: {state.available_kpi}")
        
        # Парсим данные
        parts = query.data.split('_')
        print(f"[DEBUG] Parsed parts: {parts}")
        
        if len(parts) < 3:
            print(f"[ERROR] Invalid callback data format: {query.data}")
            return ASKING_KPI
        
        kpi_id = parts[1]
        value_or_action = parts[2]
        
        print(f"[DEBUG] KPI ID: {kpi_id}, Action/Value: {value_or_action}")
        
        if value_or_action == "skip":
            # Пропускаем КПИ (оставляем 0)
            print(f"[DEBUG] Skipping KPI {kpi_id}")
            state.kpi[kpi_id] = 0
            state.current_kpi_index += 1
            print(f"[DEBUG] New KPI index: {state.current_kpi_index}")
            
            # Показываем подтверждение
            kpi_config = KPI_CONFIG[kpi_id]
            confirmation = f"⚪ {kpi_config['emoji']} <b>{kpi_config['name']}</b>: пропущено"
            await query.edit_message_text(confirmation, parse_mode=ParseMode.HTML)
            
            # Небольшая задержка
            await asyncio.sleep(0.5)
            
            return await self.ask_next_kpi(update, context)
        
        else:
            # Быстрый выбор процентного значения
            try:
                value = float(value_or_action)
                print(f"[DEBUG] Setting KPI {kpi_id} = {value}%")
                state.kpi[kpi_id] = value
                
                # Показываем подтверждение
                kpi_config = KPI_CONFIG[kpi_id]
                if value > 0:
                    confirmation = f"✅ {kpi_config['emoji']} <b>{kpi_config['name']}</b>: {value}%"
                else:
                    confirmation = f"⚪ {kpi_config['emoji']} <b>{kpi_config['name']}</b>: не заполнено"
                
                await query.edit_message_text(confirmation, parse_mode=ParseMode.HTML)
                
                # Переходим к следующему КПИ
                state.current_kpi_index += 1
                print(f"[DEBUG] Moving to next KPI, new index: {state.current_kpi_index}")
                
                # Небольшая задержка
                await asyncio.sleep(0.5)
                
                return await self.ask_next_kpi(update, context)
                
            except ValueError:
                print(f"[ERROR] Invalid value for KPI: {value_or_action}")
                return ASKING_KPI

def main():
    """Запуск тестового бота"""
    print(f"🧪 Запуск тестового КПИ бота...")
    print(f"Токен: {TOKEN[:10]}...")
    
    application = Application.builder().token(TOKEN).build()
    bot = TestKPIBot()
    
    # Создаем обработчик разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", bot.start)],
        states={
            ASKING_KPI: [CallbackQueryHandler(bot.kpi_answer_received, pattern="^kpi_")]
        },
        fallbacks=[]
    )
    
    application.add_handler(conv_handler)
    
    print("🚀 Тестовый КПИ бот запущен!")
    print("📱 Команды:")
    print("   /start - начать тест КПИ")
    print("\n🛑 Используйте Ctrl+C для остановки.")
    
    application.run_polling()

if __name__ == "__main__":
    main() 