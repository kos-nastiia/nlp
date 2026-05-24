import json
from flow_state import FlowState


def export_step(state: FlowState, fmt: str = "json") -> FlowState:
    status = state.status

    # ── Build final output ────────────────────────────────────────────────
    if status in ("executed", "validated", "repaired", "partial"):
        base = dict(state.execute_output)
        base.pop("confidence", None)  # не виводимо внутрішнє поле назовні

        final = {
            "case_id":            state.case_id,
            "route":              state.route,
            "task_type":          state.task_type,
            **{k: base.get(k) for k in
               ["sentiment", "service_type", "service_name",
                "issue_type", "mentioned_price", "currency", "key_aspect"]},
            "confidence":         state.execute_output.get("confidence"),
            "needs_manual_review": state.needs_manual_review,
        }

        if status == "validated":
            export_status = "exported"
        elif status == "repaired":
            export_status = "exported_after_repair"
        elif state.validation_issues:
            export_status = "exported_with_warnings"
        else:
            export_status = "exported_partial"

    elif status == "manual_review_required":
        final = {
            "case_id":            state.case_id,
            "route":              state.route,
            "task_type":          state.task_type,
            "sentiment":          state.execute_output.get("sentiment"),
            "service_type":       state.execute_output.get("service_type"),
            "service_name":       state.execute_output.get("service_name"),
            "issue_type":         state.execute_output.get("issue_type"),
            "mentioned_price":    None,
            "currency":           None,
            "key_aspect":         state.execute_output.get("key_aspect"),
            "confidence":         "low",
            "needs_manual_review": True,
        }
        export_status = "exported_partial_manual_review"

    elif status in ("route_failed", "execute_failed", "execute_skipped"):
        # Safe failure — structured error
        final = {
            "case_id":            state.case_id,
            "route":              state.route or "unknown",
            "task_type":          state.task_type or "unknown",
            "sentiment":          None,
            "service_type":       None,
            "service_name":       None,
            "issue_type":         None,
            "mentioned_price":    None,
            "currency":           None,
            "key_aspect":         None,
            "confidence":         "none",
            "needs_manual_review": True,
            "failure_reason":      "; ".join(e["error"] for e in state.errors) or status,
        }
        export_status = "safe_failure"

    else:
        final = {
            "case_id":            state.case_id,
            "route":              state.route,
            "needs_manual_review": True,
            "failure_reason":      f"unexpected status: {status}",
        }
        export_status = "safe_failure"

    sentiment  = final.get("sentiment")
    issue      = final.get("issue_type")
    if sentiment == "negative" and issue:
        routing = f"escalate_to_{issue}_team"
    elif sentiment == "positive":
        routing = "archive_positive_feedback"
    else:
        routing = "manual_review"
    final["routing_decision"] = routing

    state.final_output  = final
    state.export_ok     = True
    state.export_format = fmt
    state.status        = export_status
    state.mark_step("export", ok=True)
    return state


def export_to_jsonl_line(state: FlowState) -> str:
    record = {
        "case_id":            state.case_id,
        "input":              state.raw_text,
        "steps":              [
            {"step": s["step"], "ok": s["ok"]}
            for s in state.steps_completed
        ],
        "route":              state.route,
        "task_type":          state.task_type,
        "routing_reason":     state.routing_reason,
        "execute_output":     state.execute_output,
        "validation_result":  {
            "ok":       state.validation_ok,
            "issues":   state.validation_issues,
            "action":   state.recommended_action,
        },
        "fallback_triggered": state.fallback_triggered,
        "fallback_strategy":  state.fallback_strategy,
        "fallback_ok":        state.fallback_ok,
        "export_output":      state.final_output,
        "final_status":       state.status,
        "errors":             state.errors,
        "warnings":           [w["warning"] for w in state.warnings],
        "needs_manual_review":state.needs_manual_review,
    }
    return json.dumps(record, ensure_ascii=False)