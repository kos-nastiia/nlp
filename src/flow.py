import re
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from flow_state import FlowState
from router    import route_step
from executor  import execute_step
from validator import validate_step
from fallback  import fallback_step
from exporter  import export_step, export_to_jsonl_line



def ingest_step(case_id: str, raw_text: str) -> FlowState:
    """
    Ingest step: приймає raw input, базова очистка, ініціалізує FlowState.
    НЕ виконує extraction чи classification.
    """
    state = FlowState(case_id=case_id)
    state.raw_text = raw_text

    # Basic cleaning: strip, collapse whitespace, remove pipe (sentence sep)
    clean = raw_text.strip()
    clean = re.sub(r'\s+', ' ', clean)
    clean = re.sub(r'\s*\|\s*', ' | ', clean)
    state.clean_text = clean
    state.word_count = len(clean.split())

    # Guard: empty input
    if not clean or state.word_count == 0:
        state.ingest_ok = False
        state.status    = "ingest_failed"
        state.add_error("ingest", "empty input")
        state.mark_step("ingest", ok=False)
        return state

    state.ingest_ok = True
    state.status    = "ingested"
    state.mark_step("ingest")
    return state

def run_flow(case_id: str, text: str,
             log_path: str = None,
             verbose: bool = False,
             max_fallback_attempts: int = 2) -> FlowState:

    t0 = time.time()

    if verbose:
        print(f"\n[{case_id}] {text[:70]}...")

    state = ingest_step(case_id, text)
    if verbose:
        print(f"  ingest  → ok={state.ingest_ok}, words={state.word_count}")

    if state.ingest_ok:
        state = route_step(state)
        if verbose:
            print(f"  route   → {state.route} ({state.routing_reason[:60]})")

    if state.route_ok:
        state = execute_step(state)
        if verbose:
            out = state.execute_output
            print(f"  execute → sentiment={out.get('sentiment')}, "
                  f"service={out.get('service_name') or out.get('service_type')}, "
                  f"conf={out.get('confidence')}")

    if state.execute_ok:
        state = validate_step(state)
        if verbose:
            print(f"  validate→ ok={state.validation_ok}, "
                  f"action={state.recommended_action}, "
                  f"issues={len(state.validation_issues)}")

    if state.recommended_action in ("fallback_needed", "repair_and_export_with_warning"):
        for attempt in range(1, max_fallback_attempts + 1):
            state = fallback_step(state, max_attempts=max_fallback_attempts)
            if verbose:
                print(f"  fallback→ attempt={attempt}, "
                      f"strategy={state.fallback_strategy}, "
                      f"ok={state.fallback_ok}")
            if state.fallback_ok:
                break

    state = export_step(state)
    if verbose:
        fo = state.final_output or {}
        print(f"  export  → status={state.status}, "
              f"routing={fo.get('routing_decision')}, "
              f"manual={state.needs_manual_review}")

    state.duration_ms = round((time.time() - t0) * 1000, 1)

    if log_path:
        _append_log(state, log_path)

    return state



def run_batch(test_cases: list, log_path: str = None,
              verbose: bool = False) -> list:
    """Запускає flow для списку test cases."""
    results = []
    for tc in test_cases:
        state = run_flow(
            tc["case_id"], tc["text"],
            log_path=log_path, verbose=verbose
        )
        state._expected  = tc.get("expected", {})
        state._scenario  = tc.get("scenario", "")
        state._notes     = tc.get("notes", "")
        results.append(state)
    return results

def compute_metrics(results: list) -> dict:
    n = len(results)
    if not n:
        return {}

    completed     = sum(1 for r in results if r.export_ok)
    val_pass      = sum(1 for r in results if r.validation_ok)
    fb_activated  = sum(1 for r in results if r.fallback_triggered)
    fb_success    = sum(1 for r in results if r.fallback_triggered and r.fallback_ok)
    manual        = sum(1 for r in results if r.needs_manual_review)
    export_valid  = sum(1 for r in results if r.final_output is not None)
    warnings_total = sum(len(r.warnings) for r in results)
    errors_total   = sum(len(r.errors)   for r in results)

    avg_steps = sum(len(r.steps_completed) for r in results) / n
    avg_warnings = warnings_total / n

    return {
        "n_cases":              n,
        "flow_completion_rate": round(completed / n, 3),
        "validation_pass_rate": round(val_pass  / n, 3),
        "fallback_activation":  fb_activated,
        "fallback_rate":        round(fb_activated / n, 3),
        "fallback_success":     fb_success,
        "fallback_success_rate":round(fb_success / fb_activated, 3) if fb_activated else 0,
        "manual_review":        manual,
        "manual_review_rate":   round(manual / n, 3),
        "export_valid_rate":    round(export_valid / n, 3),
        "avg_steps_per_case":   round(avg_steps, 1),
        "avg_warnings_per_case":round(avg_warnings, 1),
        "total_errors":         errors_total,
        "total_warnings":       warnings_total,
    }


def print_metrics(m: dict):
    print("=== Flow Metrics ===")
    print(f"  Cases:                  {m['n_cases']}")
    print(f"  Flow completion rate:   {m['flow_completion_rate']:.1%}")
    print(f"  Validation pass rate:   {m['validation_pass_rate']:.1%}")
    print(f"  Fallback activation:    {m['fallback_activation']} ({m['fallback_rate']:.1%})")
    print(f"  Fallback success rate:  {m['fallback_success_rate']:.1%}")
    print(f"  Manual review rate:     {m['manual_review_rate']:.1%}")
    print(f"  Export valid rate:      {m['export_valid_rate']:.1%}")
    print(f"  Avg steps/case:         {m['avg_steps_per_case']}")
    print(f"  Avg warnings/case:      {m['avg_warnings_per_case']}")


def _append_log(state: FlowState, log_path: str):
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(export_to_jsonl_line(state) + "\n")