# Crew Notes Lab 13 — Multi-agent Support Assistant

## 1. Use case
Support Assistant Crew: structured аналіз відгуків про сервіси.
Корпус: processed_v2.csv (Напрям D).

## 2. Agents у crew
| Агент | Роль |
|-------|------|
| Triager | Route selection, schema assignment |
| Extractor | JSON extraction per schema |
| Reviewer | Consistency + schema validation, verdict |
| FallbackAgent | Rule repair → partial output → manual review |

## 3. Роль кожного агента
- **Triager**: читає текст, визначає route (billing/service/product/generic), required fields, difficulty. НЕ виконує extraction.
- **Extractor**: витягує structured dict за route/schema від Triager. null для відсутніх полів. Confidence note.
- **Reviewer**: перевіряє schema (required fields), consistency (sentiment vs signals), hallucinations (price/service_name not in text). Verdict: accept / accept_with_warnings / repair_needed / fallback_needed.
- **FallbackAgent**: rule-based repair для конкретних полів → partial output + warnings → manual_review flag.

## 4. Delegation rules
1. Triager → ЗАВЖДИ перший
2. Extractor → після Triager, отримує route/schema
3. Reviewer → ЗАВЖДИ перевіряє Extractor output
4. verdict=accept / accept_with_warnings → finalize
5. verdict=repair_needed → FallbackAgent (attempt 1) → re-review
6. verdict=fallback_needed → FallbackAgent → manual_review якщо не виправлено
7. Max 2 repair attempts

## 5. Що перевіряє Reviewer
- Required fields присутні (по schema)
- Sentiment узгоджений з тональністю тексту
- Ціна в extraction є в тексті (hallucination check)
- Service_name присутній у тексті
- Issue_type не set на positive sentiment
- Confidence рівень

## 6. Коли спрацьовує fallback
- Missing required fields після extraction
- Hallucinated price або service_name
- Inconsistent sentiment
- 2+ критичних проблеми від Reviewer

## 7. Що crew покращив vs single-agent
- Reviewer ловить inconsistency та hallucinations
- Structured logs для кожного кроку
- Routing decision на основі verified extraction
- Manual review flag для degenerate inputs

## 8. Де multi-agent підхід надлишковий
- Прості однозначні відгуки (6/10 кейсів): accept без жодних проблем
- 3 агенти для тексту в 5 слів — overhead

## 9. Помилки що залишились
- service_type для телеком/веб домену відсутній у словниках
- mixed sentiment detection неточний
- single-word inputs приймаються без guard

## 10. Що б фіксили далі
1. Розширити SERVICE_TYPE_KW (телеком, веб, finance)
2. Input length guard перед crew start
3. Покращити mixed-sentiment detection
4. Додати LLM-based agent для складних ambiguous кейсів