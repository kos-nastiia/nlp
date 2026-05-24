import json
import re
from json_schema import EXTRACTION_SCHEMA, EXAMPLE_VALID



SYSTEM_PROMPT = """You are a structured data extraction engine.
Your ONLY task is to extract information from Ukrainian service review texts
and return it as a single valid JSON object — nothing else.

Rules:
- Return ONLY the JSON object. No markdown, no explanation, no comments.
- Every response must start with {{ and end with }}.
- Use null (not "null", not "None", not "") for missing values.
- Adhere strictly to the field names and allowed values below.

Required output fields:
  service_name    : string or null — name of company/service mentioned
  service_type    : one of [авіакомпанія, ресторан, кафе, магазин, школа,
                    автосервіс, готель, доставка, медицина, освіта, спорт, інше]
                    or null if unclear
  sentiment       : one of [positive, negative, mixed, neutral]
  issue_type      : one of [billing, quality, delivery, support, staff,
                    facility, logistics] or null if sentiment is positive
  mentioned_price : number (digits only, no currency symbol) or null
  currency        : one of [UAH, USD, EUR] or null
  key_aspect      : string, max 10 words — main point of the review
  confidence      : one of [high, medium, low]

Example output:
{example}
""".format(example=json.dumps(EXAMPLE_VALID, ensure_ascii=False, indent=2))


EXTRACTION_PROMPT_TEMPLATE = """{system}

Text to analyze:
\"\"\"{text}\"\"\"

Return only the JSON object:"""


# ── Repair промпт ─────────────────────────────────────────────────────────

REPAIR_PROMPT_TEMPLATE = """The previous extraction attempt produced invalid output.

Original text:
\"\"\"{text}\"\"\"

Your previous (broken) output:
{broken_output}

Validation error:
{error_message}

Fix the output. Return ONLY a valid JSON object with these exact fields:
service_name, service_type, sentiment, issue_type, mentioned_price,
currency, key_aspect, confidence.

No markdown, no text outside the JSON. Start with {{ end with }}.

Corrected JSON:"""


def call_llm(prompt: str, model: str = "claude-sonnet-4-20250514",
             max_tokens: int = 512) -> str:
    import requests

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"Content-Type": "application/json"},
        json={
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    content = data.get("content", [])
    text_blocks = [b["text"] for b in content if b.get("type") == "text"]
    return "".join(text_blocks)


def build_extraction_prompt(text: str) -> str:
    return EXTRACTION_PROMPT_TEMPLATE.format(system=SYSTEM_PROMPT, text=text)


def build_repair_prompt(text: str, broken_output: str, error_message: str) -> str:
    return REPAIR_PROMPT_TEMPLATE.format(
        text=text,
        broken_output=broken_output,
        error_message=error_message,
    )


def extract_one(text: str, model: str = "claude-sonnet-4-20250514") -> str:
    prompt = build_extraction_prompt(text)
    return call_llm(prompt, model=model)


def repair_one(text: str, broken_output: str, error_message: str,
               model: str = "claude-sonnet-4-20250514") -> str:
    prompt = build_repair_prompt(text, broken_output, error_message)
    return call_llm(prompt, model=model)