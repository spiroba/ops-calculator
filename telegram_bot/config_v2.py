import os
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("Не задан TELEGRAM_BOT_TOKEN в файле .env")

# v2.4: Синхронизация с HTML калькулятором премий ОПС
# Точная копия POSITIONS_CONFIG из HTML

POSITIONS_CONFIG = {
    "operator": {
        "name": "Оператор 1-3 класса",
        "emoji": "👨‍💼",
        "operations": [1, 3, 4, 5, 6, 7, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
        "kpi": [],  # У обычных операторов НЕТ КПИ
        "teamCoefficients": ["service", "speed_reception", "speed_delivery", "efficiency"],
        "hasTeamBonus": False
    },
    "nops_operational": {
        "name": "НОПС без операторов (сам выполняет операции)",
        "emoji": "👨‍💼",
        "operations": [1, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25],
        "kpi": [],  # У НОПС без операторов НЕТ КПИ
        "teamCoefficients": ["service", "speed_reception", "speed_delivery", "efficiency"],  # Все коэффициенты вместо КПИ
        "hasTeamBonus": False
    },
    "nops_management": {
        "name": "НОПС с операторами (только руководящие функции)",
        "emoji": "👨‍✈️",
        "operations": [10, 11, 12, 13, 14, 25],
        "kpi": ["revenue", "csi", "online_rpo", "co1_co2"],
        "teamCoefficients": [],  # КПИ система вместо коэффициентов
        "hasTeamBonus": True,
        "isManagementOnly": True
    },
    "admin": {
        "name": "Администратор",
        "emoji": "👨‍💻",
        "operations": [3, 11, 16, 19, 20],
        "kpi": ["revenue", "csi", "online_rpo"],
        "teamCoefficients": ["service", "speed_reception", "speed_delivery"],
        "hasTeamBonus": False
    },
    "postman": {
        "name": "Почтальон",
        "emoji": "🚶‍♂️",
        "operations": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 25],
        "kpi": [],  # У почтальона НЕТ КПИ
        "teamCoefficients": ["service", "efficiency"],
        "hasTeamBonus": False
    },
    "chief_specialist": {
        "name": "Главный специалист по обеспечению почтовой связи",
        "emoji": "👨‍🔬",
        "operations": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
        "kpi": [],  # У главного специалиста НЕТ КПИ
        "teamCoefficients": ["service", "speed_reception", "speed_delivery", "efficiency"],
        "hasTeamBonus": False
    }
}

