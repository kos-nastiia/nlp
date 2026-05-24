# Audit Summary Lab 10 — NER pipeline + hybrid rules

## 1. Pipeline
spaCy uk_core_news_sm. Labels: PER, ORG, LOC, DATE, MONEY, MISC.

## 2. Важливі сутності
ORG (Скайфлай, Інгліш Хаб, Shimano), MONEY (грн), PRODUCT, DATE.

## 3. Що baseline знаходив добре
LOC (міста), стандартні ORG у новинному форматі.

## 4. Що baseline пропускав
Доменні ORG (Скайфлай, Інгліш Хаб), MONEY (грн/%), PRODUCT (wh1000xm4).

## 5. Правила гібридного шару
1. MONEY regex: \d+[–-]?\d*\s*(грн|гривень|$|%)
2. ORG-словник: 9 записів (Скайфлай, Інгліш Хаб, Shimano та ін.)
3. PRODUCT-словник: 3 записи (Shimano Deore, WH-1000XM4)
4. DATE regex: числові дати та роки

## 6. Що правила реально покращили
+8 правильних ORG, +2 MONEY, +2 PRODUCT.

## 7. Категорії помилок
1. missed domain entity (7) — 5/7 покрито правилами
2. false positive (4) — залишились (blocklist потрібен)
3. boundary error (3) — частково

## 8. Що далі
Blocklist ORG-слів, правило відносних дат, DATE FP guard, розширення словника.
