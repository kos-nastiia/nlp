import json
import time
from typing import Optional

from validator import validate
from llm_extract import extract_one, repair_one


# ── Основний pipeline ─────────────────────────────────────────────────────

def run_pipeline(text: str,
                 max_repairs: int = 2,
                 model: str = "claude-sonnet-4-20250514",
                 verbose: bool = False) -> dict:
    history = []
    repairs_needed = 0

    raw = extract_one(text, model=model)
    val = validate(raw)
    history.append({"attempt": 0, "type": "extraction", "output": raw, "validation": val})

    if verbose:
        _log(0, val)

    # Repair loop
    attempt = 0
    while not (val["parse_ok"] and val["schema_ok"]) and attempt < max_repairs:
        attempt += 1
        repairs_needed += 1

        error_msg = val["schema_error"] or val["parse_error"] or "unknown error"
        if verbose:
            print(f"  → Repair attempt {attempt}: {error_msg}")

        time.sleep(0.5)  # rate limit courtesy
        raw = repair_one(text, raw, error_msg, model=model)
        val = validate(raw)
        history.append({"attempt": attempt, "type": "repair", "output": raw, "validation": val})

        if verbose:
            _log(attempt, val)

    return {
        "text":           text,
        "attempts":       len(history),
        "raw_output":     raw,
        "validation":     val,
        "repairs_needed": repairs_needed,
        "success":        val["parse_ok"] and val["schema_ok"],
        "history":        history,
    }


def run_batch_pipeline(texts: list,
                       max_repairs: int = 2,
                       model: str = "claude-sonnet-4-20250514",
                       verbose: bool = True) -> list:
    results = []
    for i, text in enumerate(texts):
        if verbose:
            print(f"\n[{i+1}/{len(texts)}] {text[:60]}...")
        res = run_pipeline(text, max_repairs=max_repairs, model=model, verbose=verbose)
        results.append(res)
        time.sleep(0.3)
    return results

def pipeline_metrics(results: list) -> dict:
    n = len(results)
    if n == 0:
        return {}

    raw_valid = sum(
        1 for r in results
        if r["history"][0]["validation"]["parse_ok"]
        and r["history"][0]["validation"]["schema_ok"]
    )

    post_valid = sum(1 for r in results if r["success"])

    needed_repair = sum(1 for r in results if r["repairs_needed"] > 0)

    repair_failed = sum(
        1 for r in results
        if r["repairs_needed"] > 0 and not r["success"]
    )

    avg_repairs = sum(r["repairs_needed"] for r in results) / n

    return {
        "total":                n,
        "raw_valid":            raw_valid,
        "raw_valid_rate":       round(raw_valid  / n, 3),
        "post_repair_valid":    post_valid,
        "post_repair_rate":     round(post_valid / n, 3),
        "needed_repair":        needed_repair,
        "repair_needed_rate":   round(needed_repair / n, 3),
        "repair_failed":        repair_failed,
        "repair_failed_rate":   round(repair_failed / n, 3),
        "avg_repairs":          round(avg_repairs, 2),
        "improvement":          post_valid - raw_valid,
    }


def print_pipeline_metrics(metrics: dict):
    print("=== Pipeline Metrics ===")
    print(f"  Total examples:          {metrics['total']}")
    print(f"  Raw valid JSON rate:      {metrics['raw_valid']}/{metrics['total']} "
          f"({metrics['raw_valid_rate']:.1%})")
    print(f"  Post-repair valid rate:   {metrics['post_repair_valid']}/{metrics['total']} "
          f"({metrics['post_repair_rate']:.1%})")
    print(f"  Needed repair:           {metrics['needed_repair']} "
          f"({metrics['repair_needed_rate']:.1%})")
    print(f"  Repair failed:           {metrics['repair_failed']} "
          f"({metrics['repair_failed_rate']:.1%})")
    print(f"  Avg repairs per example: {metrics['avg_repairs']}")
    print(f"  Improvement from repair: +{metrics['improvement']}")


