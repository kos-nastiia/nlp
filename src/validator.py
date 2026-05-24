import re
from flow_state import FlowState

SENTIMENT_ENUMS = {"positive", "negative", "mixed", "neutral"}
CONFIDENCE_ENUMS = {"high", "medium", "low"}


def validate_step(state: FlowState) -> FlowState:
    if not state.execute_ok:
        state.validation_ok  = False
        state.recommended_action = "fallback_or_manual_review"
        state.status         = "validate_skipped"
        state.add_error("validate", "skipped — execute failed")
        state.mark_step("validate", ok=False)
        return state

    text   = state.clean_text.lower()
    output = state.execute_output
    issues = []

    required = state.required_fields
    # Sentiment-aware: issue_type not required for positive sentiment
    effective_required = [
        f for f in required
        if not (f == "issue_type" and output.get("sentiment") == "positive")
    ]
    missing  = [f for f in effective_required if output.get(f) is None]
    for f in missing:
        issues.append({"field": f, "problem": f"required field '{f}' is missing"})
    required_ok = len(missing) == 0

    schema_ok = True
    if output.get("sentiment") not in SENTIMENT_ENUMS:
        issues.append({"field": "sentiment",
                       "problem": f"invalid value '{output.get('sentiment')}'"})
        schema_ok = False
    if output.get("confidence") not in CONFIDENCE_ENUMS:
        issues.append({"field": "confidence",
                       "problem": f"invalid value '{output.get('confidence')}'"})
        schema_ok = False
    if output.get("mentioned_price") is not None:
        if not isinstance(output["mentioned_price"], (int, float)):
            issues.append({"field": "mentioned_price",
                           "problem": "must be numeric"})
            schema_ok = False

    consistency_ok = True
    neg_sig = any(kw in text for kw in
                  ["жахлив","погано","розчарован","нікол","занадто","не відповідає"])
    pos_sig = any(kw in text for kw in
                  ["чудово","відмінн","найкращ","задоволен","тішить","рекомендую"])

    if output.get("sentiment") == "positive" and neg_sig and not pos_sig:
        issues.append({"field": "sentiment",
                       "problem": "positive but strong negative signals in text"})
        consistency_ok = False
    if output.get("sentiment") == "negative" and pos_sig and not neg_sig:
        issues.append({"field": "sentiment",
                       "problem": "negative but strong positive signals in text"})
        consistency_ok = False
    if output.get("sentiment") == "positive" and output.get("issue_type"):
        issues.append({"field": "issue_type",
                       "problem": "issue_type set but sentiment=positive"})
        consistency_ok = False

    if output.get("mentioned_price") is not None:
        if not re.search(r'\d+\s*(грн|гривень|\$|євро)', state.clean_text, re.I):
            issues.append({"field": "mentioned_price",
                           "problem": "price in output but no numeric price in text — hallucination risk"})
            consistency_ok = False

    if output.get("service_name"):
        if output["service_name"].lower() not in state.clean_text.lower():
            issues.append({"field": "service_name",
                           "problem": f"service_name not found in text — hallucination risk"})
            consistency_ok = False

    if output.get("confidence") == "low":
        issues.append({"field": "confidence",
                       "problem": "low confidence — extraction may be incomplete"})

    hallucination = any("hallucination" in i["problem"] for i in issues)
    critical      = [i for i in issues if any(
        kw in i["problem"] for kw in ["hallucination","required","not found in text"]
    )]

    if not issues:
        action          = "export"
        validation_ok   = True
    elif hallucination or len(critical) >= 2:
        action          = "fallback_needed"
        validation_ok   = False
    elif critical:
        action          = "repair_and_export_with_warning"
        validation_ok   = False
    else:
        action          = "export_with_warnings"
        validation_ok   = True

    state.validation_ok      = validation_ok
    state.schema_ok          = schema_ok
    state.required_ok        = required_ok
    state.consistency_ok     = consistency_ok
    state.validation_issues  = issues
    state.recommended_action = action
    state.status             = "validated" if validation_ok else "validation_failed"

    for issue in issues:
        state.add_warning("validate", f"{issue['field']}: {issue['problem']}")

    state.mark_step("validate", ok=validation_ok)
    return state


def _post_init_fix(state):
    pass