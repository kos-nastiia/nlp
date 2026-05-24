# Audit Summary Lab 14 — Flow Orchestration

## 1. Use case
Stateful NLP flow для structured аналізу відгуків про сервіси.

## 2. Flow steps
ingest → route → execute → validate → [fallback] → export

## 3. Test cases
10 cases: clean_pass, missing_field, generic_route, hallucination_guard,
fallback_triggered, fallback_success, safe_failure, noisy_price, ambiguous, known_service.

## 4. Flow completion rate
100.0%

## 5. Validation pass rate
60.0%

## 6. Fallback activation rate
3 / 10 (30.0%)

## 7. Fallback success rate
0.0%

## 8. Export valid rate
100.0%

## 9. Manual review / safe failure rate
3 / 10 (30.0%)

## 10. Best flow examples
- case_001: скайфлай positive — clean 5-step pass, positive archive routing
- case_008: billing 200 UAH — billing route + price extraction
- case_009: support ambiguity resolved — скайфлай + support escalation

## 11. Problematic examples
- case_002: service_type missing — domain gap (обслуговування not in keywords)
- case_005: very short negative — fallback partial, cannot recover
- case_007: empty input — safe_failure with structured error

## 12. Flow vs ad-hoc
Flow дає: state трасування, validation, controlled fallback, structured export.
Ad-hoc: faster but no validation, no fallback, no audit trail.

## 13. What to improve
- Extend SERVICE_TYPE_KW (telecom/web)
- Input length guard before route
- Price range normalization