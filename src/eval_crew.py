import pandas as pd
from collections import Counter

TEST_CASES = [
    # 1. Простий кейс — все працює
    {
        "case_id":  "case_001",
        "text":     "авіакомпанія скайфлай це відмінний вибір для подорожей | нові літаки",
        "expected": {"sentiment": "positive", "service_name": "скайфлай", "has_issues": False},
        "scenario": "simple_clean",
        "notes":    "Triager: service_review. Extractor: clean. Reviewer: accept.",
    },
    # 2. Missing required field
    {
        "case_id":  "case_002",
        "text":     "дуже погане обслуговування",
        "expected": {"sentiment": "negative", "service_type": None, "has_issues": True},
        "scenario": "missing_field",
        "notes":    "service_type missing — validator catches, fallback attempts fix",
    },
    # 3. Ambiguous entity
    {
        "case_id":  "case_003",
        "text":     "ресторан непоганий але ціни завищені та не відповідають якості страв",
        "expected": {"sentiment": "mixed", "issue_type": "billing", "has_issues": True},
        "scenario": "ambiguous_entity",
        "notes":    "mixed sentiment — billing + quality signals simultaneously",
    },
    # 4. Explicit price extraction
    {
        "case_id":  "case_004",
        "text":     "платити майже 100 грн за посередню каву це занадто | кав'ярня розчарувала",
        "expected": {"sentiment": "negative", "mentioned_price": 100, "currency": "UAH", "has_issues": False},
        "scenario": "price_extraction",
        "notes":    "Billing route — price explicit. Extractor should capture 100 UAH.",
    },
    # 5. Hallucination risk
    {
        "case_id":  "case_005",
        "text":     "загалом нормально, є певні зауваження",
        "expected": {"sentiment": "neutral", "service_name": None, "has_issues": True},
        "scenario": "hallucination_risk",
        "notes":    "Minimal text — Extractor may hallucinate service details. Reviewer must catch.",
    },
    # 6. Noisy text / product name
    {
        "case_id":  "case_006",
        "text":     "shimano deore оптимальне поєднання ціни і якості | 12 швидкостей вистачає",
        "expected": {"sentiment": "positive", "service_name": "shimano", "has_issues": False},
        "scenario": "noisy_product",
        "notes":    "Product route. Shimano known brand, deore is product line.",
    },
    # 7. Fallback needed — reviewer rejects extraction
    {
        "case_id":  "case_007",
        "text":     "служба підтримки скайфлай працює жахливо | дозвонитись майже неможливо",
        "expected": {"sentiment": "negative", "issue_type": "support", "service_name": "скайфлай", "has_issues": False},
        "scenario": "fallback_trigger",
        "notes":    "Clear negative with known brand. Should extract cleanly.",
    },
    # 8. Reviewer rejects — inconsistency
    {
        "case_id":  "case_008",
        "text":     "інтерфейс сайту застарілий та незручний",
        "expected": {"sentiment": "negative", "service_type": None, "has_issues": True},
        "scenario": "reviewer_rejects",
        "notes":    "service_type not identifiable — telecom/web not in schema → missing field warning",
    },
    # 9. Repair helps
    {
        "case_id":  "case_009",
        "text":     "ніколи більше не замовлятиму в цій службі доставки | товар з величезною затримкою",
        "expected": {"sentiment": "negative", "issue_type": "delivery", "service_type": "доставка", "has_issues": False},
        "scenario": "repair_success",
        "notes":    "Should extract delivery + negative sentiment correctly after potential repair.",
    },
    # 10. Repair fails — manual review
    {
        "case_id":  "case_010",
        "text":     "це",
        "expected": {"sentiment": "neutral", "has_issues": True, "needs_manual_review": True},
        "scenario": "manual_review",
        "notes":    "Single word — no extraction possible. Should flag for manual review.",
    },
]

def baseline_single_agent(text: str) -> dict:
    import re
    t = text.lower()
    neg_kw = ["жахлив","погано","розчарован","завищен","занадто","нікол","застарілий"]
    pos_kw = ["чудово","відмінн","найкращ","рекоменду","задоволен","тішить"]
    neg = sum(1 for w in neg_kw if w in t)
    pos = sum(1 for w in pos_kw if w in t)
    sentiment = "positive" if pos > neg else "negative" if neg > pos else "neutral"

    svc_map = {
        "авіакомпанія": ["авіакомпанія","рейс","літак"],
        "кафе":         ["кафе","каву","смузі","кав'ярня"],
        "доставка":     ["доставка","замовлення"],
        "школа":        ["школа","навчання","курс"],
    }
    service_type = None
    for svc, kws in svc_map.items():
        if any(kw in t for kw in kws):
            service_type = svc; break
    return {
        "sentiment":    sentiment,
        "service_type": service_type,
        "service_name": None,
        "issue_type":   None,
        "confidence":   "unknown",
        "validated":    False,
        "reviewer":     "none",
    }

