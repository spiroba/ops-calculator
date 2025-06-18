import os
import logging
import asyncio
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
from telegram.constants import ParseMode

from config_v2 import (
    TOKEN, MESSAGES, POSITIONS_CONFIG, OPERATIONS_CONFIG, 
    KPI_CONFIG, KPI_WEIGHTS, TEAM_COEFFICIENTS_CONFIG, POSITION_RATES,
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
 ASKING_OPERATIONS, ASKING_OPERATION_QUANTITY, ASKING_PVZ_SCHEDULE, ASKING_PVZ_RATING,
ASKING_KPI, ASKING_COEFFICIENTS, ENTERING_COEFFICIENTS, SHOWING_RESULTS) = range(11)

# Глобальное хранилище состояний пользователей
user_states: Dict[int, UserState] = {}

def get_operations_for_position(position_id: str) -> list:
    """Получить список операций доступных для должности"""
    position_config = POSITIONS_CONFIG.get(position_id, {})
    available_operations = position_config.get('operations', [])
    
    # Если operations не указаны, возвращаем все операции
    if not available_operations:
        return list(OPERATIONS_CONFIG.keys())
    
    return available_operations

# Главное меню с кнопками
def get_main_menu():
    """Создает главное меню с кнопками"""
    keyboard = [
        [KeyboardButton("🧮 Рассчитать премию")],
        [KeyboardButton("📋 Список должностей"), KeyboardButton("📊 Список операций")],
        [KeyboardButton("❓ Справка"), KeyboardButton("🆘 Помощь")],
        [KeyboardButton("🗑️ Очистить расчет")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

class CleanPremiumBot:
    """Чистый бот калькулятора премий ОПС с кнопками меню"""
    
    def __init__(self):
        self.calculator = PremiumCalculator()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Команда /start с главным меню"""
        user_id = update.effective_user.id
        user_states[user_id] = UserState()
        
        welcome_text = (
            "👋 <b>Добро пожаловать в калькулятор премий ОПС v2.4!</b>\n\n"
            "Я помогу вам рассчитать премию с учетом:\n"
            "💰 Размера оклада и ставки\n"
            "📊 Всех 25 типов операций\n"
            "⭐ КПИ показателей\n"
            "⚡ Командных коэффициентов\n\n"
            "👇 <b>Используйте кнопки меню для навигации:</b>"
        )
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Команда /help"""
        help_text = (
            "🔍 <b>Справка по использованию:</b>\n\n"
            "🧮 <b>Рассчитать премию</b> - Начать расчет премии\n"
            "📋 <b>Список должностей</b> - Показать все должности\n"
            "📊 <b>Список операций</b> - Показать все операции\n"
            "❓ <b>Справка</b> - Показать формулы расчета\n"
            "🆘 <b>Помощь</b> - Это сообщение\n\n"
            "🤖 Версия: v2.4 (синхронизация с HTML калькулятором)\n\n"
            "💡 <b>Команды:</b>\n"
            "/start - Главное меню\n"
            "/cancel - Отменить текущий расчет\n\n"
            "👆 <b>Используйте кнопки меню - это удобнее!</b>"
        )
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END
    
    async def handle_menu_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка нажатий кнопок меню"""
        text = update.message.text
        
        if text == "🧮 Рассчитать премию":
            return await self.calculate(update, context)
        elif text == "📋 Список должностей":
            return await self.positions(update, context)
        elif text == "📊 Список операций":
            return await self.operations(update, context)
        elif text == "❓ Справка":
            return await self.show_formulas_help(update, context)
        elif text == "🆘 Помощь":
            return await self.help_command(update, context)
        elif text == "🗑️ Очистить расчет":
            return await self.clear_calculation(update, context)
        else:
            # Неизвестная кнопка
            await update.message.reply_text(
                "❓ Выберите действие из меню ниже:",
                reply_markup=get_main_menu()
            )
            return ConversationHandler.END
    
    async def clear_calculation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Очистка всех данных расчета пользователя"""
        user_id = update.effective_user.id
        
        # Проверяем, есть ли данные для очистки
        if user_id in user_states:
            # Очищаем состояние пользователя
            del user_states[user_id]
            
            await update.message.reply_text(
                "🗑️ <b>Расчет очищен!</b>\n\n"
                "✅ Все введенные данные удалены:\n"
                "• Должность\n"
                "• Оклад и ставка\n"
                "• Операции\n"
                "• КПИ показатели\n"
                "• Командные коэффициенты\n\n"
                "🔄 Теперь можете начать новый расчет с чистого листа.\n\n"
                "💡 Нажмите <b>🧮 Рассчитать премию</b> для нового расчета.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text(
                "ℹ️ <b>Нет данных для очистки</b>\n\n"
                "У вас нет активного расчета для очистки.\n\n"
                "💡 Нажмите <b>🧮 Рассчитать премию</b> чтобы начать новый расчет.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        
        return ConversationHandler.END
    
    async def show_formulas_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показать справку с формулами"""
        formulas_text = (
            "📐 <b>Формулы расчета премий ОПС v2.4:</b>\n\n"
            "💰 <b>КПИ бонус (новая формула):</b>\n"
            "<code>КПИ = (оклад × ставка) × коэффициент_КПИ</code>\n\n"
            "⚡ <b>Операции с коэффициентами:</b>\n"
            "• Тип 1: без коэффициентов\n"
            "• Тип 2: × коэффициент сервиса (CSI)\n"
            "• Тип 3: × коэффициент скорости приема\n"
            "• Тип 4: × коэффициент скорости вручения\n\n"
            "📈 <b>Коэффициент эффективности:</b>\n"
            "При выручке ≥100%: +30% к операционной премии\n\n"
            "⚠️ <b>Критическое правило:</b>\n"
            "Выручка &lt;80% → КПИ = 0₽\n\n"
            "🏆 <b>Итоговая формула:</b>\n"
            "<code>Премия = Операции + КПИ + Бонусы</code>"
        )
        
        await update.message.reply_text(
            formulas_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END
    
    async def positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Команда показа должностей с возвратом в меню"""
        positions_text = (
            "👥 <b>Должности в системе:</b>\n\n"
            "👨‍💼 Оператор 1-3 класса\n"
            "👨‍💼 НОПС без операторов\n"
            "👨‍✈️ НОПС с операторами\n"
            "👨‍💻 Администратор\n"
            "🚶‍♂️ Почтальон\n"
            "👨‍🔬 Главный специалист\n\n"
            "💡 Для расчета премии нажмите кнопку <b>🧮 Рассчитать премию</b>"
        )
        
        await update.message.reply_text(
            positions_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END
    
    async def operations(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Команда показа операций с возвратом в меню"""
        text = "📊 <b>Все операции в системе:</b>\n\n"
        
        for op_id, op_config in OPERATIONS_CONFIG.items():
            emoji = op_config.get('emoji', '📊')
            name = op_config['name']
            rate = op_config['rate']
            text += f"{emoji} <b>{op_id}.</b> {name}\n    <i>{rate}</i>\n\n"
        
        # Разделяем на части если слишком длинное
        max_length = 4000
        if len(text) > max_length:
            parts = []
            current = ""
            lines = text.split('\n\n')
            
            for line in lines:
                if len(current + line + '\n\n') > max_length:
                    if current:
                        parts.append(current.strip())
                        current = line + '\n\n'
                    else:
                        parts.append(line)
                else:
                    current += line + '\n\n'
            
            if current:
                parts.append(current.strip())
            
            for i, part in enumerate(parts):
                if i == 0:
                    part = "📊 <b>Операции (часть 1):</b>\n\n" + part
                else:
                    part = f"📊 <b>Операции (часть {i+1}):</b>\n\n" + part
                
                # Последняя часть - с меню
                if i == len(parts) - 1:
                    await update.message.reply_text(
                        part,
                        parse_mode=ParseMode.HTML,
                        reply_markup=get_main_menu()
                    )
                else:
                    await update.message.reply_text(
                        part,
                        parse_mode=ParseMode.HTML
                    )
        else:
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
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
        
        # Добавляем кнопку отмены
        keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="cancel_calc")])
        
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
        
        if query.data == "cancel_calc":
            await query.edit_message_text(
                "❌ Расчет отменен.\n\nИспользуйте кнопку <b>🧮 Рассчитать премию</b> для нового расчета.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
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
                f"💰 Для расчета КПИ укажите размер оклада по трудовому договору (в рублях):\n\n"
                f"💡 Введите число (например: <code>30000</code>)",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_SALARY
        else:
            # Для должностей без КПИ сразу переходим к пошаговому опроснику операций
            await query.edit_message_text(
                f"✅ Выбрана должность: <b>{position_config['name']}</b>",
                parse_mode=ParseMode.HTML
            )
            
            # Инициализируем пошаговый опросник
            user_states[user_id].available_operations = get_operations_for_position(position)
            user_states[user_id].current_operation_index = 0
            
            # Переходим к первой операции
            return await self.ask_next_operation(update, context)
    
    async def salary_entered(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка введенного оклада"""
        user_id = update.effective_user.id
        
        try:
            salary = float(update.message.text.strip().replace(',', '').replace(' ', ''))
            
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
            
            # Добавляем кнопку отмены
            keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="cancel_calc")])
            
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
                "❌ Некорректный размер оклада.\n\n"
                "💡 Введите число в рублях (например: <code>30000</code>):",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_SALARY
    
    async def rate_chosen(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора размера ставки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_calc":
            await query.edit_message_text(
                "❌ Расчет отменен.\n\nИспользуйте кнопку <b>🧮 Рассчитать премию</b> для нового расчета.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        user_id = update.effective_user.id
        rate = float(query.data.replace("rate_", ""))
        
        user_states[user_id].position_rate = rate
        
        # Рассчитываем реальный оклад
        real_salary = user_states[user_id].base_salary * rate
        
        await query.edit_message_text(
            f"✅ Размер ставки: <b>{rate}</b> ({rate*100:.0f}%)\n"
            f"💰 Реальный размер оклада: <b>{format_money(real_salary)}</b>",
            parse_mode=ParseMode.HTML
        )
        
        # Инициализируем пошаговый опросник
        user_states[user_id].available_operations = get_operations_for_position(user_states[user_id].position)
        user_states[user_id].current_operation_index = 0
        
        # Переходим к первой операции
        return await self.ask_next_operation(update, context)
    
    async def ask_next_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Задать вопрос о следующей операции"""
        user_id = update.effective_user.id
        state = user_states[user_id]
        
        # Проверяем, есть ли еще операции
        if state.current_operation_index >= len(state.available_operations):
            # Все операции заданы, переходим к КПИ/коэффициентам
            return await self.move_to_kpi_or_coefficients(update, context)
        
        # Получаем текущую операцию
        current_op_id = state.available_operations[state.current_operation_index]
        operation = OPERATIONS_CONFIG[current_op_id]
        
        # Специальные кнопки для ПВЗ WB (операция #13)
        if current_op_id == 13:  # Обеспечение ПВЗ WB
            keyboard = [
                [InlineKeyboardButton("0", callback_data=f"op_{current_op_id}_0")],
                [
                    InlineKeyboardButton("100", callback_data=f"op_{current_op_id}_100"),
                    InlineKeyboardButton("250", callback_data=f"op_{current_op_id}_250"),
                    InlineKeyboardButton("500", callback_data=f"op_{current_op_id}_500")
                ],
                [
                    InlineKeyboardButton("750", callback_data=f"op_{current_op_id}_750"),
                    InlineKeyboardButton("1000", callback_data=f"op_{current_op_id}_1000"),
                    InlineKeyboardButton("1500", callback_data=f"op_{current_op_id}_1500")
                ],
                [InlineKeyboardButton("✏️ Ввести точное значение", callback_data=f"op_{current_op_id}_custom")],
                [InlineKeyboardButton("⏭️ Пропустить", callback_data=f"op_{current_op_id}_skip")],
                [InlineKeyboardButton("❌ Отменить расчет", callback_data="cancel_calc")]
            ]
        else:
            # Обычные кнопки для других операций
            keyboard = [
                [InlineKeyboardButton("0", callback_data=f"op_{current_op_id}_0")],
                [
                    InlineKeyboardButton("1", callback_data=f"op_{current_op_id}_1"),
                    InlineKeyboardButton("5", callback_data=f"op_{current_op_id}_5"),
                    InlineKeyboardButton("10", callback_data=f"op_{current_op_id}_10")
                ],
                [
                    InlineKeyboardButton("50", callback_data=f"op_{current_op_id}_50"),
                    InlineKeyboardButton("100", callback_data=f"op_{current_op_id}_100"),
                    InlineKeyboardButton("500", callback_data=f"op_{current_op_id}_500")
                ],
                [InlineKeyboardButton("✏️ Ввести точное значение", callback_data=f"op_{current_op_id}_custom")],
                [InlineKeyboardButton("⏭️ Пропустить", callback_data=f"op_{current_op_id}_skip")],
                [InlineKeyboardButton("❌ Отменить расчет", callback_data="cancel_calc")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        progress = f"({state.current_operation_index + 1}/{len(state.available_operations)})"
        
        # Специальный текст для ПВЗ WB
        if current_op_id == 13:  # Обеспечение ПВЗ WB
            text = (
                f"📊 <b>Операция {progress}:</b>\n\n"
                f"{operation.get('emoji', '📊')} <b>{operation['name']}</b>\n"
                f"💰 Ставка: <i>{operation['rate']}</i>\n"
                f"📏 Единица: <i>{operation.get('unit', '')}</i>\n\n"
                f"📋 <b>Новая система расчета ПВЗ WB:</b>\n"
                f"💰 <b>WB1</b> - премия по режиму работы:\n"
                f"• 50 и менее: 0-3000₽\n"
                f"• 51-100: 1000-3000₽\n"
                f"• 101-166: 2000-3000₽\n"
                f"• 167+: 3000₽\n\n"
                f"⭐ <b>WB2</b> - премия по рейтингу:\n"
                f"• 50 и менее: 0-4500₽\n"
                f"• 51-100: 1500-4500₽\n"
                f"• 101-166: 3000-4500₽\n"
                f"• 167+: 4500₽\n\n"
                f"🏆 <b>Итого = WB1 + WB2</b>\n\n"
                f"❓ <b>Сколько услуг ПВЗ WB оказано за месяц?</b>"
            )
        else:
            text = (
                f"📊 <b>Операция {progress}:</b>\n\n"
                f"{operation.get('emoji', '📊')} <b>{operation['name']}</b>\n"
                f"💰 Ставка: <i>{operation['rate']}</i>\n"
                f"📏 Единица: <i>{operation.get('unit', '')}</i>\n\n"
                f"❓ <b>Сколько выполнили за месяц?</b>"
            )
        
        # Обновляем или отправляем сообщение
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
        
        return ASKING_OPERATIONS
    
    async def operation_answer_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ответа на операцию"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        state = user_states[user_id]
        
        if query.data == "cancel_calc":
            await query.edit_message_text(
                "❌ Расчет отменен.\n\nИспользуйте кнопку <b>🧮 Рассчитать премию</b> для нового расчета.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Обработка цифровой клавиатуры
        if query.data.startswith('op_') and ('_digit_' in query.data or '_qty_' in query.data or '_backspace' in query.data or '_confirm' in query.data or '_text_input' in query.data):
            return await self.numeric_keyboard_handler(update, context)
        
        # Парсим данные для старого формата
        parts = query.data.split('_')
        op_id = int(parts[1])
        value_or_action = parts[2]
        
        if value_or_action == "skip":
            # Пропускаем операцию (оставляем 0)
            state.operations[op_id] = 0
            state.current_operation_index += 1
            return await self.ask_next_operation(update, context)
        
        elif value_or_action == "custom":
            # Запрашиваем цифровую клавиатуру
            return await self.ask_operation_quantity(update, context)
        
        else:
            # Быстрый выбор числового значения
            value = float(value_or_action)
            state.operations[op_id] = value
            
            return await self.process_operation_quantity(update, context, value)

    async def numeric_keyboard_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработчик цифровой клавиатуры"""
        query = update.callback_query
        await query.answer()
        
        state = context.user_data.get('calc_state')
        if not state:
            user_id = update.effective_user.id
            state = user_states[user_id]
        
        data = query.data
        
        # Парсим callback_data: op_{operation_id}_action_value
        if data.startswith('op_') and '_' in data:
            parts = data.split('_')
            if len(parts) >= 3:
                op_id = int(parts[1])
                action = parts[2]
                
                # Инициализируем current_input если его нет
                if not hasattr(state, 'current_input'):
                    state.current_input = ""
                
                if action == "digit" and len(parts) >= 4:
                    # Добавляем цифру
                    digit = parts[3]
                    if len(state.current_input) < 4:  # Ограничение длины
                        state.current_input += digit
                    
                elif action == "backspace":
                    # Удаляем последнюю цифру
                    state.current_input = state.current_input[:-1]
                    
                elif action == "qty" and len(parts) >= 4:
                    # Быстрый выбор количества
                    quantity = int(parts[3])
                    state.operations[op_id] = quantity
                    
                    # Переходим к обработке как при обычном вводе
                    return await self.process_operation_quantity(update, context, quantity)
                    
                elif action == "confirm":
                    # Подтверждаем ввод
                    try:
                        quantity = int(state.current_input) if state.current_input else 0
                        state.current_input = ""  # Очищаем ввод
                        state.operations[op_id] = quantity
                        
                        return await self.process_operation_quantity(update, context, quantity)
                    except ValueError:
                        await query.edit_message_text("❌ Некорректное число. Попробуйте снова.")
                        return ASKING_OPERATION_QUANTITY
                        
                elif action == "text" and parts[3] == "input":
                    # Переключаемся на текстовый ввод
                    current_op_id = state.available_operations[state.current_operation_index]
                    operation = OPERATIONS_CONFIG[current_op_id]
                    
                    text = (
                        f"📋 <b>Операция {state.current_operation_index + 1}/{len(state.available_operations)}</b>\n\n"
                        f"{operation['emoji']} <b>{operation['name']}</b>\n"
                        f"{operation['description']}\n\n"
                        f"🔢 <b>Введите количество числом:</b>"
                    )
                    
                    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
                    return ASKING_OPERATION_QUANTITY
                
                # Обновляем клавиатуру с новым current_input
                current_op_id = state.available_operations[state.current_operation_index]
                operation = OPERATIONS_CONFIG[current_op_id]
                
                # Сокращенное описание
                short_desc = operation['description']
                if len(short_desc) > 60:
                    short_desc = short_desc[:57] + "..."
                
                text = (
                    f"📋 <b>Операция {state.current_operation_index + 1}/{len(state.available_operations)}</b>\n\n"
                    f"{operation['emoji']} <b>{operation['name']}</b>\n"
                    f"<i>{short_desc}</i>\n\n"
                    f"📊 <b>Текущий ввод:</b> {state.current_input or '(пусто)'}\n\n"
                    f"🔢 <b>Введите количество:</b>"
                )
                
                max_val = operation.get('max_reasonable', 100)
                await query.edit_message_text(
                    text, 
                    reply_markup=self.create_numeric_keyboard(current_op_id, max_val),
                    parse_mode=ParseMode.HTML
                )
        
        return ASKING_OPERATION_QUANTITY

    async def process_operation_quantity(self, update: Update, context: ContextTypes.DEFAULT_TYPE, quantity: int) -> int:
        """Обработка введенного количества операции"""
        user_id = update.effective_user.id
        state = user_states[user_id]
        current_op_id = state.available_operations[state.current_operation_index]
        
        # Специальная обработка для ПВЗ WB
        if current_op_id == 13 and quantity > 0:
            operation = OPERATIONS_CONFIG[current_op_id]
            
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(
                    f"✅ {operation['emoji']} <b>{operation['name']}</b>: {quantity} {operation.get('unit', '')}\n\n"
                    f"📋 <b>Дополнительные параметры ПВЗ WB</b>\n\n"
                    f"⚡ <b>Выберите режим работы ПВЗ:</b>",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"✅ {operation['emoji']} <b>{operation['name']}</b>: {quantity} {operation.get('unit', '')}\n\n"
                    f"📋 <b>Дополнительные параметры ПВЗ WB</b>\n\n"
                    f"⚡ <b>Выберите режим работы ПВЗ:</b>",
                    parse_mode=ParseMode.HTML
                )
            return await self.ask_pvz_schedule(update, context)
        else:
            # Обычная обработка других операций
            operation = OPERATIONS_CONFIG[current_op_id]
            if quantity > 0:
                confirmation = f"✅ {operation['emoji']} <b>{operation['name']}</b>: {quantity} {operation.get('unit', '')}"
            else:
                confirmation = f"⚪ {operation['emoji']} <b>{operation['name']}</b>: не выполнялось"
            
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(confirmation, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(confirmation, parse_mode=ParseMode.HTML)
            
            # Переходим к следующей операции
            state.current_operation_index += 1
            
            # Небольшая задержка
            await asyncio.sleep(0.5)
            
            return await self.ask_next_operation(update, context)
    
    async def operation_entered(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка точного ввода операции в пошаговом режиме"""
        user_id = update.effective_user.id
        state = user_states[user_id]
        text = update.message.text.strip()
        
        if text == "/cancel":
            return await self.cancel(update, context)
        
        # В пошаговом режиме ожидаем только число
        try:
            quantity = float(text.replace(',', '').replace(' ', ''))
            
            if quantity < 0:
                raise ValueError("Количество не может быть отрицательным")
            
            # Получаем текущую операцию
            current_op_id = state.available_operations[state.current_operation_index]
            
            # Сохраняем значение
            state.operations[current_op_id] = quantity
            
            # Специальная обработка для ПВЗ WB
            if current_op_id == 13 and quantity > 0:
                # Для ПВЗ WB переходим к диалогу дополнительных параметров
                operation = OPERATIONS_CONFIG[current_op_id]
                
                await update.message.reply_text(
                    f"✅ {operation['emoji']} <b>{operation['name']}</b>: {quantity} {operation.get('unit', '')}\n\n"
                    f"📋 <b>Дополнительные параметры ПВЗ WB</b>\n\n"
                    f"⚡ <b>Выберите режим работы ПВЗ:</b>",
                    parse_mode=ParseMode.HTML
                )
                return await self.ask_pvz_schedule(update, context)
            else:
                # Обычная обработка других операций
                operation = OPERATIONS_CONFIG[current_op_id]
                if quantity > 0:
                    confirmation = f"✅ {operation['emoji']} <b>{operation['name']}</b>: {quantity} {operation.get('unit', '')}"
                else:
                    confirmation = f"⚪ {operation['emoji']} <b>{operation['name']}</b>: не выполнялось"
                
                await update.message.reply_text(confirmation, parse_mode=ParseMode.HTML)
                
                # Переходим к следующей операции
                state.current_operation_index += 1
                
                # Небольшая задержка
                await asyncio.sleep(0.5)
                
                return await self.ask_next_operation(update, context)
            
        except ValueError:
            await update.message.reply_text(
                f"❌ Некорректное значение.\n\n"
                f"💡 Введите число (например: <code>1500</code>):",
                parse_mode=ParseMode.HTML
            )
            return ASKING_OPERATIONS
    
    async def move_to_kpi_or_coefficients(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Переход к КПИ или коэффициентам в зависимости от должности"""
        user_id = update.effective_user.id
        position = user_states[user_id].position
        position_config = POSITIONS_CONFIG[position]
        
        # Подводим итоги пошагового опросника
        filled_ops = [(op_id, quantity) for op_id, quantity in user_states[user_id].operations.items() if quantity > 0]
        
        ops_text = f"✅ <b>Опросник завершен!</b>\n\n"
        ops_text += f"📊 <b>Операций заполнено: {len(filled_ops)} из {len(user_states[user_id].available_operations)}</b>\n\n"
        
        if filled_ops:
            ops_text += "💼 <b>Заполненные операции:</b>\n"
            for op_id, quantity in filled_ops:
                op_config = OPERATIONS_CONFIG[op_id]
                emoji = op_config.get('emoji', '📊')
                ops_text += f"{emoji} {op_config['name']}: {quantity} {op_config.get('unit', '')}\n"
        else:
            ops_text += "📊 <b>Операции:</b> не заполнены\n"
        
        ops_text += "\n"
        
        # Проверяем, нужны ли КПИ показатели
        if position_config.get('kpi'):
            # Инициализируем пошаговый КПИ опросник
            user_states[user_id].available_kpi = position_config['kpi'].copy()
            user_states[user_id].current_kpi_index = 0
            
            # Показываем краткую сводку операций
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(
                    f"{ops_text}"
                    f"⭐ <b>Переходим к КПИ показателям...</b>",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"{ops_text}"
                    f"⭐ <b>Переходим к КПИ показателям...</b>",
                    parse_mode=ParseMode.HTML
                )
            
            # Переходим к первому КПИ
            return await self.ask_next_kpi(update, context)
    
    async def ask_next_kpi(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Задать вопрос о следующем КПИ показателе"""
        print(f"[DEBUG] ask_next_kpi triggered")
        
        user_id = update.effective_user.id
        state = user_states[user_id]
        
        print(f"[DEBUG] User {user_id}, Current KPI index: {state.current_kpi_index}, Available KPI: {len(state.available_kpi)}")
        
        # Проверяем, есть ли еще КПИ
        if state.current_kpi_index >= len(state.available_kpi):
            # Все КПИ заданы, переходим к коэффициентам или результатам
            print(f"[DEBUG] All KPIs completed, moving to next stage")
            return await self.move_to_coefficients_or_results(update, context)
        
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
            [InlineKeyboardButton("✏️ Ввести точное значение", callback_data=f"kpi_{current_kpi_id}_custom")],
            [InlineKeyboardButton("⏭️ Пропустить", callback_data=f"kpi_{current_kpi_id}_skip")],
            [InlineKeyboardButton("❌ Отменить расчет", callback_data="cancel_calc")]
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
    
    async def move_to_coefficients_or_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Переход к коэффициентам или результатам после КПИ"""
        print(f"[DEBUG] move_to_coefficients_or_results triggered")
        
        user_id = update.effective_user.id
        position = user_states[user_id].position
        position_config = POSITIONS_CONFIG[position]
        
        # Подводим итог КПИ
        filled_kpi = [(kpi_id, value) for kpi_id, value in user_states[user_id].kpi.items() if value > 0]
        
        kpi_text = f"✅ <b>КПИ завершено!</b>\n\n"
        kpi_text += f"⭐ <b>КПИ заполнено: {len(filled_kpi)} из {len(user_states[user_id].available_kpi)}</b>\n\n"
        
        if filled_kpi:
            kpi_text += "⭐ <b>Заполненные КПИ:</b>\n"
            for kpi_id, value in filled_kpi:
                kpi_config = KPI_CONFIG[kpi_id]
                emoji = kpi_config.get('emoji', '⭐')
                kpi_text += f"{emoji} {kpi_config['name']}: {value}%\n"
        else:
            kpi_text += "⭐ <b>КПИ:</b> не заполнены\n"
        
        kpi_text += "\n"
        
        # Проверяем, нужны ли командные коэффициенты
        if position_config.get('teamCoefficients'):
            return await self.ask_coefficients_with_buttons(update, context, kpi_text)
        
        else:
            # Для должностей без КПИ и коэффициентов показываем кнопку расчета
            keyboard = [
                [InlineKeyboardButton("🧮 РАССЧИТАТЬ ПРЕМИЮ", callback_data="final_calculate")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Определяем откуда пришли (callback query или сообщение)
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(
                    f"{kpi_text}"
                    f"🎯 <b>Все данные собраны!</b>\n\n"
                    f"💡 Нажмите кнопку для расчета премии:",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"{kpi_text}"
                    f"🎯 <b>Все данные собраны!</b>\n\n"
                    f"💡 Нажмите кнопку для расчета премии:",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            return SHOWING_RESULTS
    
    async def ask_coefficients_with_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE, kpi_text: str) -> int:
        """Задать вопросы о коэффициентах с интерактивными кнопками"""
        user_id = update.effective_user.id
        position_config = POSITIONS_CONFIG[user_states[user_id].position]
        team_coefficients = position_config.get('teamCoefficients', [])
        
        # Инициализируем состояние для коэффициентов
        if not hasattr(user_states[user_id], 'current_coefficient_index'):
            user_states[user_id].current_coefficient_index = 0
            user_states[user_id].available_coefficients = team_coefficients
        
        # Проверяем, есть ли еще коэффициенты
        if user_states[user_id].current_coefficient_index >= len(team_coefficients):
            # Все коэффициенты заданы, переходим к результатам
            keyboard = [
                [InlineKeyboardButton("🧮 РАССЧИТАТЬ ПРЕМИЮ", callback_data="final_calculate")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = f"✅ <b>Все коэффициенты заданы!</b>\n\n💡 Нажмите кнопку для расчета премии:"
            
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(
                    text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
                )
            return SHOWING_RESULTS
        
        # Получаем текущий коэффициент
        current_coeff_id = team_coefficients[user_states[user_id].current_coefficient_index]
        coeff_config = TEAM_COEFFICIENTS_CONFIG[current_coeff_id]
        
        progress = f"({user_states[user_id].current_coefficient_index + 1}/{len(team_coefficients)})"
        
        # Специальная обработка для коэффициентов скорости
        if current_coeff_id in ['speed_reception', 'speed_delivery']:
            if current_coeff_id == 'speed_reception':
                keyboard = [
                    [InlineKeyboardButton("✅ Выполнено (< 4 мин)", callback_data=f"coeff_{current_coeff_id}_1.5")],
                    [InlineKeyboardButton("❌ Не выполнено (> 4 мин)", callback_data=f"coeff_{current_coeff_id}_0.5")],
                    [InlineKeyboardButton("⚪ Не применимо", callback_data=f"coeff_{current_coeff_id}_1.0")],
                    [InlineKeyboardButton("⏭️ Пропустить", callback_data=f"coeff_{current_coeff_id}_skip")]
                ]
                speed_text = "< 4 мин = выполнено, > 4 мин = не выполнено"
            else:  # speed_delivery
                keyboard = [
                    [InlineKeyboardButton("✅ Выполнено (< 1:30 мин)", callback_data=f"coeff_{current_coeff_id}_1.5")],
                    [InlineKeyboardButton("❌ Не выполнено (> 1:30 мин)", callback_data=f"coeff_{current_coeff_id}_0.5")],
                    [InlineKeyboardButton("⚪ Не применимо", callback_data=f"coeff_{current_coeff_id}_1.0")],
                    [InlineKeyboardButton("⏭️ Пропустить", callback_data=f"coeff_{current_coeff_id}_skip")]
                ]
                speed_text = "< 1:30 мин = выполнено, > 1:30 мин = не выполнено"
            
            text = (
                f"⚡ <b>Коэффициент {progress}:</b>\n\n"
                f"{coeff_config['emoji']} <b>{coeff_config['name']}</b>\n"
                f"📏 Норма: {speed_text}\n\n"
                f"❓ <b>Выберите результат по скорости:</b>"
            )
            
        elif current_coeff_id == 'service':
            # Обычные кнопки для CSI
            keyboard = [
                [
                    InlineKeyboardButton("85", callback_data=f"coeff_{current_coeff_id}_85"),
                    InlineKeyboardButton("90", callback_data=f"coeff_{current_coeff_id}_90"),
                    InlineKeyboardButton("95", callback_data=f"coeff_{current_coeff_id}_95")
                ],
                [
                    InlineKeyboardButton("100", callback_data=f"coeff_{current_coeff_id}_100"),
                    InlineKeyboardButton("✏️ Точно", callback_data=f"coeff_{current_coeff_id}_custom")
                ],
                [InlineKeyboardButton("⏭️ Пропустить", callback_data=f"coeff_{current_coeff_id}_skip")]
            ]
            text = (
                f"⭐ <b>Коэффициент {progress}:</b>\n\n"
                f"{coeff_config['emoji']} <b>{coeff_config['name']}</b>\n"
                f"📏 Влияет на операции типа 2\n\n"
                f"❓ <b>Укажите количество баллов CSI:</b>"
            )
            
        elif current_coeff_id == 'efficiency':
            # Кнопки для эффективности
            keyboard = [
                [
                    InlineKeyboardButton("95%", callback_data=f"coeff_{current_coeff_id}_95"),
                    InlineKeyboardButton("100%", callback_data=f"coeff_{current_coeff_id}_100"),
                    InlineKeyboardButton("105%", callback_data=f"coeff_{current_coeff_id}_105")
                ],
                [
                    InlineKeyboardButton("110%", callback_data=f"coeff_{current_coeff_id}_110"),
                    InlineKeyboardButton("✏️ Точно", callback_data=f"coeff_{current_coeff_id}_custom")
                ],
                [InlineKeyboardButton("⏭️ Пропустить", callback_data=f"coeff_{current_coeff_id}_skip")]
            ]
            text = (
                f"📈 <b>Коэффициент {progress}:</b>\n\n"
                f"{coeff_config['emoji']} <b>{coeff_config['name']}</b>\n"
                f"📏 Влияет на итоговую премию\n\n"
                f"❓ <b>Укажите процент выполнения плана выручки:</b>"
            )
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Определяем откуда пришли
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
        
        return ASKING_COEFFICIENTS  # Новое состояние
    
    async def coefficient_answer_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ответа на коэффициент через кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        state = user_states[user_id]
        
        if query.data == "cancel_calc":
            await query.edit_message_text(
                "❌ Расчет отменен.\n\nИспользуйте кнопку <b>🧮 Рассчитать премию</b> для нового расчета.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Парсим данные: coeff_{coefficient_id}_{value}
        parts = query.data.split('_')
        if len(parts) < 3:
            return ASKING_COEFFICIENTS
        
        coeff_id = '_'.join(parts[1:-1])  # Все элементы между 'coeff' и value
        value_or_action = parts[-1]
        
        if value_or_action == "skip":
            # Пропускаем коэффициент (оставляем 1.0 - базовый)
            state.team_coefficients[coeff_id] = 1.0
            state.current_coefficient_index += 1
            return await self.ask_coefficients_with_buttons(update, context, "")
        
        elif value_or_action == "custom":
            # Запрашиваем точный ввод
            coeff_config = TEAM_COEFFICIENTS_CONFIG[coeff_id]
            await query.edit_message_text(
                f"✏️ <b>Точный ввод коэффициента</b>\n\n"
                f"Введите значение для:\n"
                f"{coeff_config['emoji']} <b>{coeff_config['name']}</b>\n\n"
                f"💡 Введите число (например: <code>92</code> для CSI или <code>105</code> для эффективности):",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_COEFFICIENTS  # Переходим к текстовому вводу
        
        else:
            # Быстрый выбор значения
            try:
                if coeff_id in ['speed_reception', 'speed_delivery']:
                    # Для коэффициентов скорости сохраняем прямое значение коэффициента
                    coefficient_value = float(value_or_action)
                    state.team_coefficients[coeff_id] = coefficient_value
                else:
                    # Для остальных сохраняем введенное значение (будет преобразовано в калькуляторе)
                    raw_value = float(value_or_action)
                    state.team_coefficients[coeff_id] = raw_value
                
                # Показываем подтверждение
                coeff_config = TEAM_COEFFICIENTS_CONFIG[coeff_id]
                if coeff_id in ['speed_reception', 'speed_delivery']:
                    # Для скорости показываем результат
                    if coefficient_value == 1.5:
                        result_text = "✅ Выполнено"
                    elif coefficient_value == 0.5:
                        result_text = "❌ Не выполнено"
                    else:
                        result_text = "⚪ Не применимо"
                    confirmation = f"✅ {coeff_config['emoji']} <b>{coeff_config['name']}</b>: {result_text}"
                else:
                    # Для остальных показываем значение
                    if coeff_id == 'efficiency':
                        confirmation = f"✅ {coeff_config['emoji']} <b>{coeff_config['name']}</b>: {raw_value}%"
                    else:
                        confirmation = f"✅ {coeff_config['emoji']} <b>{coeff_config['name']}</b>: {raw_value}"
                
                await query.edit_message_text(confirmation, parse_mode=ParseMode.HTML)
                
                # Переходим к следующему коэффициенту
                state.current_coefficient_index += 1
                
                # Небольшая задержка
                await asyncio.sleep(0.5)
                
                return await self.ask_coefficients_with_buttons(update, context, "")
                
            except ValueError:
                return ASKING_COEFFICIENTS
    
    async def kpi_answer_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ответа на КПИ показатель"""
        print(f"[DEBUG] kpi_answer_received triggered")
        
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        state = user_states[user_id]
        
        print(f"[DEBUG] User {user_id}, callback data: {query.data}")
        print(f"[DEBUG] Current KPI index: {state.current_kpi_index}, Available KPI: {len(state.available_kpi)}")
        
        if query.data == "cancel_calc":
            await query.edit_message_text(
                "❌ Расчет отменен.\n\nИспользуйте кнопку <b>🧮 Рассчитать премию</b> для нового расчета.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Парсим данные с учетом что ID может содержать символы подчеркивания
        parts = query.data.split('_')
        print(f"[DEBUG] Parsed parts: {parts}")
        
        if len(parts) < 3:
            print(f"[ERROR] Invalid callback data format: {query.data}")
            return ASKING_KPI
        
        # Правильно извлекаем kpi_id и value - последний элемент это value
        value_or_action = parts[-1]  # Последний элемент - это action/value
        kpi_id = '_'.join(parts[1:-1])  # Все элементы между 'kpi' и value
        
        print(f"[DEBUG] KPI ID: {kpi_id}, Action/Value: {value_or_action}")
        
        if value_or_action == "skip":
            # Пропускаем КПИ (оставляем 0)
            print(f"[DEBUG] Skipping KPI {kpi_id}")
            state.kpi[kpi_id] = 0
            state.current_kpi_index += 1
            print(f"[DEBUG] New KPI index: {state.current_kpi_index}")
            return await self.ask_next_kpi(update, context)
        
        elif value_or_action == "custom":
            # Запрашиваем ввод точного значения
            print(f"[DEBUG] Custom input for KPI {kpi_id}")
            await query.edit_message_text(
                f"✏️ <b>Точный ввод КПИ</b>\n\n"
                f"Введите процент для КПИ:\n"
                f"{KPI_CONFIG[kpi_id]['emoji']} <b>{KPI_CONFIG[kpi_id]['name']}</b>\n\n"
                f"💡 Введите число (например: <code>85</code>):",
                parse_mode=ParseMode.HTML
            )
            return ASKING_KPI  # Остаемся в том же состоянии для обработки текстового ввода
        
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
    
    async def kpi_entered(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка точного ввода КПИ в пошаговом режиме"""
        print(f"[DEBUG] kpi_entered triggered")
        
        user_id = update.effective_user.id
        state = user_states[user_id]
        text = update.message.text.strip()
        
        print(f"[DEBUG] User {user_id}, input text: {text}")
        
        if text == "/cancel":
            return await self.cancel(update, context)
        
        # В пошаговом режиме ожидаем только число
        try:
            percent = float(text.replace(',', '').replace(' ', ''))
            
            if percent < 0 or percent > 200:
                raise ValueError("Процент должен быть от 0 до 200")
            
            # Получаем текущий КПИ
            current_kpi_id = state.available_kpi[state.current_kpi_index]
            
            print(f"[DEBUG] Setting KPI {current_kpi_id} = {percent}% (manual input)")
            
            # Сохраняем значение
            state.kpi[current_kpi_id] = percent
            
            # Показываем подтверждение
            kpi_config = KPI_CONFIG[current_kpi_id]
            if percent > 0:
                confirmation = f"✅ {kpi_config['emoji']} <b>{kpi_config['name']}</b>: {percent}%"
            else:
                confirmation = f"⚪ {kpi_config['emoji']} <b>{kpi_config['name']}</b>: не заполнено"
            
            await update.message.reply_text(confirmation, parse_mode=ParseMode.HTML)
            
            # Переходим к следующему КПИ
            state.current_kpi_index += 1
            print(f"[DEBUG] Moving to next KPI, new index: {state.current_kpi_index}")
            
            # Небольшая задержка
            await asyncio.sleep(0.5)
            
            return await self.ask_next_kpi(update, context)
            
        except ValueError:
            await update.message.reply_text(
                f"❌ Некорректное значение.\n\n"
                f"💡 Введите число от 0 до 200 (например: <code>85</code>):",
                parse_mode=ParseMode.HTML
            )
            return ASKING_KPI
    
    async def coefficient_entered(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка введенного коэффициента (текстовый ввод для точных значений)"""
        user_id = update.effective_user.id
        state = user_states[user_id]
        text = update.message.text.strip()
        
        if text == "/cancel":
            return await self.cancel(update, context)
        
        try:
            # В новой системе ожидаем только число (для точного ввода после "custom")
            value = float(text.replace(',', '').replace(' ', ''))
            
            # Получаем текущий коэффициент
            current_coeff_id = state.available_coefficients[state.current_coefficient_index]
            
            if current_coeff_id in ['speed_reception', 'speed_delivery']:
                # Для коэффициентов скорости преобразуем время в коэффициент
                if current_coeff_id == 'speed_reception':
                    coefficient_value = 1.5 if value < 4 else 0.5
                else:  # speed_delivery
                    coefficient_value = 1.5 if value < 1.5 else 0.5
                state.team_coefficients[current_coeff_id] = coefficient_value
            else:
                # Для остальных сохраняем введенное значение
                if value < 0 or value > 200:
                    raise ValueError("Значение должно быть от 0 до 200")
                state.team_coefficients[current_coeff_id] = value
            
            # Показываем подтверждение
            coeff_config = TEAM_COEFFICIENTS_CONFIG[current_coeff_id]
            emoji = coeff_config.get('emoji', '📊')
            
            if current_coeff_id in ['speed_reception', 'speed_delivery']:
                result_text = "✅ Выполнено" if coefficient_value == 1.5 else "❌ Не выполнено"
                confirmation = f"✅ {emoji} <b>{coeff_config['name']}</b>: {value} мин → {result_text}"
            elif current_coeff_id == 'efficiency':
                confirmation = f"✅ {emoji} <b>{coeff_config['name']}</b>: {value}%"
            else:
                confirmation = f"✅ {emoji} <b>{coeff_config['name']}</b>: {value}"
            
            await update.message.reply_text(confirmation, parse_mode=ParseMode.HTML)
            
            # Переходим к следующему коэффициенту
            state.current_coefficient_index += 1
            
            # Небольшая задержка
            await asyncio.sleep(0.5)
            
            return await self.ask_coefficients_with_buttons(update, context, "")
            
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}\n\n"
                f"💡 Введите число (например: <code>92</code> для CSI или <code>3.5</code> для времени в минутах):",
                parse_mode=ParseMode.HTML
            )
            return ENTERING_COEFFICIENTS
    
    async def show_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показ результатов расчета"""
        user_id = update.effective_user.id
        state = user_states[user_id]
        
        try:
            # Устанавливаем параметры ПВЗ WB перед расчетом
            self.calculator.set_pvz_params(state.pvz_work_schedule, state.pvz_rating)
            
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
                
                # Показываем базовую информацию
                if result.kpi_details:
                    first_detail = result.kpi_details[0]
                    if 'base_kpi_amount' in first_detail:
                        text += f"💰 Базовая сумма КПИ (20% от оклада): <b>{format_money(first_detail['base_kpi_amount'])}</b>\n\n"
                
                for detail in result.kpi_details:
                    emoji = detail.get('emoji', '📊')
                    name = detail['name']
                    percent = detail['percent']
                    bonus = detail['bonus']
                    coeff = detail['coefficient']
                    weight = detail.get('weight', 0)
                    
                    text += f"{emoji} {name}: {format_percent(percent)} → {format_money(bonus)}\n"
                    text += f"   └ вес {weight*100:.0f}%, коэффициент {coeff:.2f}\n"
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
                [InlineKeyboardButton("🗑️ Сброс результата", callback_data="reset_result")],
                [InlineKeyboardButton("📊 Показать формулы", callback_data="show_formulas")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Определяем откуда пришли (callback query или сообщение)
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(
                    text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            
            return SHOWING_RESULTS
            
        except Exception as e:
            logger.error(f"Ошибка при расчете: {e}")
            await update.message.reply_text(
                f"❌ Ошибка при расчете премии: {str(e)}\n\n"
                f"💡 Используйте кнопку <b>🧮 Рассчитать премию</b> для повторного расчета.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
            return ConversationHandler.END
    
    async def result_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка действий в результатах"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "final_calculate":
            # Выполняем финальный расчет премии
            return await self.show_results(update, context)
        
        elif query.data == "new_calculation":
            await query.edit_message_text(
                "🔄 Начинаем новый расчет!\n\n"
                "💡 Используйте кнопку <b>🧮 Рассчитать премию</b> для расчета.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        elif query.data == "reset_result":
            # Очищаем состояние пользователя
            user_id = update.effective_user.id
            if user_id in user_states:
                del user_states[user_id]
            
            await query.edit_message_text(
                "🗑️ <b>Результат сброшен!</b>\n\n"
                "✅ Все введенные данные очищены.\n"
                "🔄 Теперь можете начать новый расчет с чистого листа.\n\n"
                "💡 Используйте кнопку <b>🧮 Рассчитать премию</b>.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        elif query.data == "main_menu":
            await query.edit_message_text(
                "🏠 Главное меню\n\n"
                "👇 Выберите действие из кнопок ниже:",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        elif query.data == "show_formulas":
            formulas_text = (
                "📐 <b>Формулы расчета:</b>\n\n"
                "<b>КПИ бонус (v2.4):</b>\n"
                "<code>КПИ = (оклад × ставка) × коэффициент_КПИ</code>\n\n"
                "<b>Операции с коэффициентами:</b>\n"
                "• Тип 1: без коэффициентов\n"
                "• Тип 2: × коэффициент сервиса (CSI)\n"
                "• Тип 3: × коэффициент скорости приема\n"
                "• Тип 4: × коэффициент скорости вручения\n\n"
                "<b>Коэффициент эффективности:</b>\n"
                "При выручке ≥100%: +30% к операционной премии\n\n"
                "<b>Критическое правило:</b>\n"
                "Выручка &lt;80% → КПИ = 0₽"
            )
            
            # Кнопки для возврата
            keyboard = [
                [InlineKeyboardButton("🔙 Назад к результату", callback_data="back_to_result")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                formulas_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
            return SHOWING_RESULTS
        
        elif query.data == "back_to_result":
            await query.edit_message_text(
                "🔙 Вернитесь к результатам расчета выше.\n\n"
                "💡 Используйте кнопки для навигации:",
                parse_mode=ParseMode.HTML
            )
            return SHOWING_RESULTS
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена текущего расчета"""
        user_id = update.effective_user.id
        if user_id in user_states:
            del user_states[user_id]
        
        await update.message.reply_text(
            "❌ Расчет отменен.\n\n"
            "💡 Используйте кнопку <b>🧮 Рассчитать премию</b> для нового расчета.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

    async def ask_pvz_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Запрос режима работы ПВЗ WB"""
        keyboard = [
            [
                InlineKeyboardButton("🕐 Режим 1: 7 дней, 11 часов", callback_data="pvz_schedule_режим1"),
                InlineKeyboardButton("🕕 Режим 2: 5 дней, 6 часов", callback_data="pvz_schedule_режим2")
            ],
            [
                InlineKeyboardButton("⚡ Полное соответствие", callback_data="pvz_schedule_полный"),
                InlineKeyboardButton("❌ Несоответствие", callback_data="pvz_schedule_несоответствие")
            ],
            [InlineKeyboardButton("🚫 Отмена", callback_data="cancel_calc")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "⚡ <b>Режим работы ПВЗ WB:</b>\n\n"
            "🕐 <b>Режим 1:</b> 7 дней в неделю, по 11 часов\n"
            "🕕 <b>Режим 2:</b> не менее 5 дней в неделю, по 6 часов, окончание не раньше 20:00\n"
            "⚡ <b>Полное соответствие:</b> соответствие обоим плановым режимам\n"
            "❌ <b>Несоответствие:</b> не соответствует плановым режимам\n\n"
            "❓ <b>Выберите ваш режим работы:</b>"
        )
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
        
        return ASKING_PVZ_SCHEDULE
    
    async def pvz_schedule_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора режима работы ПВЗ WB"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        state = user_states[user_id]
        
        if query.data == "cancel_calc":
            await query.edit_message_text(
                "❌ Расчет отменен.\n\nИспользуйте кнопку <b>🧮 Рассчитать премию</b> для нового расчета.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Парсим данные
        parts = query.data.split('_')
        if len(parts) >= 3:
            schedule = parts[2]  # режим1, режим2, полный, несоответствие
            state.pvz_work_schedule = schedule
            
            # Переходим к выбору рейтинга
            await query.edit_message_text(
                f"✅ <b>Режим работы:</b> {schedule}\n\n"
                f"⭐ <b>Переходим к рейтингу ПВЗ WB...</b>",
                parse_mode=ParseMode.HTML
            )
            
            await asyncio.sleep(0.5)
            
            # Показываем диалог рейтинга
            return await self.show_pvz_rating_dialog(query)
        
        return ASKING_PVZ_SCHEDULE
    
    async def show_pvz_rating_dialog(self, query) -> int:
        """Показать диалог выбора рейтинга ПВЗ WB"""
        keyboard = [
            [
                InlineKeyboardButton("⭐⭐⭐⭐⭐ Рейтинг = 5.0", callback_data="pvz_rating_5.0"),
                InlineKeyboardButton("⭐⭐⭐⭐ Рейтинг 4.9-4.99", callback_data="pvz_rating_4.9")
            ],
            [
                InlineKeyboardButton("⚠️ Рейтинг отсутствовал", callback_data="pvz_rating_0.1"),
                InlineKeyboardButton("❌ Рейтинг < 4.9", callback_data="pvz_rating_0")
            ],
            [InlineKeyboardButton("🚫 Отмена", callback_data="cancel_calc")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "⭐ <b>Рейтинг ПВЗ WB:</b>\n\n"
            "⭐⭐⭐⭐⭐ <b>Рейтинг = 5.0</b>\n"
            "⭐⭐⭐⭐ <b>4.9 ≤ Рейтинг &lt; 5.0</b>\n"
            "⚠️ <b>Рейтинг отсутствовал</b>\n"
            "❌ <b>Рейтинг &lt; 4.9 или отсутствовал</b>\n\n"
            "❓ <b>Выберите ваш рейтинг ПВЗ WB:</b>"
        )
        
        await query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )
        
        return ASKING_PVZ_RATING
    
    async def ask_pvz_rating(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Запрос рейтинга ПВЗ WB (fallback метод)"""
        if hasattr(update, 'callback_query') and update.callback_query:
            return await self.show_pvz_rating_dialog(update.callback_query)
        else:
            # Для текстовых сообщений создаем новое сообщение
            keyboard = [
                [
                    InlineKeyboardButton("⭐⭐⭐⭐⭐ Рейтинг = 5.0", callback_data="pvz_rating_5.0"),
                    InlineKeyboardButton("⭐⭐⭐⭐ Рейтинг 4.9-4.99", callback_data="pvz_rating_4.9")
                ],
                [
                    InlineKeyboardButton("⚠️ Рейтинг отсутствовал", callback_data="pvz_rating_0.1"),
                    InlineKeyboardButton("❌ Рейтинг < 4.9", callback_data="pvz_rating_0")
                ],
                [InlineKeyboardButton("🚫 Отмена", callback_data="cancel_calc")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                "⭐ <b>Рейтинг ПВЗ WB:</b>\n\n"
                "⭐⭐⭐⭐⭐ <b>Рейтинг = 5.0</b>\n"
                "⭐⭐⭐⭐ <b>4.9 ≤ Рейтинг &lt; 5.0</b>\n"
                "⚠️ <b>Рейтинг отсутствовал</b>\n"
                "❌ <b>Рейтинг &lt; 4.9 или отсутствовал</b>\n\n"
                "❓ <b>Выберите ваш рейтинг ПВЗ WB:</b>"
            )
            
            await update.message.reply_text(
                text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
            
            return ASKING_PVZ_RATING
    
    async def pvz_rating_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора рейтинга ПВЗ WB"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        state = user_states[user_id]
        
        if query.data == "cancel_calc":
            await query.edit_message_text(
                "❌ Расчет отменен.\n\nИспользуйте кнопку <b>🧮 Рассчитать премию</b> для нового расчета.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Парсим данные
        parts = query.data.split('_')
        if len(parts) >= 3:
            rating = float(parts[2])
            state.pvz_rating = rating
            
            # Рассчитываем финальную премию за ПВЗ WB
            from calculator_v2 import PremiumCalculator, format_money
            calculator = PremiumCalculator()
            quantity = int(state.operations[13])
            pvz_bonus = calculator.calculate_pvz_wb_bonus(quantity, state.pvz_work_schedule, state.pvz_rating)
            
            # Показываем итоговый расчет ПВЗ WB
            rating_text = {
                5.0: "⭐⭐⭐⭐⭐ Рейтинг = 5.0",
                4.9: "⭐⭐⭐⭐ Рейтинг 4.9-4.99", 
                0.1: "⚠️ Рейтинг отсутствовал",
                0: "❌ Рейтинг < 4.9"
            }.get(rating, f"Рейтинг: {rating}")
            
            schedule_text = {
                "режим1": "🕐 Режим 1: 7 дней, 11 часов",
                "режим2": "🕕 Режим 2: 5 дней, 6 часов", 
                "полный": "⚡ Полное соответствие",
                "несоответствие": "❌ Несоответствие"
            }.get(state.pvz_work_schedule, state.pvz_work_schedule)
            
            await query.edit_message_text(
                f"✅ <b>ПВЗ WB настроено!</b>\n\n"
                f"🏢 <b>Обеспечение ПВЗ WB:</b> {quantity} услуг\n"
                f"{schedule_text}\n"
                f"{rating_text}\n\n"
                f"💰 <b>Итого премия ПВЗ WB:</b> {format_money(pvz_bonus)}\n\n"
                f"➡️ <b>Переходим к следующей операции...</b>",
                parse_mode=ParseMode.HTML
            )
            
            # Переходим к следующей операции
            state.current_operation_index += 1
            
            await asyncio.sleep(1.0)
            return await self.ask_next_operation(update, context)
        
        return ASKING_PVZ_RATING

    def create_numeric_keyboard(self, operation_id: int, max_value: int = 50) -> InlineKeyboardMarkup:
        """Создать цифровую клавиатуру для ввода количества"""
        keyboard = []
        
        # Быстрые кнопки для популярных значений
        quick_values = [1, 5, 10, 20, 50] if max_value >= 50 else [1, 5, 10, max_value]
        quick_row = []
        for val in quick_values:
            if val <= max_value:
                quick_row.append(InlineKeyboardButton(f"{val}", callback_data=f"op_{operation_id}_qty_{val}"))
        if quick_row:
            keyboard.append(quick_row)
        
        # Цифровая клавиатура 3x3
        keyboard.extend([
            [
                InlineKeyboardButton("1", callback_data=f"op_{operation_id}_digit_1"),
                InlineKeyboardButton("2", callback_data=f"op_{operation_id}_digit_2"),
                InlineKeyboardButton("3", callback_data=f"op_{operation_id}_digit_3")
            ],
            [
                InlineKeyboardButton("4", callback_data=f"op_{operation_id}_digit_4"),
                InlineKeyboardButton("5", callback_data=f"op_{operation_id}_digit_5"),
                InlineKeyboardButton("6", callback_data=f"op_{operation_id}_digit_6")
            ],
            [
                InlineKeyboardButton("7", callback_data=f"op_{operation_id}_digit_7"),
                InlineKeyboardButton("8", callback_data=f"op_{operation_id}_digit_8"),
                InlineKeyboardButton("9", callback_data=f"op_{operation_id}_digit_9")
            ],
            [
                InlineKeyboardButton("⬅️", callback_data=f"op_{operation_id}_backspace"),
                InlineKeyboardButton("0", callback_data=f"op_{operation_id}_digit_0"),
                InlineKeyboardButton("✅", callback_data=f"op_{operation_id}_confirm")
            ]
        ])
        
        # Кнопки управления
        keyboard.extend([
            [
                InlineKeyboardButton("⚪ Не выполнялось", callback_data=f"op_{operation_id}_qty_0"),
                InlineKeyboardButton("📝 Ввести текстом", callback_data=f"op_{operation_id}_text_input")
            ],
            [
                InlineKeyboardButton("🚫 Отмена", callback_data="cancel_calc")
            ]
        ])
        
        return InlineKeyboardMarkup(keyboard)

    async def ask_operation_quantity(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Запрос количества для текущей операции с улучшенным UI"""
        user_id = update.effective_user.id
        state = user_states.get(user_id)
        if not state:
            return ConversationHandler.END
            
        current_op_id = state.available_operations[state.current_operation_index]
        operation = OPERATIONS_CONFIG[current_op_id]
        
        # Сокращенное описание для экономии места
        short_desc = operation['description']
        if len(short_desc) > 60:
            short_desc = short_desc[:57] + "..."
        
        # Создаем текст с компактным форматированием
        text = (
            f"📋 <b>Операция {state.current_operation_index + 1}/{len(state.available_operations)}</b>\n\n"
            f"{operation['emoji']} <b>{operation['name']}</b>\n"
            f"<i>{short_desc}</i>\n\n"
            f"📊 <b>Текущий ввод:</b> {getattr(state, 'current_input', '')}\n\n"
            f"🔢 <b>Введите количество:</b>"
        )
        
        # Определяем максимальное разумное значение
        max_val = operation.get('max_reasonable', 100)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                text, 
                reply_markup=self.create_numeric_keyboard(current_op_id, max_val),
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                text, 
                reply_markup=self.create_numeric_keyboard(current_op_id, max_val),
                parse_mode=ParseMode.HTML
            )
        
        return ASKING_OPERATION_QUANTITY


def main():
    """Запуск бота"""
    print(f"Запуск бота с кнопочным меню...")
    print(f"Токен: {TOKEN[:10]}...")
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    bot = CleanPremiumBot()
    
    # Создаем обработчик разговора
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("calculate", bot.calculate),
            MessageHandler(filters.TEXT & filters.Regex("^🧮 Рассчитать премию$"), bot.calculate)
        ],
        states={
            CHOOSING_POSITION: [CallbackQueryHandler(bot.position_chosen, pattern="^pos_|^cancel_calc$")],
            ENTERING_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.salary_entered)],
            ENTERING_RATE: [CallbackQueryHandler(bot.rate_chosen, pattern="^rate_|^cancel_calc$")],
            ASKING_OPERATIONS: [
                CallbackQueryHandler(bot.operation_answer_received, pattern="^op_|^cancel_calc$"),
                MessageHandler(filters.TEXT, bot.operation_entered)
            ],
            ASKING_OPERATION_QUANTITY: [
                CallbackQueryHandler(bot.numeric_keyboard_handler, pattern="^op_.*_(digit|qty|backspace|confirm|text_input)_|^cancel_calc$"),
                MessageHandler(filters.TEXT, bot.operation_entered)
            ],
            ASKING_PVZ_SCHEDULE: [CallbackQueryHandler(bot.pvz_schedule_received, pattern="^pvz_schedule_|^cancel_calc$")],
            ASKING_PVZ_RATING: [CallbackQueryHandler(bot.pvz_rating_received, pattern="^pvz_rating_|^cancel_calc$")],
            ASKING_KPI: [
                CallbackQueryHandler(bot.kpi_answer_received, pattern="^kpi_|^cancel_calc$"),
                MessageHandler(filters.TEXT, bot.kpi_entered)
            ],
            ASKING_COEFFICIENTS: [
                CallbackQueryHandler(bot.coefficient_answer_received, pattern="^coeff_|^cancel_calc$")
            ],
            ENTERING_COEFFICIENTS: [MessageHandler(filters.TEXT, bot.coefficient_entered)],
            SHOWING_RESULTS: [CallbackQueryHandler(bot.result_action, pattern="^final_calculate$|^new_calculation$|^reset_result$|^main_menu$|^show_formulas$|^back_to_result$")]
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)]
    )
    
    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^(📋 Список должностей|📊 Список операций|❓ Справка|🆘 Помощь|🗑️ Очистить расчет)$"), 
        bot.handle_menu_buttons
    ))
    
    print("🚀 Бот с кнопочным меню запущен!")
    print("📱 Доступные кнопки:")
    print("   🧮 Рассчитать премию")
    print("   📋 Список должностей")  
    print("   📊 Список операций")
    print("   ❓ Справка")
    print("   🆘 Помощь")
    print("   🗑️ Очистить расчет")
    print("\n🛑 Используйте Ctrl+C для остановки.")
    
    application.run_polling()


if __name__ == "__main__":
    main() 