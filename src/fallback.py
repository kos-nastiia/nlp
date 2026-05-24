import re
from flow_state import FlowState

KNOWN_SERVICES_MAP = {
    "скайфлай": "авіакомпанія", "інгліш хаб": "школа",
    "shimano": "спорт", "нова пошта": "доставка",
    "монобанк": "банк", "приватбанк": "банк",
}

SERVICE_TYPE_KW = {
    "авіакомпанія": ["авіакомпанія", "рейс", "літак"],
    "кафе":         ["кафе", "кав'ярня", "каву", "смузі"],
    "ресторан":     ["ресторан", "їжа", "страва"],
    "доставка":     ["доставка", "замовлення", "кур'єр"],
    "школа":        ["школа", "навчання", "курс"],
    "готель":       ["готель", "апартаменти", "проживання"],
    "медицина":     ["клінік", "лікар", "лікування"],
}

ISSUE_KW = {
    "billing":  ["ціни", "ціна", "завищен", "грн", "платити", "шокують"],
    "quality":  ["якість", "погано", "неякісн"],
    "delivery": ["доставка", "затримка", "губиться"],
    "support":  ["підтримка", "оператор", "дозвонитись"],
    "logistics":["багаж", "рейс", "затримується"],
}


def fallback_step(state: FlowState, max_attempts: int = 2) -> FlowState:
    action = state.recommended_action or ""

    if action in ("export", "export_with_warnings") and not state.fallback_triggered:
        # Fallback не потрібен
        return state

    state.fallback_triggered = True
    state.fallback_attempt  += 1
    text = state.clean_text.lower()
    output = dict(state.execute_output)
    repaired = []

    issues = state.validation_issues or []

    for issue in issues:
        field   = issue.get("field", "")
        problem = issue.get("problem", "")

        if field == "sentiment" and "signal" in problem:
            neg = any(kw in text for kw in ["жахлив","погано","розчарован","занадто","нікол"])
            pos = any(kw in text for kw in ["чудово","відмінн","найкращ","задоволен","тішить"])
            fixed = "negative" if neg and not pos else "positive" if pos and not neg else "mixed"
            output["sentiment"] = fixed
            repaired.append(f"sentiment → {fixed} (rule-fixed)")

        # Nullify hallucinated price
        if field == "mentioned_price" and "hallucination" in problem:
            pm = re.search(r'(\d+)\s*(грн|gривень|\$|євро)', state.clean_text, re.I)
            if pm:
                try:
                    output["mentioned_price"] = float(pm.group(1))
                    output["currency"] = "UAH" if pm.group(2).lower() in ("грн","гривень") else "USD"
                    repaired.append(f"mentioned_price re-verified: {output['mentioned_price']}")
                except Exception:
                    output["mentioned_price"] = None
                    output["currency"]        = None
                    repaired.append("mentioned_price nullified (hallucination)")
            else:
                output["mentioned_price"] = None
                output["currency"]        = None
                repaired.append("mentioned_price nullified (hallucination confirmed)")

        # Nullify hallucinated service_name
        if field == "service_name" and "not found in text" in problem:
            real = next((n for n in sorted(KNOWN_SERVICES_MAP, key=len, reverse=True)
                         if n in text), None)
            output["service_name"] = real
            repaired.append(f"service_name → {real} (re-verified)")

        # Fix issue_type on positive sentiment
        if field == "issue_type" and "positive" in problem:
            output["issue_type"] = None
            repaired.append("issue_type nullified (sentiment=positive)")

        # Recover missing required fields
        if "required field" in problem and "missing" in problem:
            if field == "service_type":
                svc_sc = {s: sum(1 for kw in kws if kw in text)
                          for s, kws in SERVICE_TYPE_KW.items()}
                svc_sc = {k: v for k, v in svc_sc.items() if v > 0}
                if svc_sc:
                    output["service_type"] = max(svc_sc, key=svc_sc.get)
                    repaired.append(f"service_type recovered: {output['service_type']}")
            elif field == "issue_type":
                iss_sc = {i: sum(1 for kw in kws if kw in text)
                          for i, kws in ISSUE_KW.items()}
                iss_sc = {k: v for k, v in iss_sc.items() if v > 0}
                if iss_sc:
                    output["issue_type"] = max(iss_sc, key=iss_sc.get)
                    repaired.append(f"issue_type recovered: {output['issue_type']}")

    required = state.required_fields
    still_missing = [f for f in required if output.get(f) is None]

    if repaired and not still_missing:
        strategy    = "rule_repair"
        fallback_ok = True
        state.execute_output = output
        state.validation_ok  = True
        state.status         = "repaired"
        for r in repaired:
            state.add_warning("fallback", f"repaired: {r}")

    elif state.fallback_attempt >= max_attempts:
        strategy    = "safe_failure"
        fallback_ok = False
        state.needs_manual_review = True
        state.status = "manual_review_required"
        for f in still_missing:
            state.add_warning("fallback", f"field '{f}' still missing after {state.fallback_attempt} attempts")

    else:
        strategy    = "partial_export"
        fallback_ok = False
        state.needs_manual_review = True
        state.status = "partial"
        state.add_warning("fallback", "partial output — some required fields missing")

    state.fallback_strategy = strategy
    state.fallback_ok       = fallback_ok
    state.execute_output    = output
    state.mark_step("fallback", ok=fallback_ok)
    return state