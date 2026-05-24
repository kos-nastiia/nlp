import pandas as pd
from collections import Counter


TEST_CASES = [
    # 1. Простий — flow без помилок
    {
        "case_id":  "case_001",
        "text":     "авіакомпанія скайфлай це відмінний вибір для подорожей | нові літаки",
        "expected": {"route": "support_classification", "sentiment": "positive", "has_issues": False},
        "scenario": "clean_pass",
        "notes":    "All 5 steps clean. Reviewer accepts. Route to positive archive.",
    },
    # 2. Missing required field
    {
        "case_id":  "case_002",
        "text":     "дуже погане обслуговування",
        "expected": {"sentiment": "negative", "service_type": None, "has_issues": True},
        "scenario": "missing_field",
        "notes":    "service_type missing → validate flags → fallback attempts rule repair",
    },
    # 3. Unknown route → generic fallback
    {
        "case_id":  "case_003",
        "text":     "загалом нічого, просто пише",
        "expected": {"route": "generic_feedback", "has_issues": False},
        "scenario": "generic_route",
        "notes":    "No keywords → generic_feedback route. Minimal required fields.",
    },
    # 4. Validation catches hallucination
    {
        "case_id":  "case_004",
        "text":     "чудовий сервіс без жодних претензій",
        "expected": {"sentiment": "positive", "mentioned_price": None, "has_issues": False},
        "scenario": "validate_hallucination_guard",
        "notes":    "Positive text, no price in text. Validate must ensure price=null.",
    },
    # 5. Fallback needed — multiple missing fields
    {
        "case_id":  "case_005",
        "text":     "це погано",
        "expected": {"sentiment": "negative", "has_issues": True, "needs_manual_review": True},
        "scenario": "fallback_triggered",
        "notes":    "Very short negative text. service_type and issue_type missing. Fallback.",
    },
    # 6. Fallback helps — repair recovers field
    {
        "case_id":  "case_006",
        "text":     "ніколи більше не замовлятиму в цій службі доставки | товар з величезною затримкою",
        "expected": {"sentiment": "negative", "issue_type": "delivery", "service_type": "доставка"},
        "scenario": "fallback_success",
        "notes":    "Delivery keywords → fallback can recover issue_type if missing.",
    },
    # 7. Fallback fails → manual review
    {
        "case_id":  "case_007",
        "text":     "",
        "expected": {"status": "ingest_failed", "needs_manual_review": True},
        "scenario": "safe_failure",
        "notes":    "Empty input → ingest fails → safe failure with structured error output.",
    },
    # 8. Noisy input — price range
    {
        "case_id":  "case_008",
        "text":     "ціни в барі клубу шокують | за один смузі можна легко викласти 200300 грн",
        "expected": {"route": "billing_extraction", "mentioned_price": 200, "currency": "UAH"},
        "scenario": "noisy_price",
        "notes":    "200-300 range → lower bound extracted. Billing route. Currency UAH.",
    },
    # 9. Ambiguous route → billing wins over support
    {
        "case_id":  "case_009",
        "text":     "служба підтримки скайфлай працює жахливо | дозвонитись майже неможливо",
        "expected": {"route": "support_classification", "issue_type": "support", "service_name": "скайфлай"},
        "scenario": "ambiguous_route",
        "notes":    "Both support and known-service signals. Support route wins.",
    },
    # 10. Flow completes with warning — partial data
    {
        "case_id":  "case_010",
        "text":     "інгліш хаб це чудова можливість вивчити англійську | зручний графік занять",
        "expected": {"sentiment": "positive", "service_name": "інгліш хаб", "service_type": "школа"},
        "scenario": "clean_with_known_service",
        "notes":    "Clean positive with known brand. All fields extractable. Accept.",
    },
]



def adhoc_pipeline(text: str) -> dict:
    import re
    t = text.lower()
    neg = sum(1 for w in ["жахлив","погано","розчарован","нікол","занадто"] if w in t)
    pos = sum(1 for w in ["чудово","відмінн","найкращ","задоволен","тішить"] if w in t)
    sentiment = "positive" if pos > neg else "negative" if neg > pos else "neutral"
    service_type = None
    for svc, kws in [("доставка",["доставка"]),("кафе",["кафе","каву"]),
                     ("авіакомпанія",["рейс","літак"]),("школа",["навчання","курс"])]:
        if any(kw in t for kw in kws):
            service_type = svc; break
    return {
        "sentiment":    sentiment,
        "service_type": service_type,
        "service_name": None,
        "issue_type":   None,
        "validated":    False,
        "fallback":     False,
        "structured":   False,
    }


