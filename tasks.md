# 📊 ПЛАН РЕАЛИЗАЦИИ: КАЛЬКУЛЯТОР ПРЕМИЙ ОПС

## 🎯 ОПРЕДЕЛЕНИЕ СЛОЖНОСТИ: LEVEL 3-4

**Обоснование уровня сложности:**
- Сложная бизнес-логика с множественными условиями
- 4 различные должности с уникальными правилами расчета
- 25+ операций с разными типами и ставками
- Критичные бизнес-правила (правило 80% выручки)
- Интеграция КПИ показателей и командных коэффициентов
- Требование автономной работы на Windows

**Complexity Level: 3** (с элементами Level 4)

## 📋 ДЕТАЛЬНЫЕ ТРЕБОВАНИЯ

### 🏢 АРХИТЕКТУРНЫЕ КОМПОНЕНТЫ

**1. Основные сущности:**
- Должности: Оператор, НОПС, Администратор, Почтальон
- Операции: 25 типов с различными ставками
- КПИ: 5 показателей с прогрессивными шкалами
- Коэффициенты: Сервис, Скорость, Эффективность ОПС

**2. Бизнес-правила:**
- Правило 80% выручки (критичное)
- Типизация операций (1-4 типа)
- Матрица доступности операций по должностям
- Формулы расчета для каждой должности

### 🔧 ТЕХНИЧЕСКАЯ АРХИТЕКТУРА

**Платформа:** Автономный HTML файл
**Технологии:** HTML5 + CSS3 + Vanilla JavaScript
**Размер:** ~50-100 КБ (включая все данные)
**Совместимость:** Все браузеры, Windows XP+

### 📊 КОМПОНЕНТЫ ИНТЕРФЕЙСА

**1. Выбор должности (радио-кнопки):**
- Оператор/Начальник с операторами
- НОПС (Начальник без операторов) 
- Администратор
- Почтальон

**2. Блок операций (динамический):**
- Отображение только доступных операций для выбранной должности
- Группировка по типам операций
- Поля ввода количества/суммы

**3. Блок КПИ:**
- Выручка ОПС (план/факт)
- CSI показатель (план/факт)
- Доля онлайн-РПО (план/факт)
- CO1/CO2 своевременность (план/факт)
- Дополнительные поля по должности

**4. Блок результатов:**
- Детальная разбивка по компонентам
- Применение коэффициентов
- Итоговая сумма премии
- Объяснение расчетов

## 🚀 ПЛАН РЕАЛИЗАЦИИ

### ✅ ФАЗА 1: БАЗОВАЯ СТРУКТУРА (Level 2) - ЗАВЕРШЕНА + ИСПРАВЛЕНИЯ
**Время:** 2-3 часа (Завершено + критичные исправления по КПИ)

**Задачи:**
- [x] Анализ требований завершен
- [x] Создание HTML структуры
- [x] Базовый CSS дизайн
- [x] Выбор должности и переключение интерфейса
- [x] Основные 10 операций (самые популярные)
- [x] Простые формулы расчета
- [x] Базовая валидация
- [x] **КРИТИЧНЫЕ ИСПРАВЛЕНИЯ:**
  - [x] Убрал КПИ у обычных операторов
  - [x] Добавил командный бонус только НОПС 
  - [x] Исправил правило 80% (только КПИ)

**Основные операции для Фазы 1:**
1. Розница товары (3%)
2. Лотерейные билеты (3%)
3. Подписка (2%)
4. Сим-карта тип 1 (50₽)
5. Мультиподпись (30₽)
6. Привлечение пенсионера (300₽)
7. Прием РПО посылка (5₽)
8. Прием РПО письмо (0.5₽)
9. Выдача WB (5₽)
10. Привлечение клиентов (1000₽)

### ⚙️ ФАЗА 2: РАСШИРЕННАЯ ЛОГИКА (Level 3)
**Время:** 3-4 часа

**Задачи:**
- [ ] Все 25 операций
- [ ] Полные КПИ расчеты с прогрессивными шкалами
- [ ] Правило 80% выручки (критичное)
- [ ] Командные коэффициенты
- [ ] Матрица доступности операций по должностям
- [ ] Детальная разбивка результатов

### 🎨 ФАЗА 3: ПОЛИРОВКА И ОПТИМИЗАЦИЯ (Level 3-4)
**Время:** 1-2 часа

