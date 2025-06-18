from dataclasses import dataclass
from typing import Dict, Any
from config import (
    OPERATION_RATES, COEFFICIENTS, KPI_SETTINGS,
    POSITIONS, OPERATION_TYPES
)

@dataclass
class CalculationResult:
    """Результат расчета премии"""
    base_bonus: float
    kpi_bonus: float
    personal_bonus: float
    efficiency_bonus: float
    total_bonus: float
    details: Dict[str, Any]

def calculate_operation_bonus(operation_code: str, amount: float, position: str) -> float:
    """Расчет бонуса за операцию"""
    if operation_code not in OPERATION_RATES:
        return 0.0
        
    rate = OPERATION_RATES[operation_code]["rate"]
    operation_type = OPERATION_RATES[operation_code]["type"]
    
    # Применяем коэффициенты в зависимости от типа операции
    if operation_type == "type2":  # С коэффициентом обслуживания
        service_coef = COEFFICIENTS["service"]["coefficients"][0]
        return rate * amount * service_coef
    elif operation_type == "type3":  # С коэффициентом скорости приема
        speed_coef = COEFFICIENTS["speed_reception"]["coefficients"][0]
        return rate * amount * speed_coef
    elif operation_type == "type4":  # С коэффициентом скорости доставки
        speed_coef = COEFFICIENTS["speed_delivery"]["coefficients"][0]
        return rate * amount * speed_coef
    else:  # type1 - без коэффициентов
        return rate * amount

def calculate_kpi_bonus(kpi: Dict[str, float], position: str) -> float:
    """Расчет КПЭ бонуса"""
    if position not in ["nops", "admin"]:
        return 0.0
        
    revenue = kpi["revenue"]
    if revenue < KPI_SETTINGS["revenue_threshold"]:
        return 0.0
        
    # Расчет CSI бонуса
    csi = kpi["csi"]
    csi_bonus = 0.0
    for threshold, bonus in KPI_SETTINGS["csi_bonuses"]:
        if csi >= threshold:
            csi_bonus = bonus
            break
            
    # Расчет бонуса за скорость приема
    speed_accept = kpi["speed_accept"]
    speed_accept_bonus = 0.0
    for threshold, bonus in KPI_SETTINGS["speed_bonuses"]:
        if speed_accept >= threshold:
            speed_accept_bonus = bonus
            break
            
    # Расчет бонуса за скорость доставки
    speed_delivery = kpi["speed_delivery"]
    speed_delivery_bonus = 0.0
    for threshold, bonus in KPI_SETTINGS["speed_bonuses"]:
        if speed_delivery >= threshold:
            speed_delivery_bonus = bonus
            break
            
    return csi_bonus + speed_accept_bonus + speed_delivery_bonus

def calculate_efficiency_bonus(base_bonus: float, position: str) -> float:
    """Расчет бонуса за эффективность"""
    if position in ["nops", "admin"]:
        return 0.0
        
    efficiency_coef = COEFFICIENTS["efficiency"]["coefficients"][0]
    return base_bonus * efficiency_coef

def calculate_bonus(user_state: 'UserState') -> Dict[str, Any]:
    """Основная функция расчета премии"""
    # Расчет базового бонуса за операции
    base_bonus = sum(
        calculate_operation_bonus(code, amount, user_state.position)
        for code, amount in user_state.operations.items()
    )
    
    # Расчет КПЭ бонуса
    kpi_bonus = calculate_kpi_bonus(user_state.kpi, user_state.position)
    
    # Расчет бонуса за эффективность
    efficiency_bonus = calculate_efficiency_bonus(base_bonus, user_state.position)
    
    # Личные бонусы всегда выплачиваются
    personal_bonus = base_bonus
    
    # Итоговая премия
    total_bonus = personal_bonus + kpi_bonus + efficiency_bonus
    
    return {
        "base_bonus": round(base_bonus, 2),
        "kpi_bonus": round(kpi_bonus, 2),
        "personal_bonus": round(personal_bonus, 2),
        "efficiency_bonus": round(efficiency_bonus, 2),
        "total_bonus": round(total_bonus, 2),
        "details": {
            "position": POSITIONS[user_state.position],
            "operations": user_state.operations,
            "kpi": user_state.kpi
        }
    } 