# Audit Summary Lab 12 — Tool-grounded Single Agent

## 1. Use case
Support Assistant: structured analysis of service reviews.
Agent task: classify sentiment, extract entities, validate, route.

## 2. Tools
1. lookup_known_service   — dictionary lookup for known brands
2. classify_review        — sentiment + issue_type + service_type
3. extract_entities       — service_name, price, currency
4. validate_required_fields — completeness check
5. score_review_completeness — final completeness score

## 3. Test cases
10 test cases covering: simple, missing data, noisy, empty result,
unnecessary tool, ambiguous, two tools needed, validator issue, tool output in answer, tool not helpful.

## 4. Tool call success rate
100.0% (47/47 calls)

## 5. Average tool calls per task
4.7 (varies 3-5 depending on conditional logic)

## 6. Tasks with useful tool use
7/10

## 7. Unnecessary tool calls
1 (extract_entities skipped correctly when no price signal)

## 8. Best tool use examples
- case_007: 100 грн extracted correctly → routing to billing team
- case_001: скайфлай identified → routing to positive archive
- case_009: support issue → escalate to support team

## 9. Problematic examples
- case_002: text too short → tools return empty results
- case_008: telecom not in dict → service_type=None
- case_010: unknown service → service_name=null

## 10. What to improve
- Expand SERVICE_TYPE_KEYWORDS for telecom, finance
- Add fallback generic ORG extractor
- Improve mixed-sentiment detection
