# Memory Policy Lab 14 — Flow State

## 1. Що зберігається в state
- case_id, raw_text, clean_text, word_count (ingest)
- route, schema_name, required_fields, routing_reason (route)
- execute_output, execution_method, execute_confidence (execute)
- validation_ok, validation_issues, recommended_action (validate)
- fallback_strategy, fallback_ok, fallback_attempt (fallback)
- final_output, export_format, status (export)
- errors[], warnings[], steps_completed[], needs_manual_review

## 2. Що НЕ зберігається
- API keys або credentials
- Дані інших кейсів або сесій
- Промпти або системні інструкції
- Повні великі документи без потреби
- Проміжні невалідні outputs як truth
- Персональна інформація поза поточним кейсом

## 3. Передача між етапами
- ingest → route: передає clean_text, word_count
- route → execute: передає route, required_fields, schema_name
- execute → validate: передає execute_output
- validate → fallback: передає validation_issues, recommended_action
- fallback → export: передає відремонтований execute_output

## 4. Логування помилок
- state.errors[]: {"step": step_name, "error": message}
- state.warnings[]: {"step": step_name, "warning": message}
- Невалідні proміжні outputs → errors, не приймаються як truth
- Safe failure: structured error dict, не виняток

## 5. Knowledge / schema registry
- router.py SCHEMAS: read-only schema definitions
- router.py ROUTE_KEYWORDS: read-only routing patterns
- executor.py dicts: read-only brand and keyword lists
- Flow НЕ може модифікувати knowledge files

## 6. Read-only knowledge files
- router.py:   SCHEMAS, ROUTE_KEYWORDS, KNOWN_SERVICES
- executor.py: KNOWN_SERVICES_MAP, SERVICE_TYPE_KW, ISSUE_KW
- exporter.py: export format templates

## 7. Запобігання state pollution
- Кожен кейс: свіжий FlowState(case_id=...)
- Fallback output → тільки після re-validation
- Invalid intermediate → logs, not accepted fields
- No shared mutable state between cases

## 8. Що не логується
- API keys або credentials
- Приватні дані інших користувачів
- Системні промпти або instructions
- Internal framework state