# Точная копия OPERATIONS_CONFIG из HTML калькулятора
OPERATIONS_CONFIG = {
    1: {"name": "Розница (товары)", "rate": "3% от суммы", "type": "percent", "value": 0.03, "unit": "₽", "operationType": 2, "emoji": "🛒", "max_reasonable": 10000, "description": "Продажа товаров в розничной торговле"},
    2: {"name": "Розница 16 ДП", "rate": "5% от суммы", "type": "percent", "value": 0.05, "unit": "₽", "operationType": 2, "emoji": "🏪", "max_reasonable": 5000, "description": "Продажа товаров по 16 дополнительным позициям"},
    3: {"name": "Лотерейные билеты", "rate": "3% от суммы", "type": "percent", "value": 0.03, "unit": "₽", "operationType": 2, "emoji": "🎲", "max_reasonable": 3000, "description": "Продажа лотерейных билетов различных видов"},
    4: {"name": "Подписка", "rate": "2% от суммы", "type": "percent", "value": 0.02, "unit": "₽", "operationType": 2, "emoji": "📰", "max_reasonable": 5000, "description": "Оформление подписки на периодические издания"},
    5: {"name": "Сим-карта тип 1", "rate": "50₽/шт", "type": "fixed", "value": 50, "unit": "шт", "operationType": 2, "emoji": "📱", "max_reasonable": 20, "description": "Продажа SIM-карт первого типа"},
    6: {"name": "Сим-карта тип 2", "rate": "30₽/шт", "type": "fixed", "value": 30, "unit": "шт", "operationType": 2, "emoji": "📲", "max_reasonable": 30, "description": "Продажа SIM-карт второго типа"},
    7: {"name": "Сим-карта тип 3", "rate": "10₽/шт", "type": "fixed", "value": 10, "unit": "шт", "operationType": 2, "emoji": "📞", "max_reasonable": 50, "description": "Продажа SIM-карт третьего типа"},
    8: {"name": "Доставка гиперлока", "rate": "50₽/шт", "type": "fixed", "value": 50, "unit": "шт", "operationType": 2, "emoji": "🔒", "max_reasonable": 20, "description": "Доставка посылок через автоматизированные ячейки"},
    9: {"name": "Платеж с МПКТ", "rate": "3₽/шт", "type": "fixed", "value": 3, "unit": "шт", "operationType": 2, "emoji": "💳", "max_reasonable": 100, "description": "Прием платежей с мобильного почтово-кассового терминала"},
    10: {"name": "Мультиподпись", "rate": "30₽/шт", "type": "fixed", "value": 30, "unit": "шт", "operationType": 2, "emoji": "✍️", "max_reasonable": 50, "description": "Оформление услуги множественной подписки"},
    11: {"name": "Привлечение пенсионера", "rate": "300₽/чел", "type": "fixed", "value": 300, "unit": "чел", "operationType": 1, "emoji": "👴", "max_reasonable": 10, "description": "Привлечение пенсионеров для получения пенсии на почте"},
    12: {"name": "Выдача WB", "rate": "5₽/заказ", "type": "fixed", "value": 5, "unit": "заказ", "operationType": 1, "emoji": "📦", "max_reasonable": 200, "description": "Выдача заказов Wildberries в ОПС"},
    13: {"name": "Обеспечение ПВЗ WB", "rate": "по таблице", "type": "formula", "value": 0, "unit": "услуга", "operationType": 1, "emoji": "🏢", "max_reasonable": 10, "description": "Организация пункта выдачи заказов Wildberries"},
    14: {"name": "Возврат клиентов с2с prof", "rate": "1000₽/клиент", "type": "fixed", "value": 1000, "unit": "клиент", "operationType": 1, "emoji": "🔄", "max_reasonable": 5, "description": "Возврат клиентов в профессиональные услуги"},
    15: {"name": "Продажа EMS", "rate": "40₽/услуга", "type": "fixed", "value": 40, "unit": "услуга", "operationType": 3, "emoji": "📨", "max_reasonable": 50, "description": "Продажа услуг экспресс-доставки EMS"},
    16: {"name": "Прием EMS предоплач.", "rate": "50₽/шт", "type": "fixed", "value": 50, "unit": "шт", "operationType": 3, "emoji": "📮", "max_reasonable": 30, "description": "Прием предоплаченных отправлений EMS"},
    17: {"name": "Прием РПО посылка", "rate": "5₽/шт", "type": "fixed", "value": 5, "unit": "шт", "operationType": 3, "emoji": "📦", "max_reasonable": 100, "description": "Прием регистрируемых почтовых отправлений - посылки"},
    18: {"name": "Прием РПО письмо", "rate": "0.5₽/шт", "type": "fixed", "value": 0.5, "unit": "шт", "operationType": 3, "emoji": "✉️", "max_reasonable": 200, "description": "Прием регистрируемых почтовых отправлений - письма"},
    19: {"name": "Прием предоплач. РПО посылка", "rate": "7₽/шт", "type": "fixed", "value": 7, "unit": "шт", "operationType": 3, "emoji": "📮", "max_reasonable": 80, "description": "Прием предоплаченных РПО - посылки"},
    20: {"name": "Прием предоплач. РПО письмо", "rate": "1₽/шт", "type": "fixed", "value": 1, "unit": "шт", "operationType": 3, "emoji": "📧", "max_reasonable": 150, "description": "Прием предоплаченных РПО - письма"},
    21: {"name": "Вручение РПО посылка", "rate": "2₽/шт", "type": "fixed", "value": 2, "unit": "шт", "operationType": 4, "emoji": "📬", "max_reasonable": 100, "description": "Вручение регистрируемых почтовых отправлений - посылки"},
    22: {"name": "Вручение EКОМ", "rate": "0.5₽/шт", "type": "fixed", "value": 0.5, "unit": "шт", "operationType": 4, "emoji": "📫", "max_reasonable": 200, "description": "Вручение отправлений электронной коммерции"},
    23: {"name": "Прием EКОМ", "rate": "0.5₽/шт", "type": "fixed", "value": 0.5, "unit": "шт", "operationType": 3, "emoji": "📪", "max_reasonable": 200, "description": "Прием отправлений электронной коммерции"},
    24: {"name": "Прочие транзакции", "rate": "0.5₽/шт", "type": "fixed", "value": 0.5, "unit": "шт", "operationType": 2, "emoji": "💳", "max_reasonable": 100, "description": "Прочие финансовые транзакции и операции"},
    25: {"name": "Участие в проектах", "rate": "10₽ (НОПС) / 13₽ (почтальон)", "type": "fixed", "value": 10, "unit": "услуга", "operationType": 1, "emoji": "🚀", "max_reasonable": 30, "description": "Участие в специальных проектах и инициативах"}
}

# КПИ конфигурация (синхронизация с HTML)
KPI_CONFIG = {
    "revenue": {"name": "КПИ Выручка ОПС", "placeholder": "% выполнения", "description": "80%+ для получения КПИ", "emoji": "💰"},
    "csi": {"name": "КПИ CSI показатель", "placeholder": "% CSI", "description": "Также влияет на коэффициент операций типа 2", "emoji": "⭐"},
    "online_rpo": {"name": "КПИ Доля онлайн-РПО", "placeholder": "% выполнения", "emoji": "🌐"},
    "co1_co2": {"name": "КПИ CO1/CO2", "placeholder": "% выполнения", "emoji": "📊"}
}

