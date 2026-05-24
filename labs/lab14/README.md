# ЛР14: Flow Orchestration

## 1. Use case
Stateful NLP flow для аналізу відгуків. Напрям D.

## 2. Flow steps
ingest → route → execute → validate → [fallback] → export

## 3. State
FlowState dataclass (flow_state.py). Акумулюється через 5+ кроків.

## 4. Routes
support_classification, billing_extraction, product_feedback,
delivery_complaint, generic_feedback, manual_review.

## 5. Validation
Schema (required fields), enums, consistency, hallucination guard.

## 6. Fallback
Max 2 attempts: rule_repair → partial_export → manual_review_required.

## 7. Export format
JSON dict + routing_decision. safe_failure = structured error.

## 8. Запуск
```bash
pip install -r labs/lab14/requirements.txt
jupyter notebook notebooks/lab14_flow_orchestration_crewai_flows.ipynb
# Kernel → Restart & Run All
```

## 9. Logs
docs/flow_logs_lab14.jsonl (10 рядків, 1 case = 1 рядок)

## 10. Метрики
- Flow completion: 100%
- Validation pass: 60%
- Fallback: 30%
- Export valid: 100%

## 11. Висновок
Stateful flow дає повний audit trail та structured output навіть при safe_failure. Validation реально ловить проблеми. Надлишковий для простих кейсів.