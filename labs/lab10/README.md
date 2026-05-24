# Лабораторна робота №10: NER pipeline + hybrid rules

## 1. Корпус / evaluation set
processed_v2.csv — звернення громадян (Напрям D).
Evaluation set: 25 вручну анотованих речень.

## 2. Pipeline
spaCy uk_core_news_sm. Labels: PER, ORG, LOC, DATE, MONEY, MISC.

## 3. Додані правила
1. MONEY regex — ціни у гривнях та відсотках
2. ORG-словник — 9 доменних брендів
3. PRODUCT-словник — технічні назви продуктів
4. DATE regex — числові дати та роки

## 4. Що baseline знаходив добре
LOC (часткове), ORG у стандартному форматі.

## 5. Що baseline пропускав
Доменні ORG, MONEY (грн/%), PRODUCT.

## 6. Що rules покращили
+8 ORG, +2 MONEY, +2 PRODUCT.

## 7. Проблеми що залишились
FP загальних ORG-слів, boundary errors, відносні дати, DATE FP.

## Файли
- notebooks/lab10_ner_pipeline_hybrid_rules.ipynb
- src/ner_pipeline.py, src/ner_rules.py, src/ner_eval.py
- docs/audit_summary_lab10.md, docs/ner_notes_lab10.md