# Веса КПИ показателей по должностям (20% от оклада общая сумма КПИ)
KPI_WEIGHTS = {
    "admin": {
        "revenue": 0.30,      # 30% от общей суммы КПИ
        "csi": 0.40,          # 40% от общей суммы КПИ  
        "online_rpo": 0.30    # 30% от общей суммы КПИ
    },
    "nops_management": {
        "revenue": 0.30,      # 30% от общей суммы КПИ
        "csi": 0.40,          # 40% от общей суммы КПИ
        "online_rpo": 0.15,   # 15% от общей суммы КПИ
        "co1_co2": 0.15       # 15% от общей суммы КПИ
    }
}

# Командные коэффициенты
TEAM_COEFFICIENTS_CONFIG = {
    "service": {
        "name": "Коэффициент Сервис (CSI)",
        "placeholder": "Баллы CSI",
        "description": "Влияет на операции типа 2",
        "type": "service",
        "emoji": "⭐"
    },
    "speed_reception": {
        "name": "Коэффициент Скорость приема",
        "placeholder": "Время в минутах",
        "description": "Влияет на операции типа 3. Норма: < 4 мин = выполнено, > 4 мин = не выполнено",
        "type": "speed_reception",
        "emoji": "⚡"
    },
    "speed_delivery": {
        "name": "Коэффициент Скорость вручения",
        "placeholder": "Время в минутах",
        "description": "Влияет на операции типа 4. Норма: < 1:30 мин = выполнено, > 1:30 мин = не выполнено",
        "type": "speed_delivery",
        "emoji": "🚚"
    },
    "efficiency": {
        "name": "Коэффициент Эффективности ОПС",
        "placeholder": "% выручки",
        "description": "Влияет на итоговую премию",
        "type": "efficiency",
        "emoji": "📈"
    }
}

# Размеры ставок (новое в v2.4)
POSITION_RATES = {
    "0.3": "0.3 ставки",
    "0.4": "0.4 ставки", 
    "0.5": "0.5 ставки (полставки)",
    "0.6": "0.6 ставки",
    "0.7": "0.7 ставки",
    "0.8": "0.8 ставки",
    "0.9": "0.9 ставки",
    "1.0": "1.0 ставки (полная ставка)",
    "1.1": "1.1 ставки",
    "1.2": "1.2 ставки",
    "1.3": "1.3 ставки"
}

@dataclass
class UserState:
    """Состояние пользователя v2.4"""
    position: str = ""
    base_salary: float = 0.0  # Новое поле - размер оклада
    position_rate: float = 0.0  # Новое поле - размер ставки
    operations: Dict[int, float] = field(default_factory=dict)  # Операции по ID
    kpi: Dict[str, float] = field(default_factory=dict)
    team_coefficients: Dict[str, float] = field(default_factory=dict)
    subordinates_bonus: float = 0.0  # Для управленческого НОПС
    
    # Поля для пошагового опросника
    available_operations: List[int] = field(default_factory=list)
    current_operation_index: int = 0
    
    # Поля для пошагового КПИ опросника
    available_kpi: List[str] = field(default_factory=list)
    current_kpi_index: int = 0
    
    # Дополнительные параметры для ПВЗ WB
    pvz_work_schedule: str = "режим1"  # режим1, режим2, полный, несоответствие
    pvz_rating: float = 5.0  # рейтинг ПВЗ WB (0-5.0)

# Сообщения бота
MESSAGES = {
    "start": (
        "👋 <b>Добро пожаловать в калькулятор премий ОПС v2.4!</b>\n\n"
        "Я помогу вам рассчитать премию с учетом:\n"
        "💰 Размера оклада и ставки\n"
        "📊 Всех 25 типов операций\n"
        "⭐ КПИ показателей\n"
        "⚡ Командных коэффициентов\n\n"
        "Используйте /calculate для начала расчета"
    ),
    "help": (
        "🔍 <b>Справка по командам:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/calculate - Начать расчет премии\n"
        "/positions - Список должностей\n"
        "/operations - Список операций\n"
        "/cancel - Отменить текущий расчет\n\n"
        "🤖 Версия: v2.4 (синхронизация с HTML калькулятором)"
    ),
    "positions": (
        "👥 <b>Должности в системе:</b>\n\n"
        "👨‍💼 Оператор 1-3 класса\n"
        "👨‍💼 НОПС без операторов\n"
        "👨‍✈️ НОПС с операторами\n"
        "👨‍💻 Администратор\n"
        "🚶‍♂️ Почтальон\n"
        "👨‍🔬 Главный специалист\n\n"
        "Используйте /calculate для расчета премии"
    )
} 