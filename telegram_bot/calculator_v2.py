"""
Модуль расчета премий v2.4
Синхронизирован с HTML калькулятором премий ОПС
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from config_v2 import OPERATIONS_CONFIG, POSITIONS_CONFIG, KPI_CONFIG, KPI_WEIGHTS

@dataclass
class CalculationResult:
    """Результат расчета премии"""
    total_premium: float
    operation_bonus: float
    kpi_bonus: float
    base_salary: float
    position_rate: float
    real_salary: float
    operation_details: List[Dict]
    kpi_details: List[Dict]
    warnings: List[str]
    position_name: str

class PremiumCalculator:
    """Калькулятор премий v2.4"""
    
    def __init__(self):
        # Параметры для ПВЗ WB (устанавливаются через set_pvz_params)
        self._pvz_work_schedule = "режим1"
        self._pvz_rating = 5.0
    
    def set_pvz_params(self, work_schedule: str = "режим1", rating: float = 5.0):
        """Установить параметры для расчета ПВЗ WB"""
        self._pvz_work_schedule = work_schedule
        self._pvz_rating = rating
    
    def calculate_kpi_coefficient(self, percent: float, kpi_type: str) -> float:
        """Расчет коэффициента КПИ (синхронизация с HTML)"""
        if kpi_type == 'revenue':
            if percent >= 110: return 1.0
            elif percent >= 105: return 0.8
            elif percent >= 100: return 0.6
            elif percent >= 95: return 0.4
            elif percent >= 90: return 0.2
            elif percent >= 85: return 0.1
            elif percent >= 80: return 0.05
            else: return 0.0
        
        elif kpi_type == 'csi':
            if percent >= 95: return 1.0
            elif percent >= 90: return 0.6
            elif percent >= 85: return 0.2
            else: return 0.0
        
        elif kpi_type in ['online_rpo', 'co1_co2']:
            if percent >= 110: return 1.0
            elif percent >= 105: return 0.8
            elif percent >= 100: return 0.6
            elif percent >= 95: return 0.4
            elif percent >= 90: return 0.2
            elif percent >= 85: return 0.1
            else: return 0.0
        
        return 0.0
    
    def calculate_team_coefficient(self, value: float, coeff_type: str) -> float:
        """Расчет командных коэффициентов (синхронизация с HTML)"""
        if coeff_type == 'service':
            if value >= 95: return 1.2
            elif value >= 90: return 1.1
            elif value >= 80: return 1.0
            else: return 1.0
        
        elif coeff_type == 'speed_reception':
            # Норма: < 4 мин = выполнено (1.5), > 4 мин = не выполнено (0.5)
            if value == 0: return 1.0  # Если не указано время, базовый коэффициент
            if value < 4: return 1.5   # Меньше 4 минут - выполнено
            return 0.5                 # Больше 4 минут - не выполнено
        
        elif coeff_type == 'speed_delivery':
            # Норма: < 1:30 мин (1.5 мин) = выполнено (1.5), > 1:30 мин = не выполнено (0.5)
            if value == 0: return 1.0  # Если не указано время, базовый коэффициент
            if value < 1.5: return 1.5 # Меньше 1:30 минут - выполнено
            return 0.5                 # Больше 1:30 минут - не выполнено
        
        elif coeff_type == 'efficiency':
            if value >= 100: return 0.3  # 30% бонус к итоговой премии
            else: return 0.0
        
        return 1.0
    
    def calculate_pvz_wb_bonus(self, quantity: int, work_schedule: str = "режим1", rating: float = 5.0) -> float:
        """Расчет бонуса за обеспечение ПВЗ WB (операция #13) согласно новой таблице"""
        if quantity <= 0:
            return 0.0
        
        # Определяем диапазон количества заказов
        if quantity <= 50:
            range_index = 0
        elif quantity <= 100:
            range_index = 1
        elif quantity <= 166:
            range_index = 2
        else:  # 167 и более
            range_index = 3
        
        # WB1 - Суммы по плановым режимам
        wb1_amounts = [
            [0, 1000, 2000, 3000],      # 50 и менее
            [1000, 2000, 3000, 3000],   # 51-100
            [2000, 3000, 3000, 3000],   # 101-166
            [3000, 3000, 3000, 3000]    # 167 и более
        ]
        
        # WB2 - Суммы по рейтингу ПВЗ
        wb2_amounts = [
            [0, 1500, 3000, 4500],      # 50 и менее
            [1500, 3000, 4500, 4500],   # 51-100
            [3000, 4500, 4500, 4500],   # 101-166
            [4500, 4500, 4500, 4500]    # 167 и более
        ]
        
        # Определяем режим работы для WB1
        schedule_index = 0  # По умолчанию несоответствие режимам
        
        if work_schedule == "режим1":  # 7 дней в неделю, по 11 часов
            schedule_index = 1
        elif work_schedule == "режим2":  # не менее 5 дней, по 6 часов, до 20:00
            schedule_index = 2
        elif work_schedule == "полный":  # соответствие обоим режимам
            schedule_index = 3
        
        # Расчет WB1 (по плановым режимам)
        wb1_bonus = wb1_amounts[range_index][schedule_index]
        
        # Расчет WB2 (по рейтингу)
        wb2_bonus = 0
        rating_index = 0  # По умолчанию рейтинг < 4.9
        
        if rating >= 5.0:
            rating_index = 3  # Рейтинг = 5.0
        elif rating >= 4.9:
            rating_index = 2  # 4.9 ≤ Рейтинг < 5.0
        elif rating > 0:
            rating_index = 1  # Рейтинг отсутствовал
        
        wb2_bonus = wb2_amounts[range_index][rating_index]
        
        # Общая премия = WB1 + WB2
        return float(wb1_bonus + wb2_bonus)
    
    def calculate_operations_bonus(
        self, 
        operations: Dict[int, float], 
        position_config: Dict,
        team_coefficients: Dict[str, float]
    ) -> Tuple[float, List[Dict]]:
        """Расчет бонуса за операции"""
        total_bonus = 0.0
        details = []
        
        # Рассчитываем коэффициенты
        service_coeff = self.calculate_team_coefficient(
            team_coefficients.get('service', 0), 'service'
        )
        
        # Для коэффициентов скорости используем прямые значения (они уже рассчитаны в боте)
        speed_reception_coeff = team_coefficients.get('speed_reception', 1.0)
        speed_delivery_coeff = team_coefficients.get('speed_delivery', 1.0)
        
        efficiency_coeff = self.calculate_team_coefficient(
            team_coefficients.get('efficiency', 0), 'efficiency'
        )
        
        for op_id, quantity in operations.items():
            if quantity <= 0 or op_id not in OPERATIONS_CONFIG:
                continue
                
            op_config = OPERATIONS_CONFIG[op_id]
            base_bonus = 0.0
            applied_coeff = 1.0
            
            # Специальная обработка для ПВЗ WB
            if op_id == 13:  # Обеспечение ПВЗ WB
                # Используем переданные параметры режима работы и рейтинга
                work_schedule = getattr(self, '_pvz_work_schedule', "режим1")
                rating = getattr(self, '_pvz_rating', 5.0)
                base_bonus = self.calculate_pvz_wb_bonus(int(quantity), work_schedule, rating)
            else:
                # Обычные операции
                if op_config['type'] == 'fixed':
                    base_bonus = quantity * op_config['value']
                elif op_config['type'] == 'percent':
                    base_bonus = quantity * op_config['value']
            
            # Применяем коэффициенты по типу операции
            operation_type = op_config.get('operationType', 1)
            
            if operation_type == 2:  # Тип 2: с коэффициентом обслуживания
                applied_coeff = service_coeff
            elif operation_type == 3:  # Тип 3: с коэффициентом скорости приема
                applied_coeff = speed_reception_coeff
            elif operation_type == 4:  # Тип 4: с коэффициентом скорости доставки
                applied_coeff = speed_delivery_coeff
            # Тип 1: без коэффициентов (applied_coeff = 1.0)
            
            final_bonus = base_bonus * applied_coeff
            total_bonus += final_bonus
            
            details.append({
                'name': op_config['name'],
                'quantity': quantity,
                'rate': op_config['rate'],
                'base_bonus': base_bonus,
                'coefficient': applied_coeff,
                'final_bonus': final_bonus,
                'operation_type': operation_type,
                'emoji': op_config.get('emoji', '📊')
            })
        
        # Применяем коэффициент эффективности к итоговому бонусу
        if efficiency_coeff > 0:
            efficiency_bonus = total_bonus * efficiency_coeff
            total_bonus += efficiency_bonus
            
            details.append({
                'name': 'Коэффициент эффективности ОПС',
                'quantity': team_coefficients.get('efficiency', 0),
                'rate': f'{efficiency_coeff*100:.0f}% от операций',
                'base_bonus': 0,
                'coefficient': 1.0,
                'final_bonus': efficiency_bonus,
                'operation_type': 'efficiency',
                'emoji': '📈'
            })
        
        return total_bonus, details
    
    def calculate_kpi_bonus(
        self, 
        kpi_values: Dict[str, float],
        base_salary: float,
        position_rate: float,
        position: str
    ) -> Tuple[float, List[Dict]]:
        """Расчет КПИ бонуса: 20% от оклада с распределением по весам показателей"""
        if not kpi_values:
            return 0.0, [], []
        
        total_bonus = 0.0
        details = []
        warnings = []
        
        # Реальный размер оклада = оклад × ставка
        # FALLBACK: если оклад или ставка не заданы, используем фиксированную базу 150000₽
        if base_salary > 0 and position_rate > 0:
            real_salary = base_salary * position_rate
        else:
            real_salary = 150000.0  # Фиксированная база для совместимости (30000 = 20% от 150000)
        
        # БАЗОВАЯ СУММА КПИ = 20% от оклада
        base_kpi_amount = real_salary * 0.20
        
        # Проверяем критическое правило для выручки
        revenue_percent = kpi_values.get('revenue', 0)
        if revenue_percent < 80:
            warnings.append(
                f"⚠️ Выручка {revenue_percent}% < 80% - КПИ не выплачивается!"
            )
            return 0.0, [], warnings
        
        # Получаем веса для данной должности
        position_weights = KPI_WEIGHTS.get(position, {})
        
        if not position_weights:
            warnings.append(f"⚠️ Не найдены веса КПИ для должности: {position}")
            return 0.0, [], warnings
        
        # Рассчитываем КПИ по каждому показателю
        for kpi_id, percent in kpi_values.items():
            if percent > 0 and kpi_id in position_weights:
                coefficient = self.calculate_kpi_coefficient(percent, kpi_id)
                weight = position_weights[kpi_id]
                
                # НОВАЯ ФОРМУЛА: КПИ_показателя = (базовая_сумма_КПИ × вес_показателя) × коэффициент_достижения
                kpi_bonus = base_kpi_amount * weight * coefficient
                total_bonus += kpi_bonus
                
                kpi_config = KPI_CONFIG.get(kpi_id, {'name': kpi_id, 'emoji': '📊'})
                
                details.append({
                    'name': kpi_config['name'],
                    'percent': percent,
                    'weight': weight,
                    'coefficient': coefficient,
                    'bonus': kpi_bonus,
                    'base_kpi_amount': base_kpi_amount,
                    'base_salary': base_salary,
                    'position_rate': position_rate,
                    'real_salary': real_salary,
                    'emoji': kpi_config.get('emoji', '📊')
                })
        
        return total_bonus, details, warnings
    
    def calculate_premium(
        self,
        position: str,
        base_salary: float,
        position_rate: float,
        operations: Dict[int, float],
        kpi_values: Dict[str, float],
        team_coefficients: Dict[str, float],
        subordinates_bonus: float = 0.0
    ) -> CalculationResult:
        """Основная функция расчета премии"""
        
        # Получаем конфигурацию должности
        position_config = POSITIONS_CONFIG.get(position, {})
        if not position_config:
            raise ValueError(f"Неизвестная должность: {position}")
        
        warnings = []
        
        # Расчет операционного бонуса
        operation_bonus, operation_details = self.calculate_operations_bonus(
            operations, position_config, team_coefficients
        )
        
        # Расчет КПИ бонуса (только для должностей с КПИ)
        kpi_bonus = 0.0
        kpi_details = []
        
        if position_config.get('kpi'):
            kpi_bonus, kpi_details, kpi_warnings = self.calculate_kpi_bonus(
                kpi_values, base_salary, position_rate, position
            )
            warnings.extend(kpi_warnings)
        
        # Добавляем бонус за подчиненных (для управленческого НОПС)
        if subordinates_bonus > 0:
            operation_bonus += subordinates_bonus
            operation_details.append({
                'name': 'Бонус за подчиненных',
                'quantity': 1,
                'rate': f'{subordinates_bonus}₽',
                'base_bonus': subordinates_bonus,
                'coefficient': 1.0,
                'final_bonus': subordinates_bonus,
                'operation_type': 'management',
                'emoji': '👥'
            })
        
        # Общая премия
        total_premium = operation_bonus + kpi_bonus
        real_salary = base_salary * position_rate if base_salary > 0 and position_rate > 0 else 0
        
        return CalculationResult(
            total_premium=total_premium,
            operation_bonus=operation_bonus,
            kpi_bonus=kpi_bonus,
            base_salary=base_salary,
            position_rate=position_rate,
            real_salary=real_salary,
            operation_details=operation_details,
            kpi_details=kpi_details,
            warnings=warnings,
            position_name=position_config.get('name', position)
        )

def format_money(amount: float) -> str:
    """Форматирование денежной суммы"""
    return f"{amount:,.0f}₽".replace(',', ' ')

def format_percent(value: float) -> str:
    """Форматирование процентов"""
    return f"{value:.1f}%" 