def simulate_results(eval_set: list) -> list:
    import random
    random.seed(42)

    simulated_outputs = [
        # 1 — скайфлай, позитив
        '{"service_name": "скайфлай", "service_type": "авіакомпанія", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "відмінний вибір для подорожей", "confidence": "high"}',
        # 2 — скайфлай, багаж
        '{"service_name": "скайфлай", "service_type": "авіакомпанія", "sentiment": "negative", "issue_type": "logistics", "mentioned_price": null, "currency": null, "key_aspect": "багаж губиться та пошкоджується", "confidence": "high"}',
        # 3 — підтримка скайфлай — parse error (зайвий текст)
        'Ось результат extraction:\n```json\n{"service_name": "скайфлай", "service_type": "авіакомпанія", "sentiment": "negative", "issue_type": "support", "mentioned_price": null, "currency": null, "key_aspect": "служба підтримки недоступна", "confidence": "high"}\n```',
        # 4 — персонал скайфлай
        '{"service_name": "скайфлай", "service_type": "авіакомпанія", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "персонал profesійний та уважний", "confidence": "high"}',
        # 5 — ресторан, schema violation (wrong sentiment value)
        '{"service_name": null, "service_type": "ресторан", "sentiment": "погано", "issue_type": "quality", "mentioned_price": null, "currency": null, "key_aspect": "їжа пересолена", "confidence": "medium"}',
        # 6 — ресторан, ціни — missing required field
        '{"service_name": null, "service_type": "ресторан", "sentiment": "negative", "issue_type": "billing", "mentioned_price": null, "currency": null, "key_aspect": "завищені ціни"}',
        # 7 — інгліш хаб ціни
        '{"service_name": "інгліш хаб", "service_type": "школа", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "доступні ціни на навчання", "confidence": "high"}',
        # 8 — інгліш хаб онлайн
        '{"service_name": "інгліш хаб", "service_type": "освіта", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "зручне дистанційне навчання", "confidence": "high"}',
        # 9 — shimano гальма
        '{"service_name": "shimano", "service_type": "спорт", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "гальма працюють чітко та плавно", "confidence": "high"}',
        # 10 — shimano deore — not JSON at all
        'Виходячи з тексту, відгук стосується shimano deore — це позитивний відгук про трансмісію велосипеда. Ціна та якість збалансовані.',
        # 11 — доставка позитив
        '{"service_name": null, "service_type": "доставка", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "швидка доставка у відмінному стані", "confidence": "high"}',
        # 12 — доставка негатив
        '{"service_name": null, "service_type": "доставка", "sentiment": "negative", "issue_type": "delivery", "mentioned_price": null, "currency": null, "key_aspect": "великі затримки доставки", "confidence": "high"}',
        # 13 — кав'ярня 100 грн — wrong type (price as string)
        '{"service_name": null, "service_type": "кафе", "sentiment": "negative", "issue_type": "billing", "mentioned_price": "100", "currency": "UAH", "key_aspect": "100 грн за каву занадто дорого", "confidence": "high"}',
        # 14 — бар 200-300 грн
        '{"service_name": null, "service_type": "кафе", "sentiment": "negative", "issue_type": "billing", "mentioned_price": 200, "currency": "UAH", "key_aspect": "200-300 грн за смузі — захмарно", "confidence": "high"}',
        # 15 — автосервіс позитив
        '{"service_name": null, "service_type": "автосервіс", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "найкращий автосервіс, майстри-професіонали", "confidence": "high"}',
        # 16 — автосервіс негатив
        '{"service_name": null, "service_type": "автосервіс", "sentiment": "negative", "issue_type": "quality", "mentioned_price": null, "currency": null, "key_aspect": "застаріле обладнання та неякісні запчастини", "confidence": "high"}',
        # 17 — готель сонячний рай — hallucinated field
        '{"service_name": "сонячний рай", "service_type": "готель", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "підтримка під час відпочинку", "confidence": "medium", "extra_field": "туристична агенція"}',
        # 18 — цифровий сервіс
        '{"service_name": null, "service_type": "інше", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "мобільний застосунок та програма заохочень", "confidence": "medium"}',
        # 19 — прокат костюмів
        '{"service_name": null, "service_type": "інше", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "швидко орендувала костюм для вечірки", "confidence": "high"}',
        # 20 — продуктовий магазин
        '{"service_name": null, "service_type": "магазин", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "великий асортимент свіжих продуктів", "confidence": "high"}',
    ]

    from validator import validate

    results = []
    for i, (item, raw) in enumerate(zip(eval_set, simulated_outputs)):
        val = validate(raw)
        repairs_needed = 0
        history = [{"attempt": 0, "type": "extraction", "output": raw, "validation": val}]

        if not (val["parse_ok"] and val["schema_ok"]):
            repairs_needed = 1
            repair_map = {
                2: '{"service_name": "скайфлай", "service_type": "авіакомпанія", "sentiment": "negative", "issue_type": "support", "mentioned_price": null, "currency": null, "key_aspect": "служба підтримки недоступна", "confidence": "high"}',
                4: '{"service_name": null, "service_type": "ресторан", "sentiment": "negative", "issue_type": "quality", "mentioned_price": null, "currency": null, "key_aspect": "їжа пересолена, очікував більшого", "confidence": "high"}',
                5: '{"service_name": null, "service_type": "ресторан", "sentiment": "negative", "issue_type": "billing", "mentioned_price": null, "currency": null, "key_aspect": "завищені ціни у ресторанах", "confidence": "medium"}',
                9: '{"service_name": "shimano", "service_type": "спорт", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "shimano deore — ціна і якість", "confidence": "high"}',
                12: '{"service_name": null, "service_type": "кафе", "sentiment": "negative", "issue_type": "billing", "mentioned_price": 100, "currency": "UAH", "key_aspect": "100 грн за каву занадто дорого", "confidence": "high"}',
                16: '{"service_name": "сонячний рай", "service_type": "готель", "sentiment": "positive", "issue_type": null, "mentioned_price": null, "currency": null, "key_aspect": "підтримка під час відпочинку", "confidence": "medium"}',
            }
            repaired_raw = repair_map.get(i, raw)
            repaired_val = validate(repaired_raw)
            history.append({"attempt": 1, "type": "repair", "output": repaired_raw, "validation": repaired_val})
            raw = repaired_raw
            val = repaired_val

        results.append({
            "text":           item["text"],
            "attempts":       len(history),
            "raw_output":     raw,
            "validation":     val,
            "repairs_needed": repairs_needed,
            "success":        val["parse_ok"] and val["schema_ok"],
            "history":        history,
        })

    return results


def _log(attempt: int, val: dict):
    status = "✓" if (val["parse_ok"] and val["schema_ok"]) else "✗"
    parse  = "parse:OK" if val["parse_ok"]  else f"parse:FAIL({val['parse_error'][:50]})"
    schema = "schema:OK" if val["schema_ok"] else f"schema:FAIL({(val['schema_error'] or '')[:60]})"
    print(f"  [{status}] attempt={attempt} | {parse} | {schema}")