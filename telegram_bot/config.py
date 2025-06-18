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

# Должности
POSITIONS = {
    "operator": {
        "name": "Оператор",
        "emoji": "👨‍💼",
        "operations": ["wb_issue", "pensioner", "retail", "lottery", "sim_card"]
    },
    "postman": {
        "name": "Почтальон", 
        "emoji": "🚶‍♂️",
        "operations": ["rpo_delivery", "ems_delivery", "wb_issue"]
    },
    "nops": {
        "name": "НОПС",
        "emoji": "👨‍💼",
        "operations": ["rpo_accept", "ems_accept", "retail", "lottery"]
    },
    "admin": {
        "name": "Администратор",
        "emoji": "👨‍💻",
        "operations": ["multisign", "other_trans", "retail"]
    },
    "chief": {
        "name": "Начальник",
        "emoji": "👨‍✈️",
        "operations": ["ems_sell", "retail", "other_trans"]
    }
}

# Типы операций
OPERATION_TYPES = {
    "type1": "Без коэффициентов",
    "type2": "С коэффициентом обслуживания",
    "type3": "С коэффициентом скорости приема",
    "type4": "С коэффициентом скорости доставки"
}

# Ставки операций
OPERATION_RATES = {
    "wb_issue": {
        "name": "Выдача WB",
        "rate": 30,
        "type": "type1",
        "emoji": "📦"
    },
    "pensioner": {
        "name": "Привлечение пенсионера",
        "rate": 500,
        "type": "type1",
        "emoji": "👴"
    },
    "retail": {
        "name": "Розничные операции",
        "rate": 0.03,
        "type": "type2",
        "emoji": "🛒"
    },
    "lottery": {
        "name": "Лотереи",
        "rate": 0.03,
        "type": "type2",
        "emoji": "🎲"
    },
    "sim_card": {
        "name": "Сим-карты",
        "rate": 30,
        "type": "type2",
        "emoji": "📱"
    },
    "multisign": {
        "name": "Мультиподпись",
        "rate": 30,
        "type": "type2",
        "emoji": "✍️"
    },
    "other_trans": {
        "name": "Прочие транзакции",
        "rate": 0.5,
        "type": "type2",
        "emoji": "💳"
    },
    "rpo_accept": {
        "name": "Прием РПО",
        "rate": 5,
        "type": "type3",
        "emoji": "📮"
    },
    "ems_accept": {
        "name": "Прием EMS",
        "rate": 50,
        "type": "type3",
        "emoji": "📨"
    },
    "ems_sell": {
        "name": "Продажа EMS",
        "rate": 40,
        "type": "type2",
        "emoji": "💼"
    },
    "rpo_delivery": {
        "name": "Вручение РПО",
        "rate": 5,
        "type": "type4",
        "emoji": "📬"
    },
    "ems_delivery": {
        "name": "Вручение EMS",
        "rate": 50,
        "type": "type4",
        "emoji": "🚚"
    }
}

# Алиас для совместимости с bot.py
OPERATIONS = OPERATION_RATES

# Коэффициенты
COEFFICIENTS = {
    "service": {
        "thresholds": [80, 90, 95],
        "coefficients": [1.0, 1.1, 1.2]
    },
    "speed_reception": {
        "thresholds": [85, 90, 95],
        "coefficients": [1.0, 1.1, 1.2]
    },
    "speed_delivery": {
        "thresholds": [85, 90, 95],
        "coefficients": [1.0, 1.1, 1.2]
    },
    "efficiency": {
        "thresholds": [100],
        "coefficients": [0.3]  # 30% от базового бонуса
    }
}

# Настройки КПИ
KPI_SETTINGS = {
    "revenue_threshold": 80,  # % от плана
    "csi_bonuses": [
        (95, 5000),  # CSI >= 95% -> +5000₽
        (90, 3000),  # CSI >= 90% -> +3000₽
        (85, 1000),  # CSI >= 85% -> +1000₽
    ],
    "speed_bonuses": [
        (95, 3000),  # Скорость >= 95% -> +3000₽
        (90, 2000),  # Скорость >= 90% -> +2000₽
        (85, 1000),  # Скорость >= 85% -> +1000₽
    ]
}

# Сообщения бота
MESSAGES = {
    "start": (
        "👋 Привет! Я бот для расчета премий ОПС.\n\n"
        "Используйте /calculate чтобы начать расчет премии\n"
        "Используйте /help для получения справки"
    ),
    "help": (
        "🔍 Справка по командам:\n\n"
        "/start - Начать работу с ботом\n"
        "/calculate - Начать расчет премии\n"
        "/cancel - Отменить текущий расчет\n\n"
        "По всем вопросам обращайтесь к руководителю"
    )
}

@dataclass
class UserState:
    """Состояние пользователя"""
    position: str = ""
    operations: Dict[str, float] = field(default_factory=dict)
    kpi: Dict[str, float] = field(default_factory=lambda: {
        "csi": 0,
        "revenue": 0,
        "speed_accept": 0,
        "speed_delivery": 0
    })