**Задачи:**
- [ ] Современный UI/UX дизайн
- [ ] Адаптивность для мобильных
- [ ] Продвинутая валидация
- [ ] Подсказки и объяснения
- [ ] Экспорт результатов
- [ ] Тестирование на разных браузерах

## 🧩 ДЕТАЛЬНАЯ АРХИТЕКТУРА

### 💾 СТРУКТУРА ДАННЫХ

```javascript
const positions = {
  operator: {
    name: "Оператор/Начальник с операторами",
    operations: [1,2,3,4,5,6,7,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25],
    kpi: ["revenue", "csi", "online_rpo", "co1_co2"],
    formula: "personalBonus + kpiBonus + 3%_from_others"
  },
  nops: {
    name: "НОПС (без операторов)",
    operations: [1,2,3,4,5,6,7,15,16,17,18,19,20,21,22,23,24,25],
    kpi: ["revenue", "csi", "online_rpo", "co1_co2"],
    formula: "personalBonus + kpiBonus"
  },
  admin: {
    name: "Администратор", 
    operations: [3,16],
    kpi: ["revenue", "csi", "online_rpo"],
    formula: "personalBonus + kpiBonus"
  },
  postman: {
    name: "Почтальон",
    operations: [2,3,4,5,6,7,8,9],
    kpi: ["revenue_postamt", "csi"],
    formula: "personalBonus * service_coef * efficiency_coef"
  }
}
```

### 🔄 КРИТИЧНЫЕ БИЗНЕС-ПРАВИЛА

**1. Правило 80% выручки:**
```javascript
if (revenue_percent < 80) {
  all_kpi_coefficients = 0;
  kpi_bonus = 0;
}
```

**2. Прогрессивные шкалы КПИ:**
```javascript
function calculateKpiCoef(percent, type) {
  if (type === 'revenue') {
    if (percent < 80) return 0;
    if (percent < 90) return 0.3;
    if (percent < 100) return 0.5;
    if (percent < 150) return percent / 100;
    return 1.5;
  }
  // ...другие типы
}
```

## ⚠️ ВЫЯВЛЕННЫЕ ВЫЗОВЫ И РЕШЕНИЯ

### 🚨 ОСНОВНЫЕ ВЫЗОВЫ:

**1. Сложность бизнес-логики**
- **Проблема:** 4 разные формулы расчета
- **Решение:** Модульная архитектура с отдельными калькуляторами

**2. Большой объем операций**
- **Проблема:** 25 операций перегружают интерфейс
- **Решение:** Группировка + прогрессивное раскрытие

**3. Критичное правило 80%**
- **Проблема:** Может обнулить всю премию
- **Решение:** Яркое предупреждение + объяснение

**4. Автономность**
- **Проблема:** Все данные должны быть встроены
- **Решение:** JSON конфигурация внутри HTML

### 💡 ИННОВАЦИОННЫЕ РЕШЕНИЯ:

**1. Пошаговый мастер:** Guided flow для сложных расчетов
**2. Визуализация:** Диаграммы разбивки премии  
**3. Валидация:** Real-time проверка и подсказки
**4. Экспорт:** Сохранение результатов в PDF/Excel

## ✅ КРИТЕРИИ ГОТОВНОСТИ

### 📊 ФАЗА 1 (MVP):
- [ ] Работают все 4 должности
- [ ] Основные 10 операций реализованы
- [ ] Базовые КПИ рассчитываются
- [ ] Правило 80% работает
- [ ] Результат показывается с разбивкой

### 🎯 ФАЗА 2 (FULL):
- [ ] Все 25 операций
- [ ] Все КПИ с прогрессивными шкалами
- [ ] Командные коэффициенты
- [ ] Детальные объяснения
- [ ] Современный дизайн

### 🏆 ФАЗА 3 (POLISH):
- [ ] Мобильная адаптивность
- [ ] Экспорт результатов
- [ ] Продвинутая валидация
- [ ] Тестирование в IE/Edge/Chrome/Safari

## 🎨 КОМПОНЕНТЫ ТРЕБУЮЩИЕ CREATIVE PHASE

**Не требуется Creative Phase** - архитектура и дизайн достаточно определены из требований.

## ⏭️ РЕКОМЕНДАЦИЯ СЛЕДУЮЩЕГО РЕЖИМА

**IMPLEMENT MODE** - план детализирован, можно приступать к реализации с Фазы 1.

---

**Статус:** ✅ Планирование завершено  
**Следующий этап:** → IMPLEMENT MODE (Фаза 1)  
**Время реализации:** 6-9 часов (все фазы) 