ERROR_ANALYSIS = [
    {
        "case_id":         "case_001",
        "scenario":        "clean_pass",
        "input":           "авіакомпанія скайфлай це відмінний вибір",
        "expected":        "5 steps clean, accept, positive archive",
        "actual_route":    "support_classification",
        "execute_output":  "sentiment=positive, service_name=скайфлай",
        "validation":      "accept",
        "fallback":        "none",
        "export_status":   "exported",
        "category":        "correct behavior",
        "fix":             "N/A — showcase of successful flow",
    },
    {
        "case_id":         "case_002",
        "scenario":        "missing_field",
        "input":           "дуже погане обслуговування",
        "expected":        "service_type identified, issue=support",
        "actual_route":    "generic_feedback",
        "execute_output":  "service_type=None (no keyword match)",
        "validation":      "repair_and_export_with_warning",
        "fallback":        "rule_repair attempted, partial success",
        "export_status":   "exported_with_warnings",
        "category":        "missing field — domain gap",
        "fix":             "Додати 'обслуговування' до SERVICE_TYPE_KW",
    },
    {
        "case_id":         "case_004",
        "scenario":        "validate_hallucination_guard",
        "input":           "чудовий сервіс без жодних претензій",
        "expected":        "no price, validate ensures mentioned_price=null",
        "actual_route":    "support_classification",
        "execute_output":  "mentioned_price=null (correct)",
        "validation":      "accept",
        "fallback":        "none",
        "export_status":   "exported",
        "category":        "correct — hallucination guard works",
        "fix":             "N/A",
    },
    {
        "case_id":         "case_005",
        "scenario":        "fallback_triggered",
        "input":           "це погано",
        "expected":        "negative, some issue identified",
        "actual_route":    "generic_feedback",
        "execute_output":  "sentiment=negative, service_type=None, issue_type=None",
        "validation":      "repair_and_export_with_warning — missing fields",
        "fallback":        "partial_output — cannot recover without text signals",
        "export_status":   "exported_with_warnings",
        "category":        "fallback not fully helpful — minimal text",
        "fix":             "Input guard: length < 4 tokens → immediate manual_review",
    },
    {
        "case_id":         "case_007",
        "scenario":        "safe_failure",
        "input":           "(empty string)",
        "expected":        "ingest fails, structured error exported",
        "actual_route":    "None — ingest blocked",
        "execute_output":  "None",
        "validation":      "skipped",
        "fallback":        "skipped",
        "export_status":   "safe_failure",
        "category":        "ingest failure — correct safe behavior",
        "fix":             "N/A — flow handles degenerate input correctly",
    },
    {
        "case_id":         "case_008",
        "scenario":        "noisy_price",
        "input":           "200300 грн — злите число",
        "expected":        "price=200 (lower bound), currency=UAH",
        "actual_route":    "billing_extraction",
        "execute_output":  "mentioned_price=200, currency=UAH",
        "validation":      "accept_with_warnings — lower bound assumption",
        "fallback":        "none",
        "export_status":   "exported_with_warnings",
        "category":        "normalization issue — price range",
        "fix":             "Додати price range нормалізацію (200-300 → range object)",
    },
    {
        "case_id":         "case_009",
        "scenario":        "ambiguous_route",
        "input":           "скайфлай підтримка жахлива",
        "expected":        "support route, скайфлай identified",
        "actual_route":    "support_classification",
        "execute_output":  "sentiment=negative, service_name=скайфлай, issue=support",
        "validation":      "accept",
        "fallback":        "none",
        "export_status":   "exported",
        "category":        "correct — ambiguity resolved by priority",
        "fix":             "N/A — scoring + priority handles ties",
    },
    {
        "case_id":         "case_003",
        "scenario":        "generic_route",
        "input":           "загалом нічого, просто пише",
        "expected":        "generic_feedback, neutral, minimal fields",
        "actual_route":    "generic_feedback",
        "execute_output":  "sentiment=neutral, service_type=None",
        "validation":      "accept (only sentiment+key_aspect required)",
        "fallback":        "none",
        "export_status":   "exported",
        "category":        "correct — generic route handles unknown input",
        "fix":             "N/A",
    },
    {
        "case_id":         "case_006",
        "scenario":        "fallback_success",
        "input":           "ніколи не замовлятиму в цій службі доставки",
        "expected":        "delivery, negative, fallback recovers issue_type",
        "actual_route":    "delivery_complaint",
        "execute_output":  "sentiment=negative, service_type=доставка",
        "validation":      "accept — all required fields present",
        "fallback":        "none needed — direct extraction succeeded",
        "export_status":   "exported",
        "category":        "correct — delivery route works cleanly",
        "fix":             "N/A",
    },
    {
        "case_id":         "case_010",
        "scenario":        "clean_known_service",
        "input":           "інгліш хаб це чудова можливість вивчити англійську",
        "expected":        "positive, школа, інгліш хаб",
        "actual_route":    "support_classification",
        "execute_output":  "sentiment=positive, service_name=інгліш хаб, service_type=школа",
        "validation":      "accept",
        "fallback":        "none",
        "export_status":   "exported",
        "category":        "correct — known brand + education route",
        "fix":             "N/A",
    },
]


def error_analysis_df() -> pd.DataFrame:
    return pd.DataFrame(ERROR_ANALYSIS)


def error_category_summary() -> Counter:
    return Counter(e["category"] for e in ERROR_ANALYSIS)