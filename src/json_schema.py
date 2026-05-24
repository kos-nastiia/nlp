"""
json_schema.py — ЛР11: JSON schema для extraction відгуків про сервіси.

Extraction-задача:
  З тексту відгуку витягти структурований запис:
  - service_name    (назва компанії/сервісу)
  - service_type    (тип сервісу: авіакомпанія, ресторан, магазин, ...)
  - sentiment       (positive / negative / mixed / neutral)
  - issue_type      (billing, quality, delivery, support, staff, facility, null)
  - mentioned_price (числова сума якщо є, інакше null)
  - currency        (UAH / USD / EUR / null)
  - key_aspect      (головний аспект відгуку — до 10 слів)
  - confidence      (high / medium / low — наскільки модель впевнена)
"""

EXTRACTION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ServiceReviewExtraction",
    "description": "Structured extraction from a service review text.",
    "type": "object",
    "required": [
        "service_name",
        "service_type",
        "sentiment",
        "issue_type",
        "mentioned_price",
        "currency",
        "key_aspect",
        "confidence"
    ],
    "additionalProperties": False,
    "properties": {
        "service_name": {
            "description": "Name of the company or service mentioned. null if not mentioned.",
            "type": ["string", "null"],
            "maxLength": 100
        },
        "service_type": {
            "description": "Category of the service.",
            "type": ["string", "null"],
            "enum": [
                "авіакомпанія",
                "ресторан",
                "кафе",
                "магазин",
                "школа",
                "автосервіс",
                "готель",
                "доставка",
                "медицина",
                "освіта",
                "спорт",
                "інше",
                None
            ]
        },
        "sentiment": {
            "description": "Overall sentiment of the review.",
            "type": "string",
            "enum": ["positive", "negative", "mixed", "neutral"]
        },
        "issue_type": {
            "description": "Main problem category if negative/mixed, else null.",
            "type": ["string", "null"],
            "enum": [
                "billing",
                "quality",
                "delivery",
                "support",
                "staff",
                "facility",
                "logistics",
                None
            ]
        },
        "mentioned_price": {
            "description": "Numeric price if explicitly mentioned, else null.",
            "type": ["number", "null"],
            "minimum": 0
        },
        "currency": {
            "description": "Currency if price mentioned, else null.",
            "type": ["string", "null"],
            "enum": ["UAH", "USD", "EUR", None]
        },
        "key_aspect": {
            "description": "Main aspect of the review in up to 10 words.",
            "type": "string",
            "maxLength": 120
        },
        "confidence": {
            "description": "Model confidence in extraction quality.",
            "type": "string",
            "enum": ["high", "medium", "low"]
        }
    }
}


EXAMPLE_VALID = {
    "service_name": "скайфлай",
    "service_type": "авіакомпанія",
    "sentiment": "negative",
    "issue_type": "logistics",
    "mentioned_price": None,
    "currency": None,
    "key_aspect": "багаж губиться, чемодани пошкоджуються",
    "confidence": "high"
}

EXAMPLE_VALID_2 = {
    "service_name": None,
    "service_type": "кафе",
    "sentiment": "negative",
    "issue_type": "billing",
    "mentioned_price": 100,
    "currency": "UAH",
    "key_aspect": "ціна за каву не відповідає якості",
    "confidence": "high"
}