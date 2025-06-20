# 🧮 Руководство по тестированию калькулятора премий ОПС v2.8.4

## 📋 Список тестовых сценариев

### ✅ Тест 1: Оператор - базовый расчет
**Должность:** Оператор
**Исходные данные:**
- Розница (товары): 10,000₽
- Сим-карта тип 1: 10 шт
- Привлечение пенсионера: 2 чел
- Прием РПО посылка: 50 шт
- Вручение РПО посылка: 30 шт

**Коэффициенты:**
- CSI: 95 баллов (коэфф. Сервис = 1.5)
- Скорость приема: Выполнено (коэфф. = 1.5)
- Скорость вручения: Выполнено (коэфф. = 1.5)
- Выручка ОПС: 110% (коэфф. Эффективность = 1.3)

**Ожидаемый расчет:**
1. **Операции тип 1 (без коэфф.):** 
   - Пенсионеры: 2 × 300₽ = 600₽
   
2. **Операции тип 2 (×К Сервис):**
   - Розница: 10,000₽ × 3% = 300₽
   - Сим-карты: 10 × 50₽ = 500₽
   - Итого: 800₽ × 1.5 = **1,200₽**

3. **Операции тип 3 (×К Скорость приема):**
   - Прием РПО: 50 × 5₽ = 250₽ × 1.5 = **375₽**

4. **Операции тип 4 (×К Скорость вручения):**
   - Вручение РПО: 30 × 2₽ = 60₽ × 1.5 = **90₽**

5. **Промежуточная сумма:** 600 + 1,200 + 375 + 90 = **2,265₽**

6. **Итоговая премия:** 2,265₽ × 1.3 (эффективность) = **2,944.50₽**

---

### ✅ Тест 2: НОПС - расчет с КПИ и командным бонусом
**Должность:** НОПС с операторами
**Исходные данные:**
- Розница (товары): 5,000₽  
- Выдача WB: 100 заказов
- Размер оклада: 40,000₽
- Размер ставки: 1.0 (100%)
- Премия подчиненных: 1,000₽

**Коэффициенты:**
- CSI: 98 баллов (коэфф. Сервис = 1.5)

**КПИ:**
- Выручка ОПС: 85% → коэфф. 0.3
- CSI показатель: 105% → коэфф. 1.05
- Доля онлайн-РПО: 110% → коэфф. 1.1  
- CO1/CO2: 95% → коэфф. 0

**Ожидаемый расчет:**
1. **Операции:**
   - Розница: 5,000₽ × 3% = 150₽ × 1.5 = 225₽
   - Выдача WB: 100 × 5₽ = 500₽ (тип 1, без коэфф.)
   - **Итого операции:** 725₽

2. **КПИ (20% от оклада):**
   - База КПИ: 40,000₽ × 1.0 × 20% = 8,000₽
   - Взвешенная сумма: (0.30×0.3) + (0.40×1.05) + (0.15×1.1) + (0.15×0) = 0.09 + 0.42 + 0.165 + 0 = 0.675
   - **КПИ:** 8,000₽ × 0.675 = **5,400₽**

3. **Командный бонус:** 1,000₽ × 3% = **30₽**

4. **Итоговая премия:** 725 + 5,400 + 30 = **6,155₽**

---

### ✅ Тест 3: Проверка коэффициента CSI
**Должность:** Оператор
**Исходные данные:**
- Розница (товары): 1,000₽

**Варианты CSI:**
- **CSI = 89 баллов:** коэфф. 0.5 → премия = 1,000₽ × 3% × 0.5 = **15₽**
- **CSI = 94 балла:** коэфф. 1.0 → премия = 1,000₽ × 3% × 1.0 = **30₽**  
- **CSI = 96 баллов:** коэфф. 1.5 → премия = 1,000₽ × 3% × 1.5 = **45₽**

---

### ✅ Тест 4: КПИ Выручка < 80% (блокировка)
**Должность:** НОПС с операторами
**КПИ:**
- Выручка ОПС: 75% (< 80%)
- Остальные показатели: любые

**Ожидаемый результат:** 
- КПИ = **0₽** (блокируется при выручке < 80%)

---

### ✅ Тест 5: Коэффициент Эффективности ОПС
**Должность:** Оператор  
**Исходные данные:**
- Розница: 1,000₽ (премия 30₽)

**Варианты:**
- **Выручка ОПС = 80%:** коэфф. 1.0 → итого = 30₽ × 1.0 = **30₽**
- **Выручка ОПС = 110%:** коэфф. 1.3 → итого = 30₽ × 1.3 = **39₽**

---

## 🛠️ Как проводить тест:

1. **Откройте калькулятор** (`калькулятор_премий_опс.html`)
2. **Выберите должность** из тестового сценария
3. **Введите данные** точно как указано в тесте
4. **Сравните результат** с ожидаемым значением
5. **Откройте консоль браузера** (F12) для просмотра логов расчета

## ✨ Дополнительные проверки:

### Проверка скоростных коэффициентов:
- **Скорость приема:** < 4 мин = 1.5, > 4 мин = 0.5
- **Скорость вручения:** < 1:30 мин = 1.5, > 1:30 мин = 0.5

### Проверка веб КПИ:
- **Выручка:** < 80% = 0, 80-89% = 0.3, 90-99% = 0.5, 100-149% = процент/100, ≥150% = 1.5
- **Остальные:** < 100% = 0, 100% = 1, > 100% = процент/100 (макс. 1.2)

### Проверка автоматического расчета:
- При изменении любого поля должен происходить мгновенный пересчет
- Фиксированная карточка справа должна обновляться в реальном времени

---

## 🎯 Ожидаемые результаты:
- ✅ Все тесты должны показывать точные суммы
- ✅ Автоматический расчет работает без ошибок  
- ✅ Консоль браузера не показывает ошибок
- ✅ Фиксированная карточка отображает корректную сумму 