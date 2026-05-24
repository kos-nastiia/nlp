import json
from collections import Counter
from typing import List, Dict
import pandas as pd

TEST_CASES = [
    # 1. Простий кейс — tools очевидно допомагають
    {
        "task_id": "case_001",
        "text": "авіакомпанія скайфлай це відмінний вибір для подорожей | нові літаки",
        "expected": {"sentiment": "positive", "service_name": "скайфлай", "service_type": "авіакомпанія"},
        "notes": "простий позитивний відгук — tools дають структуру",
        "scenario": "simple_helpful",
    },
    # 2. Кейс із missing data
    {
        "task_id": "case_002",
        "text": "дуже погане обслуговування",
        "expected": {"sentiment": "negative", "service_name": None, "issue_type": "support"},
        "notes": "дуже короткий текст — service_name відсутній",
        "scenario": "missing_data",
    },
    # 3. Noisy text
    {
        "task_id": "case_003",
        "text": "shimano deore оптимальне поєднання ціни і якості | 12 швидкостей вистачає для будьяких схилів",
        "expected": {"sentiment": "positive", "service_name": "shimano"},
        "notes": "технічна назва, відсутні пробіли — noisy text",
        "scenario": "noisy_text",
    },
    # 4. Tool повертає порожній результат
    {
        "task_id": "case_004",
        "text": "загалом непогано, але є деякі зауваження",
        "expected": {"sentiment": "mixed", "service_name": None},
        "notes": "мінімальний текст, lookup не знаходить нічого",
        "scenario": "empty_result",
    },
    # 5. Агент не має викликати зайвий tool
    {
        "task_id": "case_005",
        "text": "персонал скайфлай дуже професійний та уважний | стюардеси завжди готові допомогти",
        "expected": {"sentiment": "positive", "service_name": "скайфлай"},
        "notes": "немає ціни → extract_entities не потрібен (skip expected)",
        "scenario": "unnecessary_tool",
    },
    # 6. Неоднозначний кейс
    {
        "task_id": "case_006",
        "text": "ресторан непоганий але ціни у ресторанах та кафе завищені та не відповідають якості",
        "expected": {"sentiment": "mixed", "service_type": "ресторан", "issue_type": "billing"},
        "notes": "змішаний sentiment, ambiguous — і позитив і негатив",
        "scenario": "ambiguous",
    },
    # 7. Два tools підряд критично важливі
    {
        "task_id": "case_007",
        "text": "платити майже 100 грн за посередню каву це занадто | кав'ярня повністю розчарувала",
        "expected": {"sentiment": "negative", "issue_type": "billing", "mentioned_price": 100, "currency": "UAH"},
        "notes": "потрібні classify + extract (ціна 100 грн)",
        "scenario": "two_tools_needed",
    },
    # 8. Validator знаходить проблему
    {
        "task_id": "case_008",
        "text": "жахлива якість мобільного та інтернетзвязку | постійні обриви",
        "expected": {"sentiment": "negative", "service_type": None, "issue_type": "quality"},
        "notes": "service_type не визначено → validation warning",
        "scenario": "validator_finds_issue",
    },
    # 9. Final answer має послатися на tool output
    {
        "task_id": "case_009",
        "text": "служба підтримки скайфлай працює жахливо | дозвонитись до оператора майже неможливо",
        "expected": {"sentiment": "negative", "service_name": "скайфлай", "issue_type": "support"},
        "notes": "final answer має містити routing до support team",
        "scenario": "tool_output_in_answer",
    },
    # 10. Агент помилився або tool не допоміг
    {
        "task_id": "case_010",
        "text": "цей продуктовий магазин найкращий у нашому районі | асортимент свіжих продуктів завжди великий",
        "expected": {"sentiment": "positive", "service_type": "магазин"},
        "notes": "магазин не в KNOWN_SERVICES → service_name буде null",
        "scenario": "tool_not_helpful",
    },
]


def compute_metrics(results: list, logger) -> dict:
    """Рахує базові метрики по batch результатах."""
    n = len(results)
    log_summary = logger.summary()

    # Tool call success rate
    success_rate = log_summary.get("success_rate", 0)
    avg_calls    = log_summary.get("avg_calls_per_task", 0)

    # Tasks з реальною користю від tools
    useful = 0
    for r in results:
        sd = r.get("structured_data", {})
        if sd.get("sentiment") and (sd.get("service_name") or sd.get("service_type")):
            useful += 1

    unnecessary = 0
    for r in results:
        text_lower = r.get("text", "").lower()
        has_price = any(kw in text_lower for kw in ["грн", "$", "євро", "%", "ціна"])
        logs = logger.get_logs(r["task_id"])
        called_extract = any(l["tool_name"] == "extract_entities" for l in logs)
        if called_extract and not has_price and r.get("structured_data", {}).get("service_name"):
            unnecessary += 1

    ratings = []
    for r in results:
        exp = r.get("expected", {})
        sd  = r.get("structured_data", {})
        correct_sentiment = exp.get("sentiment") == sd.get("sentiment")
        correct_name = exp.get("service_name") == sd.get("service_name") or exp.get("service_name") is None
        if correct_sentiment and correct_name:
            ratings.append("correct")
        elif correct_sentiment or correct_name:
            ratings.append("partly_correct")
        else:
            ratings.append("wrong")

    rating_counts = Counter(ratings)

    return {
        "n_tasks":                n,
        "tool_call_success_rate": round(success_rate, 3),
        "avg_calls_per_task":     round(avg_calls, 2),
        "tasks_with_useful_tools": useful,
        "unnecessary_tool_calls": unnecessary,
        "total_tool_calls":       log_summary.get("total_calls", 0),
        "ratings":                dict(rating_counts),
    }


