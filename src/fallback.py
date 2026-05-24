import re
from agents import KNOWN_SERVICES, SERVICE_TYPE_KW, ISSUE_KW


class FallbackAgent:

    NAME = "FallbackAgent"

    STRATEGIES = ["rule_repair", "partial_output", "manual_review"]

    def run(self, text: str, extraction: dict, review: dict,
            triage: dict, attempt: int = 1) -> dict:
        issues  = review.get("issues", [])
        verdict = review.get("verdict", "")
        t = text.lower()

        repaired_fields = []
        output = dict(extraction)
        output.pop("agent", None)
        warnings = []
        repair_notes = []

        for issue in issues:
            field   = issue.get("field", "")
            problem = issue.get("problem", "")

            if field == "sentiment" and "signal" in problem:
                neg_sig = any(kw in t for kw in
                    ["жахлив","погано","розчарован","завищен","нікол","занадто","шокують"])
                pos_sig = any(kw in t for kw in
                    ["чудово","відмінн","найкращ","задоволен","тішить"])
                if neg_sig and not pos_sig:
                    output["sentiment"] = "negative"
                    repaired_fields.append("sentiment → negative (rule)")
                elif pos_sig and not neg_sig:
                    output["sentiment"] = "positive"
                    repaired_fields.append("sentiment → positive (rule)")
                elif neg_sig and pos_sig:
                    output["sentiment"] = "mixed"
                    repaired_fields.append("sentiment → mixed (rule)")

            if field == "mentioned_price" and "hallucination" in problem:
                pm = re.search(r'(\d+)\s*(грн|гривень|\$|євро)', text, re.I)
                if pm:
                    try:
                        output["mentioned_price"] = float(pm.group(1))
                        c = pm.group(2).lower()
                        output["currency"] = "UAH" if c in ("грн","гривень") else "USD" if c=="$" else "EUR"
                        repaired_fields.append(f"mentioned_price verified via regex: {output['mentioned_price']}")
                    except Exception:
                        output["mentioned_price"] = None
                        output["currency"] = None
                        repaired_fields.append("mentioned_price nullified (no valid number)")
                else:
                    output["mentioned_price"] = None
                    output["currency"] = None
                    repaired_fields.append("mentioned_price nullified (hallucination confirmed)")

            if field == "service_name" and "not in text" in problem:
                real_name = next(
                    (n for n in sorted(KNOWN_SERVICES, key=len, reverse=True) if n in t),
                    None
                )
                output["service_name"] = real_name
                repaired_fields.append(f"service_name → {real_name} (re-extracted from text)")

            if field == "issue_type" and "positive" in problem:
                output["issue_type"] = None
                repaired_fields.append("issue_type nullified (sentiment=positive)")

            if "required" in problem and "missing" in problem:
                if field == "service_type":
                    svc_sc = {s: sum(1 for kw in kws if kw in t)
                               for s, kws in SERVICE_TYPE_KW.items()}
                    svc_sc = {k:v for k,v in svc_sc.items() if v > 0}
                    if svc_sc:
                        output["service_type"] = max(svc_sc, key=svc_sc.get)
                        repaired_fields.append(f"service_type re-extracted: {output['service_type']}")
                    else:
                        warnings.append(f"service_type still missing after repair")

                elif field == "issue_type":
                    issue_sc = {i: sum(1 for kw in kws if kw in t)
                                 for i, kws in ISSUE_KW.items()}
                    issue_sc = {k:v for k,v in issue_sc.items() if v > 0}
                    if issue_sc:
                        output["issue_type"] = max(issue_sc, key=issue_sc.get)
                        repaired_fields.append(f"issue_type re-extracted: {output['issue_type']}")
                    else:
                        warnings.append(f"issue_type still missing after repair")

        required = triage.get("required_fields", [])
        still_missing = [f for f in required if output.get(f) is None]

        if still_missing and attempt >= 2:
            for f in still_missing:
                warnings.append(f"field '{f}' still missing after {attempt} repair attempts")
            output["needs_manual_review"] = True
            strategy = "manual_review"
            repair_notes.append(f"Repair failed after {attempt} attempts; flagged for manual review")
        elif repaired_fields:
            strategy = "rule_repair"
            output["needs_manual_review"] = False
        elif still_missing:
            strategy = "partial_output"
            output["needs_manual_review"] = True
            warnings.append("partial output — some required fields could not be recovered")
        else:
            strategy = "rule_repair"
            output["needs_manual_review"] = False

        if repaired_fields:
            repair_notes.extend(repaired_fields)

        return {
            "agent":               self.NAME,
            "strategy":            strategy,
            "repaired":            len(repaired_fields) > 0,
            "repaired_fields":     repaired_fields,
            "output":              output,
            "needs_manual_review": output.get("needs_manual_review", False),
            "warnings":            warnings,
            "repair_notes":        "; ".join(repair_notes) if repair_notes else "no repair needed",
            "attempt":             attempt,
        }