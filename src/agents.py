import re

KNOWN_SERVICES = {
    "скайфлай":     {"type": "авіакомпанія", "category": "transport"},
    "skyfly":       {"type": "авіакомпанія", "category": "transport"},
    "інгліш хаб":   {"type": "школа",        "category": "education"},
    "english hub":  {"type": "школа",        "category": "education"},
    "shimano":      {"type": "бренд",        "category": "sports"},
    "нова пошта":   {"type": "доставка",     "category": "logistics"},
    "новапошта":    {"type": "доставка",     "category": "logistics"},
    "приватбанк":   {"type": "банк",         "category": "finance"},
    "монобанк":     {"type": "банк",         "category": "finance"},
    "сонячний рай": {"type": "готель",       "category": "hospitality"},
}

SCHEMAS = {
    "billing_review": {
        "required": ["sentiment", "service_type", "issue_type", "mentioned_price", "currency"],
        "optional": ["service_name", "key_aspect"],
    },
    "service_review": {
        "required": ["sentiment", "service_type", "key_aspect"],
        "optional": ["service_name", "issue_type"],
    },
    "product_review": {
        "required": ["sentiment", "service_name", "key_aspect"],
        "optional": ["service_type", "issue_type", "mentioned_price"],
    },
    "generic_review": {
        "required": ["sentiment", "key_aspect"],
        "optional": ["service_name", "service_type", "issue_type"],
    },
}

SERVICE_TYPE_KW = {
    "авіакомпанія": ["авіакомпанія", "рейс", "літак", "аеропорт", "стюардеса", "переліт"],
    "ресторан":     ["ресторан", "страва", "меню", "їжа", "офіціант"],
    "кафе":         ["кафе", "кав'ярня", "кавярня", "каву", "десерт", "смузі", "бар"],
    "магазин":      ["магазин", "асортимент", "товар", "покупка", "продукт"],
    "школа":        ["школа", "навчання", "курс", "викладач", "урок", "освіта"],
    "автосервіс":   ["автосервіс", "ремонт", "запчастини", "майстер", "автомобіл"],
    "готель":       ["готель", "номер", "заселення", "проживання", "бронювання"],
    "доставка":     ["доставка", "замовлення", "кур'єр", "відправили", "посилка"],
    "медицина":     ["клінік", "лікар", "стоматолог", "лікування", "аналіз"],
    "спорт":        ["велосипед", "гальма", "трансмісія", "shimano", "тренування"],
    "телеком":      ["мобільний", "інтернет", "зв'язку", "оператор", "мережа"],
}

ISSUE_KW = {
    "billing":  ["ціни", "ціна", "дорого", "завищен", "грн", "вартість", "платити", "шокують"],
    "quality":  ["якість", "якост", "пересолен", "погано", "неякісн", "застарілий", "поганий"],
    "delivery": ["доставка", "затримка", "не приїхало", "повернення", "губиться"],
    "support":  ["підтримка", "оператор", "дозвонитись", "служба", "відповідь"],
    "staff":    ["персонал", "співробітник", "грубо", "неввічлив"],
    "facility": ["номер", "інтер'єр", "холодний", "брудн", "зношен"],
    "logistics":["багаж", "рейс", "затримується", "скасован"],
}


class TriagerAgent:
    NAME = "Triager"

    def run(self, text: str) -> dict:
        t = text.lower()
        has_price   = bool(re.search(r'\d+\s*(грн|гривень|\$|євро|%)', text, re.I))
        has_known   = any(s in t for s in KNOWN_SERVICES)
        has_product = any(kw in t for kw in ["shimano", "wh1000", "deore"])
        has_svc     = any(any(kw in t for kw in kws) for kws in SERVICE_TYPE_KW.values())

        if has_price and has_svc:
            route, task_type = "billing_review",  "billing_complaint"
        elif has_product:
            route, task_type = "product_review",  "product_feedback"
        elif has_svc or has_known:
            route, task_type = "service_review",  "service_feedback"
        else:
            route, task_type = "generic_review",  "generic_text"

        schema   = SCHEMAS[route]
        n_words  = len(text.split())
        difficulty = "low" if n_words < 8 else "medium" if n_words < 20 else "high"

        notes = []
        if has_price:   notes.append("explicit price signal")
        if has_known:   notes.append("known service brand")
        if has_product: notes.append("product name detected")
        if n_words < 8: notes.append("very short — extraction risk")

        return {
            "agent":           self.NAME,
            "task_type":       task_type,
            "route":           route,
            "required_fields": schema["required"],
            "optional_fields": schema["optional"],
            "difficulty":      difficulty,
            "notes":           "; ".join(notes) or "standard",
        }


