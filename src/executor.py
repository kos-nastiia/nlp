import re
from flow_state import FlowState

KNOWN_SERVICES_MAP = {
    "скайфлай":     {"type": "авіакомпанія", "category": "transport"},
    "skyfly":       {"type": "авіакомпанія", "category": "transport"},
    "інгліш хаб":   {"type": "школа",        "category": "education"},
    "english hub":  {"type": "школа",        "category": "education"},
    "shimano":      {"type": "бренд",        "category": "sports"},
    "нова пошта":   {"type": "доставка",     "category": "logistics"},
    "монобанк":     {"type": "банк",         "category": "finance"},
    "приватбанк":   {"type": "банк",         "category": "finance"},
    "сонячний рай": {"type": "готель",       "category": "hospitality"},
}

SERVICE_TYPE_KW = {
    "авіакомпанія": ["авіакомпанія", "рейс", "літак", "стюардеса", "переліт"],
    "ресторан":     ["ресторан", "страва", "меню", "їжа", "офіціант"],
    "кафе":         ["кафе", "кав'ярня", "кавярня", "каву", "десерт", "смузі", "бар"],
    "магазин":      ["магазин", "асортимент", "товар", "покупка"],
    "школа":        ["школа", "навчання", "курс", "викладач"],
    "автосервіс":   ["автосервіс", "ремонт", "запчастини", "майстер"],
    "готель":       ["готель", "апартаменти", "номер", "проживання", "бронювання"],
    "доставка":     ["доставка", "замовлення", "кур'єр", "відправили", "посилка"],
    "медицина":     ["клінік", "лікар", "стоматолог", "лікування"],
    "спорт":        ["велосипед", "гальма", "трансмісія", "shimano"],
    "телеком":      ["мобільний", "інтернет", "зв'язку", "мережа"],
}

ISSUE_KW = {
    "billing":  ["ціни", "ціна", "дорого", "завищен", "грн", "вартість", "платити", "шокують"],
    "quality":  ["якість", "пересолен", "погано", "неякісн", "застарілий"],
    "delivery": ["доставка", "затримка", "не приїхало", "губиться"],
    "support":  ["підтримка", "оператор", "дозвонитись"],
    "staff":    ["персонал", "грубо", "неввічлив"],
    "logistics":["багаж", "рейс", "затримується", "скасован"],
}


def execute_step(state: FlowState) -> FlowState:
    if not state.route_ok:
        state.execute_ok = False
        state.status     = "execute_skipped"
        state.add_error("execute", "skipped — route failed")
        state.mark_step("execute", ok=False)
        return state

    text = state.clean_text
    tl   = text.lower()
    route = state.route

    try:
        output = {}

        pos_kw = ["чудово","відмінн","найкращ","рекоменду","задоволен",
                  "чудов","зручн","доступн","тішить","спасибі","оптимальн",
                  "рекомендую","позитивн","добре","швидко"]
        neg_kw = ["жахлив","погано","розчарован","завищен","нікол","неможливо",
                  "застарілий","неякісн","проблем","занадто","шокують","не відповідає",
                  "незадоволен","розчарував","затримк"]
        pos = sum(1 for kw in pos_kw if kw in tl)
        neg = sum(1 for kw in neg_kw if kw in tl)
        output["sentiment"] = (
            "positive" if pos > neg else
            "negative" if neg > pos else
            "mixed"    if pos == neg > 0 else
            "neutral"
        )

        svc_sc = {s: sum(1 for kw in kws if kw in tl)
                  for s, kws in SERVICE_TYPE_KW.items()}
        svc_sc = {k: v for k, v in svc_sc.items() if v > 0}
        output["service_type"] = max(svc_sc, key=svc_sc.get) if svc_sc else None

        output["service_name"] = next(
            (n for n in sorted(KNOWN_SERVICES_MAP, key=len, reverse=True) if n in tl),
            None
        )

        if output["sentiment"] in ("negative", "mixed"):
            issue_sc = {i: sum(1 for kw in kws if kw in tl)
                        for i, kws in ISSUE_KW.items()}
            issue_sc = {k: v for k, v in issue_sc.items() if v > 0}
            output["issue_type"] = max(issue_sc, key=issue_sc.get) if issue_sc else None
        else:
            output["issue_type"] = None

        pm = re.search(r'(\d+(?:[–\-]\d+)?)\s*(грн|гривень|\$|євро|%)', text, re.I)
        if pm:
            try:
                output["mentioned_price"] = float(pm.group(1).split("–")[0].split("-")[0])
            except ValueError:
                output["mentioned_price"] = None
            c = pm.group(2).lower()
            output["currency"] = (
                "UAH"     if c in ("грн","гривень") else
                "USD"     if c == "$" else
                "EUR"     if c == "євро" else
                "PERCENT"
            )
        else:
            output["mentioned_price"] = None
            output["currency"]        = None

        words = [w for w in text.split() if w != "|" and len(w) > 3]
        output["key_aspect"] = " ".join(words[:8]) if words else text[:60]

        required = state.required_fields
        found    = sum(1 for f in required if output.get(f) is not None)
        cr       = found / len(required) if required else 1.0
        output["confidence"] = (
            "high"   if cr >= 0.8 else
            "medium" if cr >= 0.5 else
            "low"
        )

        state.execute_output    = output
        state.execution_method  = "keyword_heuristic_with_regex"
        state.execute_confidence = output["confidence"]
        state.execute_ok        = True
        state.status            = "executed"

    except Exception as e:
        state.execute_ok = False
        state.status     = "execute_failed"
        state.add_error("execute", str(e))

    state.mark_step("execute", ok=state.execute_ok)
    return state