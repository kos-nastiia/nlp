import json
from typing import Optional
from tool_logger import ToolCallLogger, safe_tool_call
from tools import (
    classify_review,
    extract_entities,
    validate_required_fields,
    lookup_known_service,
    score_review_completeness,
)

def baseline_llm_response(text: str) -> str:
    """
    Симулює відповідь LLM БЕЗ tools — тільки на основі тексту.
    Демонструє типові проблеми: галюцинації, неточний sentiment, відсутність структури.
    """
    text_lower = text.lower()

    neg_words = ["жахлив", "погано", "розчарован", "завищен", "нікол", "неможливо"]
    pos_words = ["чудово", "відмінн", "найкращ", "рекоменду", "задоволен"]

    neg = sum(1 for w in neg_words if w in text_lower)
    pos = sum(1 for w in pos_words if w in text_lower)

    if neg > pos:
        sentiment_guess = "negative"
        summary = f"Відгук містить скаргу. Рекомендую передати у відділ якості."
    elif pos > neg:
        sentiment_guess = "positive"
        summary = f"Позитивний відгук. Можна використати для маркетингу."
    else:
        sentiment_guess = "neutral"
        summary = f"Відгук нейтральний або незрозумілий."

    return (
        f"Sentiment: {sentiment_guess}\n"
        f"Summary: {summary}\n"
        f"(no structured extraction, no validation)"
    )

class SupportAssistantAgent:
    def __init__(self, logger: ToolCallLogger):
        self.logger = logger

    def run(self, task_id: str, text: str, verbose: bool = False) -> dict:
        if verbose:
            print(f"\n[{task_id}] {text[:80]}...")

        structured = {}
        tool_calls_count = 0

        lookup_result = safe_tool_call(
            self.logger, task_id,
            lookup_known_service, "lookup_known_service",
            {"text": text},
            reason="identify known service brands in text"
        )
        tool_calls_count += 1

        if lookup_result.get("found"):
            best_match = lookup_result["matches"][0]
            structured["service_name"] = best_match["name"]
            structured["service_category"] = best_match.get("category")
            if verbose:
                print(f"  → Known service: {best_match['name']}")

        classify_result = safe_tool_call(
            self.logger, task_id,
            classify_review, "classify_review",
            {"text": text},
            reason="determine sentiment, issue type, service type"
        )
        tool_calls_count += 1

        if "error" not in classify_result:
            structured.update(classify_result)
            if verbose:
                print(f"  → Sentiment: {classify_result.get('sentiment')} | "
                      f"Issue: {classify_result.get('issue_type')} | "
                      f"Type: {classify_result.get('service_type')}")

        has_price_signal = any(kw in text.lower() for kw in
                               ["грн", "гривен", "$", "євро", "%", "ціна", "ціни", "вартість"])
        needs_entity_extraction = has_price_signal or not structured.get("service_name")

        if needs_entity_extraction:
            extract_result = safe_tool_call(
                self.logger, task_id,
                extract_entities, "extract_entities",
                {"text": text},
                reason="extract service name and price" if needs_entity_extraction else "verify entity extraction"
            )
            tool_calls_count += 1

            if "error" not in extract_result:
                if not structured.get("service_name") and extract_result.get("service_name"):
                    structured["service_name"] = extract_result["service_name"]
                if extract_result.get("mentioned_price") is not None:
                    structured["mentioned_price"] = extract_result["mentioned_price"]
                    structured["currency"]        = extract_result.get("currency")
                if verbose and extract_result.get("mentioned_price"):
                    print(f"  → Price: {extract_result['mentioned_price']} {extract_result.get('currency')}")
        else:
            if verbose:
                print("  → Skipped extract_entities (no price signal, service known)")

        validation = safe_tool_call(
            self.logger, task_id,
            validate_required_fields, "validate_required_fields",
            {"data": structured},
            reason="check extraction completeness"
        )
        tool_calls_count += 1

        if verbose and not validation.get("valid"):
            print(f"  → Validation warnings: {validation.get('warnings')}")

        completeness = safe_tool_call(
            self.logger, task_id,
            score_review_completeness, "score_review_completeness",
            {"data": structured},
            reason="final completeness assessment"
        )
        tool_calls_count += 1

        final_answer = self._compose_answer(structured, validation, completeness, text)

        if verbose:
            print(f"  → Final: {final_answer}")

        return {
            "task_id":         task_id,
            "text":            text,
            "tool_calls_count": tool_calls_count,
            "structured_data": structured,
            "validation":      validation,
            "completeness":    completeness,
            "final_answer":    final_answer,
        }

    def _compose_answer(self, structured: dict, validation: dict,
                        completeness: dict, text: str) -> str:
        sentiment  = structured.get("sentiment", "unknown")
        issue      = structured.get("issue_type")
        svc_name   = structured.get("service_name", "невідомий сервіс")
        svc_type   = structured.get("service_type", "невизначено")
        price      = structured.get("mentioned_price")
        currency   = structured.get("currency")
        level      = completeness.get("level", "?") if isinstance(completeness, dict) else "?"
        warnings   = validation.get("warnings", []) if isinstance(validation, dict) else []

        parts = [f"Сервіс: {svc_name} ({svc_type})"]
        parts.append(f"Sentiment: {sentiment}")
        if issue:
            parts.append(f"Issue: {issue}")
        if price is not None:
            parts.append(f"Ціна: {price} {currency or ''}")
        parts.append(f"Completeness: {level}")
        if warnings:
            parts.append(f"Warnings: {'; '.join(warnings)}")

        # Routing decision
        if sentiment == "negative" and issue:
            parts.append(f"→ Routing: escalate to {issue} team")
        elif sentiment == "positive":
            parts.append("→ Routing: flag for positive feedback archive")
        else:
            parts.append("→ Routing: manual review needed")

        return " | ".join(parts)


def run_agent_batch(test_cases: list, logger: ToolCallLogger,
                    verbose: bool = False) -> list:
    agent = SupportAssistantAgent(logger)
    results = []
    for case in test_cases:
        res = agent.run(case["task_id"], case["text"], verbose=verbose)
        res["expected"] = case.get("expected", {})
        res["notes"]    = case.get("notes", "")
        results.append(res)
    return results