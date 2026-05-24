import re
from typing import Optional

KNOWN_SERVICES = {
    "скайфлай":    {"type": "авіакомпанія", "category": "transport"},
    "skyfly":      {"type": "авіакомпанія", "category": "transport"},
    "інгліш хаб":  {"type": "школа",        "category": "education"},
    "english hub": {"type": "школа",        "category": "education"},
    "shimano":     {"type": "бренд",        "category": "sports"},
    "нова пошта":  {"type": "доставка",     "category": "logistics"},
    "новапошта":   {"type": "доставка",     "category": "logistics"},
    "укрпошта":    {"type": "доставка",     "category": "logistics"},
    "приватбанк":  {"type": "банк",         "category": "finance"},
    "монобанк":    {"type": "банк",         "category": "finance"},
    "сонячний рай":{"type": "готель",       "category": "hospitality"},
}

ISSUE_KEYWORDS = {
    "billing":  ["ціни", "ціна", "дорого", "завищен", "грн", "вартість", "оплат", "платити", "коштує"],
    "quality":  ["якість", "якост", "пересолен", "погано", "неякісн", "застарілий", "неякісні"],
    "delivery": ["доставка", "доставки", "затримка", "затримк", "не приїхало", "повернення"],
    "support":  ["підтримка", "оператор", "дозвонитись", "служба", "відповідь", "ігнорують"],
    "staff":    ["персонал", "співробітник", "стюардеса", "офіціант", "грубо", "неввічлив"],
    "facility": ["номер", "кімната", "інтер'єр", "інтерєр", "холодний", "брудн", "зношен"],
    "logistics":["багаж", "рейс", "затримується", "скасован", "запізнення"],
}

SERVICE_TYPE_KEYWORDS = {
    "авіакомпанія": ["авіакомпанія", "рейс", "літак", "аеропорт", "стюардеса", "посадка", "переліт"],
    "ресторан":     ["ресторан", "страва", "меню", "кухня", "їжа", "офіціант", "заклад харчування"],
    "кафе":         ["кафе", "кав'ярня", "кавярня", "каву", "десерт", "смузі"],
    "магазин":      ["магазин", "асортимент", "товар", "покупка", "полиці", "продукт"],
    "школа":        ["школа", "навчання", "курс", "викладач", "урок", "англійська", "освіта"],
    "автосервіс":   ["автосервіс", "ремонт", "запчастини", "майстер", "обладнання", "автомобіл"],
    "готель":       ["готель", "номер", "заселення", "проживання", "відпочинок", "бронювання"],
    "доставка":     ["доставка", "замовлення", "кур'єр", "відправили", "отримав", "посилка"],
    "медицина":     ["клінік", "лікар", "стоматолог", "лікування", "прийом", "аналіз"],
    "спорт":        ["велосипед", "гальма", "трансмісія", "шоолам", "shimano", "тренування"],
}


def classify_review(text: str) -> dict:
    if not text or not isinstance(text, str):
        return {"error": "text must be non-empty string"}

    text_lower = text.lower()

    pos_kw = ["чудово", "відмінн", "чудов", "прекрасн", "задоволен", "найкращ",
              "рекоменду", "дякую", "дякую", "позитивн", "professional", "профес",
              "зручн", "доступн", "швидко", "якісн", "задоволен", "спасибі", "тішить"]
    neg_kw = ["жахлив", "погано", "розчарован", "завищен", "проблем", "нікол",
              "неможливо", "застарілий", "неякісн", "бруд", "холодн", "грубо",
              "не відповідає", "незадоволен", "огидн", "жахл", "сміттєзвалищ"]

    pos_count = sum(1 for kw in pos_kw if kw in text_lower)
    neg_count = sum(1 for kw in neg_kw if kw in text_lower)

    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    elif pos_count == neg_count and pos_count > 0:
        sentiment = "mixed"
    else:
        sentiment = "neutral"

    issue_type = None
    issue_scores = {}
    for issue, keywords in ISSUE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            issue_scores[issue] = score
    if issue_scores and sentiment in ("negative", "mixed"):
        issue_type = max(issue_scores, key=issue_scores.get)

    # Service type
    service_type = None
    svc_scores = {}
    for svc, keywords in SERVICE_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            svc_scores[svc] = score
    if svc_scores:
        service_type = max(svc_scores, key=svc_scores.get)

    confidence = "high" if max(pos_count, neg_count) >= 2 else "medium" if max(pos_count, neg_count) == 1 else "low"

    return {
        "sentiment":    sentiment,
        "issue_type":   issue_type,
        "service_type": service_type,
        "confidence":   confidence,
    }

