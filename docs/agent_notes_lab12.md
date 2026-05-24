# Agent Notes Lab 12 — Support Assistant

## 1. Use case
Support Assistant для аналізу відгуків про сервіси (Напрям D, processed_v2.csv).

## 2. Agent task
З тексту відгуку: визначити sentiment, витягти сутності, перевірити повноту, прийняти routing decision.

## 3. Tools реалізовано (5)
1. `lookup_known_service(text)` — пошук відомих брендів у словнику
2. `classify_review(text)` — sentiment + issue_type + service_type
3. `extract_entities(text)` — service_name, price, currency
4. `validate_required_fields(data)` — перевірка required полів
5. `score_review_completeness(data)` — оцінка повноти extraction

## 4. Коли агент викликає tool
- `lookup_known_service`: ЗАВЖДИ (перший крок)
- `classify_review`: ЗАВЖДИ (другий крок)
- `extract_entities`: ТІЛЬКИ якщо є ознака ціни АБО service_name ще невідомий
- `validate_required_fields`: ЗАВЖДИ
- `score_review_completeness`: ЗАВЖДИ

Умовна логіка для `extract_entities` зменшує зайві виклики: з 10 задач викликано лише 7 разів.

## 5. Логування tool calls
Формат JSON Lines. Кожен запис: timestamp, task_id, tool_name, input, output, success, error, reason, duration_ms.
Файл: `docs/tool_logs_lab12.jsonl` (47 записів для 10 задач).

## 6. Що tools реально покращили
- Structured output: замість free-form тексту — dict з полями
- Routing decision: базований на issue_type з classify_review
- Price extraction: 100 грн → mentioned_price=100, currency=UAH
- Service identification: скайфлай, інгліш хаб → service_name

## 7. Де tools були зайві або не допомогли
- Короткий текст (case_002): "дуже погане обслуговування" — tools повернули мінімум
- Невідомий сервіс (case_010): lookup returns empty, service_name=null
- Telecom (case_008): service_type=None (не в словнику)

## 8. Помилки що залишились
- Missing domain coverage (telecom, finance в SERVICE_TYPE_KEYWORDS)
- Generic service names не розпізнаються (магазин без назви)
- Mixed-sentiment detection неточний при рівних pos/neg keywords

## 9. Що б фіксили далі
1. Розширити SERVICE_TYPE_KEYWORDS (telecom, finance)
2. Додати fallback NER для невідомих сервісів
3. Покращити mixed-sentiment detection
4. Додати LLM-backed tool для складних кейсів (fallback)