ERROR_ANALYSIS = [
    {
        "case_id":         "case_002",
        "input":           "дуже погане обслуговування",
        "expected_behavior": "identify service_type, issue=support",
        "triager_out":     "route=generic_review, difficulty=low",
        "extractor_out":   "sentiment=negative, service_type=None",
        "reviewer_out":    "repair_needed — service_type missing",
        "fallback_action": "rule_repair: service_type re-extraction attempted",
        "final_out":       "service_type still None — partial output",
        "category":        "extractor missing field",
        "fix":             "Додати keyword 'обслуговування' до service_type dict",
    },
    {
        "case_id":         "case_003",
        "input":           "ресторан непоганий але ціни завищені",
        "expected_behavior": "sentiment=mixed, issue=billing",
        "triager_out":     "route=billing_review",
        "extractor_out":   "sentiment may be negative (neg dominates)",
        "reviewer_out":    "accept_with_warnings — possible mixed missed",
        "fallback_action": "none needed",
        "final_out":       "negative/billing — partially correct",
        "category":        "sentiment ambiguity",
        "fix":             "Покращити mixed-detection: рахувати і pos і neg >0",
    },
    {
        "case_id":         "case_005",
        "input":           "загалом нормально, є певні зауваження",
        "expected_behavior": "neutral, no hallucinations",
        "triager_out":     "route=generic_review",
        "extractor_out":   "sentiment=neutral, service_type=None",
        "reviewer_out":    "accept — no obvious errors but data minimal",
        "fallback_action": "none",
        "final_out":       "minimal extraction — correct that it's empty",
        "category":        "tool output minimal — correct behavior",
        "fix":             "N/A — агент правильно утримався від галюцинацій",
    },
    {
        "case_id":         "case_008",
        "input":           "інтерфейс сайту застарілий та незручний",
        "expected_behavior": "service_type=телеком/веб, sentiment=negative",
        "triager_out":     "route=generic_review (no known service keywords)",
        "extractor_out":   "service_type=None (telecom not in dict)",
        "reviewer_out":    "repair_needed — service_type required but missing",
        "fallback_action": "rule repair: service_type still None",
        "final_out":       "partial — service_type missing, manual_review=True",
        "category":        "missing domain coverage",
        "fix":             "Додати 'інтерфейс','сайту','веб' до SERVICE_TYPE_KW",
    },
    {
        "case_id":         "case_010",
        "input":           "це",
        "expected_behavior": "manual review flagged",
        "triager_out":     "route=generic_review, difficulty=low",
        "extractor_out":   "sentiment=neutral, everything=None",
        "reviewer_out":    "fallback_needed (multiple missing required)",
        "fallback_action": "partial_output + manual_review=True",
        "final_out":       "status=manual_review_required",
        "category":        "repair not possible — degenerate input",
        "fix":             "Мінімальна валідація input (len < 3) before crew start",
    },
    {
        "case_id":         "case_001",
        "input":           "авіакомпанія скайфлай це відмінний вибір",
        "expected_behavior": "accept, routing=positive archive",
        "triager_out":     "route=service_review, known brand",
        "extractor_out":   "sentiment=positive, service_name=скайфлай",
        "reviewer_out":    "accept",
        "fallback_action": "none",
        "final_out":       "clean accept — showcase of correct crew behavior",
        "category":        "correct behavior — positive example",
        "fix":             "N/A",
    },
    {
        "case_id":         "case_004",
        "input":           "платити 100 грн за каву це занадто",
        "expected_behavior": "price=100, currency=UAH, issue=billing",
        "triager_out":     "route=billing_review (price signal)",
        "extractor_out":   "mentioned_price=100, currency=UAH, issue=billing",
        "reviewer_out":    "accept",
        "fallback_action": "none",
        "final_out":       "correct — billing extraction successful",
        "category":        "correct behavior — positive example",
        "fix":             "N/A",
    },
    {
        "case_id":         "case_009",
        "input":           "ніколи більше не замовлятиму в цій службі доставки",
        "expected_behavior": "delivery issue, negative sentiment",
        "triager_out":     "route=service_review",
        "extractor_out":   "sentiment=negative, service_type=доставка, issue=delivery",
        "reviewer_out":    "accept",
        "fallback_action": "none",
        "final_out":       "correct extraction and routing",
        "category":        "correct behavior — delivery use case",
        "fix":             "N/A",
    },
    {
        "case_id":         "case_006",
        "input":           "shimano deore оптимальне поєднання ціни і якості",
        "expected_behavior": "product=shimano, sentiment=positive",
        "triager_out":     "route=product_review (shimano detected)",
        "extractor_out":   "service_name=shimano, sentiment=positive",
        "reviewer_out":    "accept",
        "fallback_action": "none",
        "final_out":       "correct product review extraction",
        "category":        "correct behavior — product review",
        "fix":             "N/A — shimano correctly identified",
    },
    {
        "case_id":         "case_007",
        "input":           "служба підтримки скайфлай жахлива",
        "expected_behavior": "support issue, скайфлай identified",
        "triager_out":     "route=service_review, known brand",
        "extractor_out":   "service_name=скайфлай, issue=support, sentiment=negative",
        "reviewer_out":    "accept",
        "fallback_action": "none",
        "final_out":       "routing: escalate to support team",
        "category":        "correct behavior — support escalation",
        "fix":             "N/A",
    },
]


def error_analysis_df() -> pd.DataFrame:
    return pd.DataFrame(ERROR_ANALYSIS)


def print_metrics(metrics: dict):
    print("=== Crew Metrics ===")
    print(f"  Cases:                  {metrics['n_cases']}")
    print(f"  Valid final rate:        {metrics['valid_final_rate']:.1%}")
    print(f"  Fallback activations:    {metrics['fallback_activation']} ({metrics['fallback_rate']:.1%})")
    print(f"  Fallback success rate:   {metrics['fallback_success_rate']:.1%}")
    print(f"  Manual review rate:      {metrics['manual_review_rate']:.1%}")
    print(f"  Avg agents/case:         {metrics['avg_agents_per_case']}")