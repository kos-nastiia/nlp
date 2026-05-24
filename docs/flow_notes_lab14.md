# Flow Notes Lab 14 — Stateful NLP Flow

## 1. Use case
Stateful NLP flow для structured аналізу відгуків про сервіси.
Корпус: processed_v2.csv (Напрям D).

## 2. Етапи flow
ingest → route → execute → validate → [fallback] → export

## 3. Структура state
FlowState dataclass: 30+ полів, що акумулюються через кроки.
Ключові групи: ingest_fields, route_fields, execute_fields, validate_fields, fallback_fields, export_fields, lifecycle.

## 4. Можливі routes
- support_classification  — відомий сервіс, загальний feedback
- billing_extraction      — ціна/гривні у тексті
- product_feedback        — shimano/wh1000/бренд
- delivery_complaint      — доставка/затримка
- generic_feedback        — немає специфічних keywords
- manual_review           — порожній input або тривалий fallback

## 5. Що робить execute
Keyword heuristic + regex: sentiment, service_type, service_name, issue_type, mentioned_price, currency, key_aspect, confidence.
Поважає route: не виконує зайвих extraction поза схемою.

## 6. Що перевіряє validate
- Required fields (schema-aware, sentiment-aware)
- Enum validation (sentiment, confidence)
- Consistency: sentiment vs text signals
- Hallucination: price/service_name must be in text
- Confidence threshold

## 7. Коли fallback
- recommended_action = fallback_needed (2+ critical issues)
- recommended_action = repair_and_export_with_warning (missing critical fields)
- Max 2 attempts, then manual_review_required

## 8. Export format
JSON dict: case_id, route, task_type, sentiment, service_type, service_name, issue_type, mentioned_price, currency, key_aspect, confidence, needs_manual_review, routing_decision.
JSONL log: flow_logs_lab14.jsonl (1 рядок = 1 кейс).

## 9. Flow vs ad-hoc pipeline
Flow: state трасування, validation, controlled fallback, structured safe_failure, audit JSONL.
Ad-hoc: один крок, без state, без validation, debug неможливий.

## 10. Де flow надлишковий
7/10 кейсів проходять cleanly без fallback. 5-крокова архітектура — overhead для простих однозначних відгуків.

## 11. Що б фіксили далі
1. SERVICE_TYPE_KW: телеком, веб, фінансові послуги
2. Input guard: len < 3 tokens → immediate manual_review
3. Price range normalization (200-300 → {"min":200,"max":300})
4. Mixed-sentiment detection (pos + neg > 0)
5. LLM-backed execute для складних ambiguous кейсів