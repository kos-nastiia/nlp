import json
import re
from typing import Tuple, Optional, Dict, Any

try:
    import jsonschema
    _JSONSCHEMA_AVAILABLE = True
except ImportError:
    _JSONSCHEMA_AVAILABLE = False
    print("Warning: jsonschema not installed. Run: pip install jsonschema")

from json_schema import EXTRACTION_SCHEMA


def extract_json_from_text(text: str) -> str:
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)

    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)

    return text


def validate(raw_output: str) -> Dict[str, Any]:
    result = {
        "parse_ok":      False,
        "schema_ok":     False,
        "data":          None,
        "parse_error":   None,
        "schema_error":  None,
        "extracted_text": "",
    }

    # Крок 1: витягнення JSON з тексту
    cleaned = extract_json_from_text(raw_output.strip())
    result["extracted_text"] = cleaned

    # Крок 2: parse
    try:
        data = json.loads(cleaned)
        result["parse_ok"] = True
        result["data"] = data
    except json.JSONDecodeError as e:
        result["parse_error"] = str(e)
        return result

    # Крок 3: schema validation
    if not _JSONSCHEMA_AVAILABLE:
        # Мінімальна ручна перевірка якщо jsonschema не встановлено
        required = EXTRACTION_SCHEMA.get("required", [])
        missing = [f for f in required if f not in data]
        if missing:
            result["schema_error"] = f"Missing required fields: {missing}"
        else:
            result["schema_ok"] = True
        return result

    try:
        jsonschema.validate(instance=data, schema=EXTRACTION_SCHEMA)
        result["schema_ok"] = True
    except jsonschema.ValidationError as e:
        result["schema_error"] = e.message
    except jsonschema.SchemaError as e:
        result["schema_error"] = f"Schema error: {e.message}"

    return result


def is_valid(raw_output: str) -> bool:
    r = validate(raw_output)
    return r["parse_ok"] and r["schema_ok"]

def batch_validate(outputs: list) -> list:
    return [validate(o) for o in outputs]


def validation_summary(results: list) -> dict:
    n = len(results)
    parse_ok  = sum(1 for r in results if r["parse_ok"])
    schema_ok = sum(1 for r in results if r["schema_ok"])
    both_fail = sum(1 for r in results if not r["parse_ok"])
    schema_fail_only = sum(1 for r in results if r["parse_ok"] and not r["schema_ok"])

    return {
        "total":              n,
        "parse_ok":           parse_ok,
        "parse_fail":         n - parse_ok,
        "schema_ok":          schema_ok,
        "schema_fail_only":   schema_fail_only,
        "raw_valid_rate":     round(schema_ok / n, 3) if n else 0,
        "parse_success_rate": round(parse_ok  / n, 3) if n else 0,
    }


def print_validation_summary(summary: dict, label: str = ""):
    tag = f" [{label}]" if label else ""
    print(f"=== Validation Summary{tag} ===")
    print(f"  Total examples:      {summary['total']}")
    print(f"  Parse OK:            {summary['parse_ok']} ({summary['parse_success_rate']:.1%})")
    print(f"  Parse FAIL:          {summary['parse_fail']}")
    print(f"  Schema OK:           {summary['schema_ok']} ({summary['raw_valid_rate']:.1%})")
    print(f"  Schema FAIL (parse OK): {summary['schema_fail_only']}")