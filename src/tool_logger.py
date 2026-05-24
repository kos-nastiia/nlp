import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class ToolCallLogger:

    def __init__(self, log_path: Optional[str] = None):
        self.log_path = Path(log_path) if log_path else None
        self._buffer: list[dict] = []
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        task_id: str,
        tool_name: str,
        input_data: Any,
        output_data: Any,
        success: bool,
        error: Optional[str] = None,
        reason: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ) -> dict:
        entry = {
            "timestamp":   datetime.now(timezone.utc).isoformat(),
            "task_id":     task_id,
            "tool_name":   tool_name,
            "input":       input_data,
            "output":      output_data,
            "success":     success,
            "error":       error,
            "reason":      reason,
            "duration_ms": duration_ms,
        }
        self._buffer.append(entry)

        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry

    def get_logs(self, task_id: Optional[str] = None) -> list[dict]:
        if task_id:
            return [e for e in self._buffer if e["task_id"] == task_id]
        return list(self._buffer)

    def clear(self):
        self._buffer.clear()

    def summary(self) -> dict:
        if not self._buffer:
            return {"total": 0}

        total = len(self._buffer)
        success = sum(1 for e in self._buffer if e["success"])
        tools_used = {}
        for e in self._buffer:
            tools_used[e["tool_name"]] = tools_used.get(e["tool_name"], 0) + 1

        tasks = set(e["task_id"] for e in self._buffer)
        calls_per_task = {}
        for e in self._buffer:
            calls_per_task[e["task_id"]] = calls_per_task.get(e["task_id"], 0) + 1

        avg_calls = round(sum(calls_per_task.values()) / len(tasks), 2) if tasks else 0

        return {
            "total_calls":         total,
            "success":             success,
            "failed":              total - success,
            "success_rate":        round(success / total, 3),
            "tools_used":          tools_used,
            "unique_tasks":        len(tasks),
            "avg_calls_per_task":  avg_calls,
        }

    def print_summary(self):
        s = self.summary()
        print("=== Tool Call Logger Summary ===")
        print(f"  Total calls:        {s['total_calls']}")
        print(f"  Success:            {s['success']} ({s['success_rate']:.1%})")
        print(f"  Failed:             {s['failed']}")
        print(f"  Unique tasks:       {s['unique_tasks']}")
        print(f"  Avg calls/task:     {s['avg_calls_per_task']}")
        print(f"  Tools used:")
        for tool, cnt in s.get("tools_used", {}).items():
            print(f"    {tool}: {cnt}")

    def to_dataframe(self):
        """Конвертує лог у pandas DataFrame."""
        import pandas as pd
        rows = []
        for e in self._buffer:
            rows.append({
                "timestamp": e["timestamp"],
                "task_id":   e["task_id"],
                "tool_name": e["tool_name"],
                "success":   e["success"],
                "error":     e["error"],
                "reason":    e.get("reason"),
            })
        return pd.DataFrame(rows)


def logged_call(logger: ToolCallLogger, task_id: str, tool_name: str,
                input_data: Any, reason: str = None):
    pass 


def safe_tool_call(logger: ToolCallLogger, task_id: str,
                   tool_fn, tool_name: str, input_data: dict,
                   reason: str = None) -> dict:
    t0 = time.time()
    try:
        result = tool_fn(**input_data)
        duration = round((time.time() - t0) * 1000, 2)
        logger.log(task_id, tool_name, input_data, result, True,
                   reason=reason, duration_ms=duration)
        return result
    except Exception as e:
        duration = round((time.time() - t0) * 1000, 2)
        err_msg = str(e)
        logger.log(task_id, tool_name, input_data, None, False,
                   error=err_msg, reason=reason, duration_ms=duration)
        return {"error": err_msg}