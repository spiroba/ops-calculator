#!/usr/bin/env python3
"""
Telegram бот для расчета премий ОПС v2.4
Полная синхронизация с HTML калькулятором премий
"""

import logging
from typing import Dict, Any
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ConversationHandler, ContextTypes
)

from config_v2 import (
    TOKEN, MESSAGES, POSITIONS_CONFIG, OPERATIONS_CONFIG, 
    KPI_CONFIG, TEAM_COEFFICIENTS_CONFIG, POSITION_RATES,
    UserState
)
from calculator_v2 import PremiumCalculator, format_money, format_percent

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния разговора
(CHOOSING_POSITION, ENTERING_SALARY, ENTERING_RATE,
 ENTERING_OPERATIONS, ENTERING_KPI, ENTERING_COEFFICIENTS,
 SHOWING_RESULTS, ENTERING_SUBORDINATES) = range(8)

# Глобальное хранилище состояний пользователей
user_states = {}

class PremiumBot:
    """Главный класс бота премий ОПС"""
    
    def __init__(self):
        self.calculator = PremiumCalculator()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Команда /start"""
        user_id = update.effective_user.id
        user_states[user_id] = UserState()
        
        await update.message.reply_text(
            MESSAGES["start"],
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Команда /help"""
        await update.message.reply_text(
            MESSAGES["help"],
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    async def positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Команда /positions - список должностей"""
        await update.message.reply_text(
            MESSAGES["positions"],
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    async def operations(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Команда /operations - список всех операций"""
        text = "📊 <b>Все операции в системе:</b>\n\n"
        
        for op_id, op_config in OPERATIONS_CONFIG.items():
            emoji = op_config.get('emoji', '📊')
            name = op_config['name']
            rate = op_config['rate']
            text += f"{emoji} <b>{op_id}.</b> {name}\n    {rate}_\n\n"
        
        # Разделяем на части если слишком длинное
        if len(text) > 4000:
            parts = text.split('\n\n')
            current = ""
            for part in parts:
                if len(current + part) > 4000:
                    await update.message.reply_text(
                        current,
                        parse_mode=ParseMode.HTML
                    )
                    current = part + "\n\n"
                else:
                    current += part + "\n\n"
            
            if current:
                await update.message.reply_text(
                    current,
                    parse_mode=ParseMode.HTML
                )
        else:
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML
            )
        
        return ConversationHandler.END
    
    async def calculate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало расчета премии"""
        user_id = update.effective_user.id
        user_states[user_id] = UserState()
        
        # Создаем клавиатуру с должностями
        keyboard = []
        for pos_id, pos_config in POSITIONS_CONFIG.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{pos_config['emoji']} {pos_config['name']}", 
                                         callback_data=f"pos_{pos_id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👥 <b>Выберите вашу должность:</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return CHOOSING_POSITION
    
    async def position_chosen(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора должности"""
        query = update.callback_query
        await query.answer()
        
                 user_id = update.effective_user.id
         position = query.data.replace("pos_", "")
        
        if user_id not in user_states:
            user_states[user_id] = UserState()
        
        user_states[user_id].position = position
        position_config = POSITIONS_CONFIG[position]
        
        # Проверяем, нужны ли КПИ показатели
        if position_config.get('kpi'):
            await query.edit_message_text(
                f"✅ Выбрана должность: <b>{position_config['name']}</b>\n\n"
                f"💰 Для расчета КПИ укажите размер оклада по трудовому договору (в рублях):",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_SALARY
        else:
            # Для должностей без КПИ сразу переходим к операциям
            await query.edit_message_text(
                f"✅ Выбрана должность: <b>{position_config['name']}</b>\n\n"
                f"📊 Теперь введите данные по операциям.\n"
                f"Используйте формат: `номер операции: количество`\n"
                f"Например: `1: 5000` (розница 5000₽)\n\n"
                f"Введите /operations для списка всех операций.\n"
                f"Введите /done когда закончите.",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_OPERATIONS
    
    async def salary_entered(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка введенного оклада"""
        user_id = update.effective_user.id
        
        try:
            salary = float(update.message.text.replace(',', '').replace(' ', ''))
            if salary <= 0:
                raise ValueError("Оклад должен быть больше 0")
            
            user_states[user_id].base_salary = salary
            
            # Создаем клавиатуру с размерами ставок
            keyboard = []
            for rate_value, rate_name in POSITION_RATES.items():
                keyboard.append([
                    InlineKeyboardButton(
                        rate_name, 
                                                 callback_data=f"rate_{rate_value}"
                    )
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ Оклад: <b>{format_money(salary)}</b>\n\n"
                f"📊 Выберите размер занимаемой ставки:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
            return ENTERING_RATE
            
        except ValueError:
            await update.message.reply_text(
                "❌ Некорректный размер оклада. "
                "Введите число в рублях (например: 30000):",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_SALARY
    
    async def rate_chosen(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора размера ставки"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        rate = float(query.data.replace("rate_", ""))
        
        user_states[user_id].position_rate = rate
        
        # Рассчитываем реальный оклад
        real_salary = user_states[user_id].base_salary * rate
        
        await query.edit_message_text(
            f"✅ Размер ставки: <b>{rate}</b> ({rate*100:.0f}%)\n"
            f"💰 Реальный размер оклада: <b>{format_money(real_salary)}</b>\n\n"
            f"📊 Теперь введите данные по операциям.\n"
            f"Используйте формат: `номер операции: количество`\n"
            f"Например: `1: 5000` (розница 5000₽)\n\n"
            f"Введите /operations для списка всех операций.\n"
            f"Введите /done когда закончите.",
            parse_mode=ParseMode.HTML
        )
        
        return ENTERING_OPERATIONS
    
    async def operation_entered(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка введенной операции"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        if text == "/done":
            return await self.move_to_kpi_or_coefficients(update, context)
        elif text == "/operations":
            await self.operations(update, context)
            return ENTERING_OPERATIONS
        
        try:
            # Парсим формат "номер: количество"
            if ':' not in text:
                raise ValueError("Используйте формат 'номер: количество'")
            
            op_id_str, quantity_str = text.split(':', 1)
            op_id = int(op_id_str.strip())
            quantity = float(quantity_str.strip().replace(',', '').replace(' ', ''))
            
            if op_id not in OPERATIONS_CONFIG:
                raise ValueError(f"Операция {op_id} не существует")
            
            if quantity < 0:
                raise ValueError("Количество не может быть отрицательным")
            
            # Сохраняем операцию
            user_states[user_id].operations[op_id] = quantity
            
            op_config = OPERATIONS_CONFIG[op_id]
            emoji = op_config.get('emoji', '📊')
            
            await update.message.reply_text(
                f"✅ {emoji} <b>{op_config['name']}</b>: {quantity} {op_config.get('unit', '')}\n\n"
                f"Продолжайте вводить операции или /done для завершения.",
                parse_mode=ParseMode.HTML
            )
            
            return ENTERING_OPERATIONS
            
        except (ValueError, IndexError) as e:
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}\n"
                f"Используйте формат: `номер операции: количество`\n"
                f"Например: `1: 5000`",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_OPERATIONS
    
    async def move_to_kpi_or_coefficients(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Переход к КПИ или коэффициентам в зависимости от должности"""
        user_id = update.effective_user.id
        position = user_states[user_id].position
        position_config = POSITIONS_CONFIG[position]
        
        # Показываем введенные операции
        ops_text = "📊 <b>Введенные операции:</b>\n\n"
        for op_id, quantity in user_states[user_id].operations.items():
            op_config = OPERATIONS_CONFIG[op_id]
            emoji = op_config.get('emoji', '📊')
            ops_text += f"{emoji} {op_config['name']}: {quantity} {op_config.get('unit', '')}\n"
        
        if not user_states[user_id].operations:
            ops_text += "Операции не введены_\n"
        
        ops_text += "\n"
        
        # Проверяем, есть ли КПИ показатели
        if position_config.get('kpi'):
            kpi_list = ""
            for kpi_id in position_config['kpi']:
                kpi_config = KPI_CONFIG[kpi_id]
                emoji = kpi_config.get('emoji', '📊')
                kpi_list += f"{emoji} {kpi_config['name']}\n"
            
            await update.message.reply_text(
                f"{ops_text}"
                f"⭐ <b>Теперь введите КПИ показатели:</b>\n\n"
                f"{kpi_list}\n"
                f"Используйте формат: `показатель: процент`\n"
                f"Например: `revenue: 95` (выручка 95%)\n\n"
                f"Доступные показатели: {', '.join(position_config['kpi'])}\n"
                f"Введите /done когда закончите.",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_KPI
        
        # Проверяем, есть ли командные коэффициенты
        elif position_config.get('teamCoefficients'):
            coeff_list = ""
            for coeff_id in position_config['teamCoefficients']:
                coeff_config = TEAM_COEFFICIENTS_CONFIG[coeff_id]
                emoji = coeff_config.get('emoji', '📊')
                coeff_list += f"{emoji} {coeff_config['name']}\n"
            
            await update.message.reply_text(
                f"{ops_text}"
                f"⚡ <b>Теперь введите командные коэффициенты:</b>\n\n"
                f"{coeff_list}\n"
                f"Используйте формат: `коэффициент: значение`\n"
                f"Например: `service: 92` (CSI 92 балла)\n\n"
                f"Доступные коэффициенты: {', '.join(position_config['teamCoefficients'])}\n"
                f"Введите /done когда закончите.",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_COEFFICIENTS
        
        # Если нет ни КПИ, ни коэффициентов - сразу показываем результат
        else:
            return await self.show_results(update, context)
    
    async def kpi_entered(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка введенного КПИ"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        if text == "/done":
            # Переходим к коэффициентам или результатам
            position = user_states[user_id].position
            position_config = POSITIONS_CONFIG[position]
            
            if position_config.get('teamCoefficients'):
                coeff_list = ""
                for coeff_id in position_config['teamCoefficients']:
                    coeff_config = TEAM_COEFFICIENTS_CONFIG[coeff_id]
                    emoji = coeff_config.get('emoji', '📊')
                    coeff_list += f"{emoji} {coeff_config['name']}\n"
                
                await update.message.reply_text(
                    f"⚡ <b>Теперь введите командные коэффициенты:</b>\n\n"
                    f"{coeff_list}\n"
                    f"Используйте формат: `коэффициент: значение`\n"
                    f"Например: `service: 92`\n\n"
                    f"Доступные: {', '.join(position_config['teamCoefficients'])}\n"
                    f"Введите /done когда закончите.",
                    parse_mode=ParseMode.HTML
                )
                return ENTERING_COEFFICIENTS
            else:
                return await self.show_results(update, context)
        
        try:
            # Парсим формат "показатель: процент"
            if ':' not in text:
                raise ValueError("Используйте формат 'показатель: процент'")
            
            kpi_id, percent_str = text.split(':', 1)
            kpi_id = kpi_id.strip()
            percent = float(percent_str.strip())
            
            position_config = POSITIONS_CONFIG[user_states[user_id].position]
            if kpi_id not in position_config.get('kpi', []):
                raise ValueError(f"КПИ '{kpi_id}' недоступно для вашей должности")
            
            if percent < 0:
                raise ValueError("Процент не может быть отрицательным")
            
            # Сохраняем КПИ
            user_states[user_id].kpi[kpi_id] = percent
            
            kpi_config = KPI_CONFIG[kpi_id]
            emoji = kpi_config.get('emoji', '📊')
            
            await update.message.reply_text(
                f"✅ {emoji} <b>{kpi_config['name']}</b>: {format_percent(percent)}\n\n"
                f"Продолжайте вводить КПИ или /done для завершения.",
                parse_mode=ParseMode.HTML
            )
            
            return ENTERING_KPI
            
        except (ValueError, IndexError) as e:
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}\n"
                f"Используйте формат: `показатель: процент`\n"
                f"Например: `revenue: 95`",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_KPI
    
    async def coefficient_entered(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка введенного коэффициента"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        if text == "/done":
            return await self.show_results(update, context)
        
        try:
            # Парсим формат "коэффициент: значение"
            if ':' not in text:
                raise ValueError("Используйте формат 'коэффициент: значение'")
            
            coeff_id, value_str = text.split(':', 1)
            coeff_id = coeff_id.strip()
            value = float(value_str.strip())
            
            position_config = POSITIONS_CONFIG[user_id]
            if coeff_id not in position_config.get('teamCoefficients', []):
                raise ValueError(f"Коэффициент '{coeff_id}' недоступен для вашей должности")
            
            if value < 0:
                raise ValueError("Значение не может быть отрицательным")
            
            # Сохраняем коэффициент
            user_states[user_id].team_coefficients[coeff_id] = value
            
            coeff_config = TEAM_COEFFICIENTS_CONFIG[coeff_id]
            emoji = coeff_config.get('emoji', '📊')
            
            await update.message.reply_text(
                f"✅ {emoji} <b>{coeff_config['name']}</b>: {value}\n\n"
                f"Продолжайте вводить коэффициенты или /done для завершения.",
                parse_mode=ParseMode.HTML
            )
            
            return ENTERING_COEFFICIENTS
            
        except (ValueError, IndexError) as e:
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}\n"
                f"Используйте формат: `коэффициент: значение`\n"
                f"Например: `service: 92`",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_COEFFICIENTS
    
    async def show_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показ результатов расчета"""
        user_id = update.effective_user.id
        state = user_states[user_id]
        
        try:
            # Выполняем расчет
            result = self.calculator.calculate_premium(
                position=state.position,
                base_salary=state.base_salary,
                position_rate=state.position_rate,
                operations=state.operations,
                kpi_values=state.kpi,
                team_coefficients=state.team_coefficients,
                subordinates_bonus=state.subordinates_bonus
            )
            
            # Формируем результат
            text = f"🎯 <b>РЕЗУЛЬТАТ РАСЧЕТА ПРЕМИИ</b>\n\n"
            text += f"👤 <b>Должность:</b> {result.position_name}\n"
            
            # Информация об окладе (только для КПИ должностей)
            if result.base_salary > 0 and result.position_rate > 0:
                text += f"💰 <b>Оклад по договору:</b> {format_money(result.base_salary)}\n"
                text += f"📊 <b>Размер ставки:</b> {result.position_rate} ({result.position_rate*100:.0f}%)\n"
                text += f"💵 <b>Реальный размер оклада:</b> {format_money(result.real_salary)}\n\n"
            
            # Результаты
            text += f"🏆 <b>ИТОГОВАЯ ПРЕМИЯ: {format_money(result.total_premium)}</b>\n\n"
            
            if result.operation_bonus > 0:
                text += f"📈 Бонус за операции: <b>{format_money(result.operation_bonus)}</b>\n"
            
            if result.kpi_bonus > 0:
                text += f"⭐ Бонус КПИ: <b>{format_money(result.kpi_bonus)}</b>\n"
            
            text += "\n"
            
            # Детализация операций
            if result.operation_details:
                text += "📊 <b>Детализация операций:</b>\n"
                for detail in result.operation_details:
                    emoji = detail.get('emoji', '📊')
                    name = detail['name']
                    quantity = detail['quantity']
                    final_bonus = detail['final_bonus']
                    
                    if detail['coefficient'] != 1.0:
                        text += f"{emoji} {name}: {quantity} → {format_money(final_bonus)} (к={detail['coefficient']:.1f})\n"
                    else:
                        text += f"{emoji} {name}: {quantity} → {format_money(final_bonus)}\n"
                text += "\n"
            
            # Детализация КПИ
            if result.kpi_details:
                text += "⭐ <b>Детализация КПИ:</b>\n"
                for detail in result.kpi_details:
                    emoji = detail.get('emoji', '📊')
                    name = detail['name']
                    percent = detail['percent']
                    bonus = detail['bonus']
                    coeff = detail['coefficient']
                    
                    text += f"{emoji} {name}: {format_percent(percent)} → {format_money(bonus)} (к={coeff:.2f})\n"
                text += "\n"
            
            # Предупреждения
            if result.warnings:
                text += "⚠️ <b>Важные уведомления:</b>\n"
                for warning in result.warnings:
                    text += f"• {warning}\n"
                text += "\n"
            
            # Кнопки действий
            keyboard = [
                [InlineKeyboardButton("🔄 Новый расчет", callback_data="new_calculation")],
                [InlineKeyboardButton("📊 Показать формулы", callback_data="show_formulas")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
            return SHOWING_RESULTS
            
        except Exception as e:
            logger.error(f"Ошибка расчета для пользователя {user_id}: {e}")
            await update.message.reply_text(
                f"❌ Ошибка при расчете премии: {str(e)}\n\n"
                f"Используйте /calculate для повторного расчета.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
    
    async def result_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка действий в результатах"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "new_calculation":
            await query.edit_message_text(
                "🔄 Начинаем новый расчет!\n\n"
                "Используйте /calculate для расчета премии.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        elif query.data == "show_formulas":
            formulas_text = (
                "📐 <b>Формулы расчета:</b>\n\n"
                "<b>КПИ бонус (v2.4):</b>\n"
                "`КПИ = (оклад × ставка) × коэффициент_КПИ`\n\n"
                "<b>Операции с коэффициентами:</b>\n"
                "• Тип 1: без коэффициентов\n"
                "• Тип 2: × коэффициент сервиса (CSI)\n"
                "• Тип 3: × коэффициент скорости приема\n"
                "• Тип 4: × коэффициент скорости вручения\n\n"
                "<b>Коэффициент эффективности:</b>\n"
                "При выручке ≥100%: +30% к операционной премии\n\n"
                "<b>Критическое правило:</b>\n"
                "Выручка <80% → КПИ = 0₽"
            )
            
            await query.edit_message_text(
                formulas_text,
                parse_mode=ParseMode.HTML
            )
            
            return SHOWING_RESULTS
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена текущего расчета"""
        user_id = update.effective_user.id
        if user_id in user_states:
            del user_states[user_id]
        
        await update.message.reply_text(
            "❌ Расчет отменен. Используйте /calculate для нового расчета.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

def main():
    """Запуск бота"""
    print(f"🚀 Запуск Telegram бота премий ОПС v2.4...")
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    bot = PremiumBot()
    
    # Создаем обработчик разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("calculate", bot.calculate)],
        states={
            CHOOSING_POSITION: [CallbackQueryHandler(bot.position_chosen, pattern="^pos_")],
            ENTERING_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.salary_entered)],
            ENTERING_RATE: [CallbackQueryHandler(bot.rate_chosen, pattern="^rate_")],
            ENTERING_OPERATIONS: [MessageHandler(filters.TEXT, bot.operation_entered)],
            ENTERING_KPI: [MessageHandler(filters.TEXT, bot.kpi_entered)],
            ENTERING_COEFFICIENTS: [MessageHandler(filters.TEXT, bot.coefficient_entered)],
            SHOWING_RESULTS: [CallbackQueryHandler(bot.result_action)]
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)]
    )
    
    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("positions", bot.positions))
    application.add_handler(CommandHandler("operations", bot.operations))
    
    # Запускаем бота
    print("✅ Бот готов к работе!")
    application.run_polling()

if __name__ == "__main__":
    main() 