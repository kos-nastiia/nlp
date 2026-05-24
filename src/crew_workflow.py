import json
import time
from datetime import datetime, timezone
from pathlib import Path
from agents   import TriagerAgent, ExtractorAgent, ReviewerAgent
from fallback import FallbackAgent


class CrewWorkflow:
    MAX_REPAIRS = 2

    def __init__(self, log_path: str = None):
        self.triager   = TriagerAgent()
        self.extractor = ExtractorAgent()
        self.reviewer  = ReviewerAgent()
        self.fallback  = FallbackAgent()
        self.log_path  = Path(log_path) if log_path else None
        self._logs: list = []
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def run_case(self, case_id: str, text: str, verbose: bool = False) -> dict:
        if verbose:
            print(f"\n[{case_id}] {text[:70]}...")

        triage = self.triager.run(text)
        if verbose:
            print(f"  Triager  → route={triage['route']}, diff={triage['difficulty']}")

        extraction = self.extractor.run(text, triage)
        if verbose:
            print(f"  Extractor→ sentiment={extraction['sentiment']}, "
                  f"service={extraction.get('service_name') or extraction.get('service_type')}, "
                  f"conf={extraction['confidence']}")

        review = self.reviewer.run(text, extraction, triage)
        if verbose:
            print(f"  Reviewer → verdict={review['verdict']}, issues={review['issues_count']}")

        fallback_triggered = False
        fallback_output    = None
        final_extraction   = extraction
        repair_attempts    = 0
        status             = "accepted"

        if review["verdict"] in ("repair_needed", "fallback_needed"):
            fallback_triggered = True

            for attempt in range(1, self.MAX_REPAIRS + 1):
                repair_attempts = attempt
                fb = self.fallback.run(text, final_extraction, review, triage, attempt)
                fallback_output = fb

                if verbose:
                    print(f"  Fallback → attempt={attempt}, strategy={fb['strategy']}, "
                          f"repaired={fb['repaired']}")

                # Re-review after repair
                re_review = self.reviewer.run(text, fb["output"], triage)
                if verbose:
                    print(f"  Re-review→ verdict={re_review['verdict']}")

                if re_review["verdict"] in ("accept", "accept_with_warnings"):
                    final_extraction = fb["output"]
                    review = re_review
                    status = "accepted_after_repair"
                    break
                else:
                    final_extraction = fb["output"]
                    review = re_review

            if status != "accepted_after_repair":
                if fb["needs_manual_review"]:
                    status = "manual_review_required"
                else:
                    status = "accepted_partial"
        else:
            status = "accepted" if review["verdict"] == "accept" else "accepted_with_warnings"

        # Build final output (clean)
        final_output = {k: v for k, v in final_extraction.items()
                        if k not in ("agent", "confidence")}
        final_output["confidence"]          = final_extraction.get("confidence")
        final_output["needs_manual_review"] = final_extraction.get("needs_manual_review", False)

        case_log = {
            "case_id":            case_id,
            "timestamp":          datetime.now(timezone.utc).isoformat(),
            "input":              text,
            "triager_output":     {k: v for k, v in triage.items() if k != "agent"},
            "extractor_output":   {k: v for k, v in extraction.items() if k != "agent"},
            "reviewer_output":    {k: v for k, v in review.items() if k != "agent"},
            "fallback_triggered": fallback_triggered,
            "fallback_output":    {k: v for k, v in fallback_output.items() if k != "agent"} if fallback_output else None,
            "repair_attempts":    repair_attempts,
            "final_output":       final_output,
            "status":             status,
        }

        self._logs.append(case_log)
        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(case_log, ensure_ascii=False) + "\n")

        return case_log

    def run_batch(self, test_cases: list, verbose: bool = False) -> list:
        results = []
        for tc in test_cases:
            r = self.run_case(tc["case_id"], tc["text"], verbose=verbose)
            r["expected"]  = tc.get("expected", {})
            r["scenario"]  = tc.get("scenario", "")
            r["notes"]     = tc.get("notes", "")
            results.append(r)
        return results

    def metrics(self, results: list) -> dict:
        n = len(results)
        if not n:
            return {}

        statuses = [r["status"] for r in results]

        valid_final = sum(1 for s in statuses if s in
                          ("accepted", "accepted_with_warnings", "accepted_after_repair"))
        fallback_activated = sum(1 for r in results if r["fallback_triggered"])
        fallback_success   = sum(1 for r in results
                                 if r["fallback_triggered"] and r["status"] == "accepted_after_repair")
        manual_review      = sum(1 for s in statuses if s == "manual_review_required")

        real_catches = sum(
            1 for r in results
            if r["reviewer_output"].get("issues_count", 0) > 0
            and r["expected"].get("has_issues", True)
        )

        avg_agents = []
        for r in results:
            n_agents = 2 if not r["fallback_triggered"] else 2 + r.get("repair_attempts", 1)
            avg_agents.append(n_agents)

        return {
            "n_cases":               n,
            "valid_final_rate":      round(valid_final / n, 3),
            "fallback_activation":   fallback_activated,
            "fallback_rate":         round(fallback_activated / n, 3),
            "fallback_success":      fallback_success,
            "fallback_success_rate": round(fallback_success / fallback_activated, 3) if fallback_activated else 0,
            "manual_review":         manual_review,
            "manual_review_rate":    round(manual_review / n, 3),
            "avg_agents_per_case":   round(sum(avg_agents) / n, 2),
        }

    def get_logs(self) -> list:
        return list(self._logs)