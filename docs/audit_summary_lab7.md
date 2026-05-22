# Audit Summary Lab 7 — Linear SVM + char-ngrams

## 1. Назва задачі
Бінарна класифікація текстів звернень громадян (клас 0 — негативний/скарга, клас 1 — позитивний).
Напрям D. Продовження ЛР6.

## 2. Baseline з ЛР6 (референс)
- Конфігурація: TF-IDF word(1,2) + LogisticRegression (balanced)
- Test Accuracy: 0.8953 | Test Macro-F1: 0.8930

## 3. SVM-моделі, що тестувались
1. LinearSVC word(1,2), без class_weight
2. LinearSVC word(1,2), class_weight='balanced'
3. LinearSVC char_wb(3,5), class_weight='balanced'
4. LinearSVC word(1,2) + char_wb(3,5), class_weight='balanced' ← **найкраща**

## 4. Найкращий результат на Test Set
- Модель: LinearSVC word(1,2)+char_wb(3,5) balanced
- Test Accuracy: 0.9332
- Test Macro-F1: 0.9319
- Приріст відносно ЛР6: +0.0389

## 5. Чи допомогли char-ngrams?
Приріст Macro-F1 від додавання char_wb(3,5): +0.0204
Так, char-ngrams дали приріст.

## 6. Чи допоміг class_weight='balanced'?
Приріст Macro-F1 від balanced: +0.0019
Так, balanced покращив Macro-F1.

## 7. Поріг рішення
- Логіка: recall-first (пропустити скаргу дорожче, ніж хибна тривога)
- Обраний поріг на val: -0.6961
- Test Accuracy з порогом: 0.7830 | Test Macro-F1: 0.7535

## 8. Найчастіші типи помилок
1. Overlap класів — тексти з амбівалентним змістом (є і скарга, і похвала)
2. Складні заперечення — частка "не" у позитивному контексті збиває модель
3. Короткий текст — недостатньо токенів для впевненого TF-IDF сигналу