def extract_entities(text: str) -> dict:
    if not text or not isinstance(text, str):
        return {"error": "text must be non-empty string"}

    text_lower = text.lower()

    # Service name lookup
    service_name = None
    matched_service_info = None
    for name in sorted(KNOWN_SERVICES.keys(), key=len, reverse=True):
        if name in text_lower:
            service_name = name
            matched_service_info = KNOWN_SERVICES[name]
            break

    # Price extraction
    price_match = re.search(
        r'(\d+(?:[–\-]\d+)?)\s*(грн|гривень|гривні|\$|євро|%)',
        text, re.IGNORECASE
    )
    mentioned_price = None
    currency = None
    raw_price_text = None

    if price_match:
        raw_price_text = price_match.group(0)
        price_str = price_match.group(1).split('–')[0].split('-')[0]
        try:
            mentioned_price = float(price_str)
        except ValueError:
            mentioned_price = None

        curr_raw = price_match.group(2).lower()
        if curr_raw in ("грн", "гривень", "гривні"):
            currency = "UAH"
        elif curr_raw == "$":
            currency = "USD"
        elif curr_raw == "євро":
            currency = "EUR"
        elif curr_raw == "%":
            currency = "PERCENT"

    return {
        "service_name":       service_name,
        "service_info":       matched_service_info,
        "mentioned_price":    mentioned_price,
        "currency":           currency,
        "raw_price_text":     raw_price_text,
    }

def validate_required_fields(data: dict) -> dict:
    if not isinstance(data, dict):
        return {"error": "data must be a dict"}

    REQUIRED = ["sentiment", "service_type"]
    OPTIONAL  = ["service_name", "issue_type", "mentioned_price"]

    missing = [f for f in REQUIRED if f not in data or data[f] is None]
    warnings = []

    if data.get("sentiment") == "negative" and not data.get("issue_type"):
        warnings.append("negative sentiment but issue_type is missing")
    if data.get("mentioned_price") and not data.get("currency"):
        warnings.append("mentioned_price present but currency is missing")
    if data.get("confidence") == "low":
        warnings.append("confidence is low — extraction may be unreliable")

    present_optional = [f for f in OPTIONAL if data.get(f) is not None]
    score = round(len(present_optional) / len(OPTIONAL), 2)

    return {
        "valid":          len(missing) == 0,
        "missing_fields": missing,
        "warnings":       warnings,
        "completeness_score": score,
    }


def lookup_known_service(text: str) -> dict:
    if not text or not isinstance(text, str):
        return {"error": "text must be non-empty string"}

    text_lower = text.lower()
    matches = []
    for name, info in KNOWN_SERVICES.items():
        if name in text_lower:
            matches.append({"name": name, **info})

    return {
        "found":   len(matches) > 0,
        "matches": matches,
        "count":   len(matches),
    }


def score_review_completeness(data: dict) -> dict:
    if not isinstance(data, dict):
        return {"error": "data must be a dict"}

    fields = ["sentiment", "service_type", "service_name",
              "issue_type", "mentioned_price"]
    present = sum(1 for f in fields if data.get(f) is not None)
    score = round(present / len(fields), 2)

    level = "complete" if score >= 0.8 else "partial" if score >= 0.4 else "minimal"
    missing = [f for f in fields if data.get(f) is None]

    return {"score": score, "level": level, "missing_context": missing}