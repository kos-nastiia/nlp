# Лабораторна робота №7: Linear SVM + char-ngrams + imbalance

## 1. Підзадача класифікації
**Напрям D:** Груба тематична бінарна класифікація текстів звернень громадян (клас 0 — негативний досвід / скарга, клас 1 — позитивний досвід / задоволення) на основі `processed_v2.csv`.

## 2. Baseline з ЛР6 (референс)
**TF-IDF word(1,2) + Logistic Regression (class_weight='balanced')**
- Accuracy: 0.8968 | Macro-F1: 0.8944

## 3. SVM-варіанти, що перевірялись
| # | Назва | Векторизація | class_weight |
|---|-------|-------------|--------------|
| 1 | LogReg (ЛР6 ref) | TF-IDF word(1,2) | balanced |
| 2 | LinearSVC word | TF-IDF word(1,2) | no |
| 3 | LinearSVC word balanced | TF-IDF word(1,2) | balanced |
| 4 | LinearSVC char | TF-IDF char_wb(3,5) | balanced |
| 5 | LinearSVC word+char | TF-IDF word(1,2) + char_wb(3,5) | balanced |

## 4. Дисбаланс класів
У датасеті є помірний дисбаланс: клас 1 — 56.6%, клас 0 — 43.4%.
`class_weight='balanced'` дав приріст Macro-F1 приблизно на 1–2 п.п. для SVM моделей.

## 5. Поріг рішення
Поріг підбирався на **validation set** (не на test).
Обрано **recall-first логіку**: для завдань моніторингу скарг громадян пропустити скаргу (FN) дорожче, ніж помилково відмітити нейтральний текст (FP).
Підібрано поріг з максимальним recall при precision ≥ 0.75.

## 6. Найкраща модель
**LinearSVC word(1,2) + char_wb(3,5) + class_weight='balanced'** (комбінований варіант) показав найкращий результат завдяки здатності char-ngrams вловлювати варіативність написання, заперечення та специфічний сленг.

## 7. Що робити далі
- Спробувати лематизацію (`lemma_text` з ЛР3) у комбінації з char-ngrams
- Налаштувати параметр `C` у LinearSVC через крос-валідацію
- Розглянути oversampling minority class через SMOTE для кращого балансу
- Перейти до щільних представлень (embeddings) у наступних лабораторних

## Файли
- `notebooks/lab7_linear_svm_char_ngrams.ipynb` — основний ноутбук
- `src/svm_experiments.py` — функції побудови та оцінки моделей
- `src/threshold_eval.py` — PR-curve та аналіз порогу
- `docs/audit_summary_lab7.md` — підсумковий звіт