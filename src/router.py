import re
from flow_state import FlowState


SCHEMAS = {
    "support_classification": {
        "required": ["sentiment", "service_type", "issue_type"],
        "optional": ["service_name", "key_aspect"],
    },
    "billing_extraction": {
        "required": ["sentiment", "service_type", "mentioned_price", "currency"],
        "optional": ["service_name", "issue_type", "key_aspect"],
    },
    "product_feedback": {
        "required": ["sentiment", "service_name", "key_aspect"],
        "optional": ["service_type", "issue_type", "mentioned_price"],
    },
    "delivery_complaint": {
        "required": ["sentiment", "service_type", "issue_type", "key_aspect"],
        "optional": ["service_name", "mentioned_price"],
    },
    "generic_feedback": {
        "required": ["sentiment", "key_aspect"],
        "optional": ["service_name", "service_type", "issue_type"],
    },
    "manual_review": {
        "required": [],
        "optional": [],
    },
}

ROUTE_KEYWORDS = {
    "billing_extraction": [
        r"\d+\s*(грн|гривень|\$|євро|%)",
        r"ціни?|вартість|платити|дорого|завищен|коштує",
    ],
    "product_feedback": [
        r"shimano|wh[-]?\d+|deore|xiaomi|apple|samsung",
    ],
    "delivery_complaint": [
        r"доставк|замовлен|відправили|посилк|кур'єр|затримк",
    ],
    "support_classification": [
        r"підтримка|оператор|дозвонитись|скайфлай|інгліш хаб",
        r"авіакомпанія|ресторан|кафе|готел|клінік",
    ],
}

KNOWN_SERVICES = [
    "скайфлай", "skyfly", "інгліш хаб", "english hub",
    "shimano", "нова пошта", "монобанк", "приватбанк", "сонячний рай",
]


def route_step(state: FlowState) -> FlowState:
    text = state.clean_text.lower()
    reasons = []

    # Guard: empty text
    if not text.strip() or state.word_count < 2:
        state.route          = "manual_review"
        state.task_type      = "unknown"
        state.schema_name    = "manual_review"
        state.required_fields = []
        state.optional_fields = []
        state.routing_reason = "text too short or empty — cannot route"
        state.route_ok       = False
        state.status         = "route_failed"
        state.add_error("route", "input too short for routing")
        state.add_warning("route", "manual review required")
        state.mark_step("route", ok=False)
        return state

    # Scoring per route
    scores: dict[str, int] = {r: 0 for r in ROUTE_KEYWORDS}

    for route, patterns in ROUTE_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                scores[route] += 1
                reasons.append(f"{route}: matched '{pat}'")

    if any(s in text for s in KNOWN_SERVICES):
        scores["support_classification"] = scores.get("support_classification", 0) + 2
        reasons.append("support_classification: known service detected")

    best_score = max(scores.values()) if scores else 0

    if best_score == 0:
        route    = "generic_feedback"
        task_type = "general_review"
        reason   = "no specific keywords found — generic fallback route"
    else:
        # Tie-break: billing > delivery > support > product > generic
        priority = ["billing_extraction", "delivery_complaint",
                    "support_classification", "product_feedback", "generic_feedback"]
        candidates = [r for r in priority if scores.get(r, 0) == best_score]
        route    = candidates[0]
        task_type = route
        reason   = "; ".join([r for r in reasons if r.startswith(route)])

    schema   = SCHEMAS.get(route, SCHEMAS["generic_feedback"])

    state.route           = route
    state.task_type       = task_type
    state.schema_name     = route
    state.required_fields = schema["required"]
    state.optional_fields = schema["optional"]
    state.routing_reason  = reason or f"matched route: {route}"
    state.route_ok        = True
    state.status          = "routed"
    state.mark_step("route")
    return state