# ⚡ Быстрая проверка калькулятора

## 🎯 Тест 1: Оператор
1. Выберите **Оператор**
2. Введите: **Розница (товары): 1000**
3. **CSI: 95**, **Выручка ОПС: 110**
4. **Ожидаемо:** 1000 × 3% × 1.5 × 1.3 = **58.50₽**

## 🎯 Тест 2: Проверка CSI
1. Смените **CSI на 89**
2. **Ожидаемо:** 1000 × 3% × 0.5 × 1.3 = **19.50₽**

## 🎯 Тест 3: НОПС КПИ
1. Выберите **НОПС с операторами**
2. **Оклад: 50000**, **Ставка: 1.0**  
3. КПИ: **Выручка 85%**, **CSI 100%**, **онлайн-РПО 100%**, **CO1/CO2 100%**
4. **Ожидаемо КПИ:** 50000 × 0.2 × (0.3×0.3 + 0.4×1 + 0.15×1 + 0.15×1) = **9,400₽**

✅ Все расчеты должны быть точными до копейки! 