class ExtractorAgent:
    NAME = "Extractor"

    def run(self, text: str, triage: dict) -> dict:
        t = text.lower()

        # sentiment
        pos = sum(1 for kw in ["чудово","відмінн","найкращ","рекоменду","задоволен",
                                "чудов","зручн","доступн","тішить","спасибі","оптимальн"] if kw in t)
        neg = sum(1 for kw in ["жахлив","погано","розчарован","завищен","нікол",
                                "неможливо","застарілий","неякісн","проблем","занадто","шокують"] if kw in t)
        sentiment = "positive" if pos > neg else "negative" if neg > pos else \
                    "mixed" if pos == neg > 0 else "neutral"

        # service_type
        svc_sc = {s: sum(1 for kw in kws if kw in t) for s, kws in SERVICE_TYPE_KW.items()}
        svc_sc = {k: v for k, v in svc_sc.items() if v > 0}
        service_type = max(svc_sc, key=svc_sc.get) if svc_sc else None

        # service_name
        service_name = next((n for n in sorted(KNOWN_SERVICES, key=len, reverse=True) if n in t), None)

        # issue_type
        if sentiment in ("negative", "mixed"):
            issue_sc = {i: sum(1 for kw in kws if kw in t) for i, kws in ISSUE_KW.items()}
            issue_sc = {k: v for k, v in issue_sc.items() if v > 0}
            issue_type = max(issue_sc, key=issue_sc.get) if issue_sc else None
        else:
            issue_type = None

        # price
        pm = re.search(r'(\d+(?:[–\-]\d+)?)\s*(грн|гривень|\$|євро|%)', text, re.I)
        if pm:
            try:
                mentioned_price = float(pm.group(1).split("–")[0].split("-")[0])
            except ValueError:
                mentioned_price = None
            c = pm.group(2).lower()
            currency = "UAH" if c in ("грн","гривень") else "USD" if c=="$" else \
                       "EUR" if c=="євро" else "PERCENT"
        else:
            mentioned_price, currency = None, None

        # key_aspect
        words = [w for w in text.split() if w != "|" and len(w) > 3]
        key_aspect = " ".join(words[:8]) if words else text[:50]

        # confidence
        required = triage.get("required_fields", [])
        extracted = {"sentiment": sentiment, "service_type": service_type,
                     "service_name": service_name, "issue_type": issue_type,
                     "mentioned_price": mentioned_price, "currency": currency,
                     "key_aspect": key_aspect}
        found = sum(1 for f in required if extracted.get(f) is not None)
        cr = found / len(required) if required else 1.0
        confidence = "high" if cr >= 0.8 else "medium" if cr >= 0.5 else "low"

        return {
            "agent":           self.NAME,
            "sentiment":       sentiment,
            "service_type":    service_type,
            "service_name":    service_name,
            "issue_type":      issue_type,
            "mentioned_price": mentioned_price,
            "currency":        currency,
            "key_aspect":      key_aspect,
            "confidence":      confidence,
        }

class ReviewerAgent:
    NAME = "Reviewer"

    def run(self, text: str, extraction: dict, triage: dict) -> dict:
        t = text.lower()
        required = triage.get("required_fields", [])
        issues = []

        missing = [f for f in required if extraction.get(f) is None]
        for f in missing:
            issues.append({"field": f, "problem": f"required '{f}' is missing"})

        neg_sig = any(kw in t for kw in ["жахлив","погано","розчарован","нікол","занадто"])
        pos_sig = any(kw in t for kw in ["чудово","відмінн","найкращ","задоволен","тішить"])
        if extraction.get("sentiment") == "positive" and neg_sig and not pos_sig:
            issues.append({"field": "sentiment", "problem": "positive but text has strong negative signals"})
        if extraction.get("sentiment") == "negative" and pos_sig and not neg_sig:
            issues.append({"field": "sentiment", "problem": "negative but text has strong positive signals"})

        if extraction.get("mentioned_price") is not None:
            if not re.search(r'\d+\s*(грн|гривень|\$|євро)', text, re.I):
                issues.append({"field": "mentioned_price",
                                "problem": "price in extraction but no numeric price in text — hallucination risk"})

        if extraction.get("service_name"):
            if extraction["service_name"].lower() not in t:
                issues.append({"field": "service_name",
                                "problem": f"service_name '{extraction['service_name']}' not in text"})

        if extraction.get("sentiment") == "positive" and extraction.get("issue_type"):
            issues.append({"field": "issue_type",
                           "problem": "issue_type set but sentiment=positive — inconsistent"})

        if extraction.get("confidence") == "low":
            issues.append({"field": "confidence", "problem": "low confidence extraction"})

        hallucination = any("hallucination" in i["problem"] for i in issues)
        critical = [i for i in issues if any(
            kw in i["problem"] for kw in ["hallucination","not in text","required"]
        )]

        if not issues:
            verdict, action = "accept",                "finalize"
        elif hallucination or len(critical) >= 2:
            verdict, action = "fallback_needed",       "run_fallback_or_manual_review"
        elif critical:
            verdict, action = "repair_needed",         "repair_flagged_fields"
        else:
            verdict, action = "accept_with_warnings",  "finalize_with_warnings"

        return {
            "agent":              self.NAME,
            "verdict":            verdict,
            "schema_ok":          len(missing) == 0,
            "consistency_ok":     not any("signal" in i["problem"] or "inconsistent" in i["problem"]
                                          for i in issues),
            "missing_required":   missing,
            "hallucination_risk": hallucination,
            "issues":             issues,
            "recommended_action": action,
            "issues_count":       len(issues),
        }