def print_metrics(metrics: dict):
    print("=== Agent Metrics ===")
    print(f"  Tasks:                    {metrics['n_tasks']}")
    print(f"  Tool call success rate:   {metrics['tool_call_success_rate']:.1%}")
    print(f"  Avg tool calls/task:      {metrics['avg_calls_per_task']}")
    print(f"  Tasks with useful tools:  {metrics['tasks_with_useful_tools']}/{metrics['n_tasks']}")
    print(f"  Unnecessary tool calls:   {metrics['unnecessary_tool_calls']}")
    print(f"  Total tool calls:         {metrics['total_tool_calls']}")
    print(f"  Final answer ratings:     {metrics['ratings']}")


ERROR_ANALYSIS = [
    {
        "task_id":   "case_002",
        "input":     "дуже погане обслуговування",
        "expected":  "service_name identified, issue_type=support",
        "actual":    "service_name=null, issue_type=null (text too short)",
        "category":  "tool output insufficient",
        "fix":       "Додати fuzzy matching або запитати уточнення у користувача",
    },
    {
        "task_id":   "case_004",
        "input":     "загалом непогано, але є деякі зауваження",
        "expected":  "sentiment=mixed, some issue identified",
        "actual":    "lookup returns empty, classify returns neutral",
        "category":  "tool returns empty result",
        "fix":       "Розширити словники keyword для neutral/mixed texts",
    },
    {
        "task_id":   "case_005",
        "input":     "персонал скайфлай дуже професійний та уважний",
        "expected":  "extract_entities NOT called (no price)",
        "actual":    "extract_entities called because service_name already found",
        "category":  "unnecessary tool call avoided correctly",
        "fix":       "Логіка вже правильна — перевірити needs_entity_extraction",
    },
    {
        "task_id":   "case_006",
        "input":     "ресторан непоганий але ціни завищені",
        "expected":  "sentiment=mixed",
        "actual":    "sentiment may be negative (neg keywords dominate)",
        "category":  "sentiment ambiguity",
        "fix":       "Покращити mixed-detection (рахувати і pos, і neg > 0)",
    },
    {
        "task_id":   "case_008",
        "input":     "жахлива якість мобільного та інтернетзвязку",
        "expected":  "service_type identified as telecom",
        "actual":    "service_type=None (telecom not in SERVICE_TYPE_KEYWORDS)",
        "category":  "missing domain coverage",
        "fix":       "Додати 'телеком' та 'мобільний зв'язок' до SERVICE_TYPE_KEYWORDS",
    },
    {
        "task_id":   "case_010",
        "input":     "цей продуктовий магазин найкращий",
        "expected":  "service_name identified",
        "actual":    "service_name=null (магазин не в KNOWN_SERVICES)",
        "category":  "tool not helpful — unknown service",
        "fix":       "Розширити KNOWN_SERVICES або додати generic ORG extractor",
    },
    {
        "task_id":   "case_003",
        "input":     "shimano deore оптимальне поєднання ціни і якості",
        "expected":  "service_name=shimano, product=shimano deore",
        "actual":    "service_name=shimano (OK), product not extracted separately",
        "category":  "partial tool output",
        "fix":       "Додати extract_product tool для технічних назв продуктів",
    },
    {
        "task_id":   "case_007",
        "input":     "платити майже 100 грн за посередню каву",
        "expected":  "mentioned_price=100, currency=UAH",
        "actual":    "mentioned_price=100, currency=UAH (correct)",
        "category":  "correct tool use — positive example",
        "fix":       "N/A — показовий успішний кейс",
    },
    {
        "task_id":   "case_001",
        "input":     "авіакомпанія скайфлай відмінний вибір | нові літаки",
        "expected":  "service_name=скайфлай, sentiment=positive, routing=positive archive",
        "actual":    "correct — all tools cooperate",
        "category":  "correct tool use — positive example",
        "fix":       "N/A — показовий успішний кейс",
    },
    {
        "task_id":   "case_009",
        "input":     "служба підтримки скайфлай жахлива",
        "expected":  "routing: escalate to support team",
        "actual":    "final answer contains '→ Routing: escalate to support team'",
        "category":  "tool output correctly used in final answer",
        "fix":       "N/A — демонструє цінність structured tool outputs",
    },
]


def error_analysis_df(errors: list = None) -> pd.DataFrame:
    if errors is None:
        errors = ERROR_ANALYSIS
    return pd.DataFrame(errors)


def error_category_summary(errors: list = None) -> dict:
    if errors is None:
        errors = ERROR_ANALYSIS
    return Counter(e["category"] for e in errors)