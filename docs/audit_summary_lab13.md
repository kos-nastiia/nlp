# Audit Summary Lab 13 — Multi-agent Crew

## 1. Use case
Support Assistant Crew для structured аналізу відгуків.

## 2. Agents
- Triager:      route selection, schema assignment
- Extractor:    JSON extraction per schema
- Reviewer:     consistency + schema validation, verdict
- FallbackAgent: rule repair → partial → manual_review

## 3. Test cases
10 cases: simple, missing_field, ambiguous, price, hallucination,
noisy, fallback_trigger, reviewer_rejects, repair_success, manual_review.

## 4. Valid final output rate
90.0%

## 5. Fallback activation rate
10.0% (1/10 cases)

## 6. Fallback success rate
0.0%

## 7. Manual review rate
10.0%

## 8. Avg agents per case
2.2

## 9. Single-agent vs crew
Baseline: free-form, unvalidated, no fallback.
Crew: structured, reviewer-validated, with fallback and audit logs.

## 10. Best crew examples
- case_001: clean accept, скайфлай + positive routing
- case_004: billing 100 UAH extracted correctly
- case_007: support escalation via review verdict

## 11. Problematic examples
- case_002: service_type missing — partial output
- case_008: domain gap (telecom) — manual review
- case_010: degenerate input — manual review required

## 12. What to improve
- Add telecom/web to SERVICE_TYPE_KW
- Improve mixed-sentiment detection
- Add input length guard before crew start
