from dataclasses import dataclass, field
from typing import Any, Optional
import uuid


@dataclass
class FlowState:

    case_id:        str             = field(default_factory=lambda: f"case_{uuid.uuid4().hex[:6]}")
    raw_text:       str             = ""
    clean_text:     str             = ""
    word_count:     int             = 0
    ingest_ok:      bool            = False

    route:          Optional[str]   = None
    task_type:      Optional[str]   = None
    schema_name:    Optional[str]   = None
    required_fields: list           = field(default_factory=list)
    optional_fields: list           = field(default_factory=list)
    routing_reason: Optional[str]   = None
    route_ok:       bool            = False

    execute_output: dict            = field(default_factory=dict)
    execution_method: Optional[str] = None
    execute_confidence: Optional[str] = None
    execute_ok:     bool            = False

    validation_ok:  bool            = False
    schema_ok:      bool            = False
    required_ok:    bool            = False
    consistency_ok: bool            = False
    validation_issues: list         = field(default_factory=list)
    recommended_action: Optional[str] = None

    fallback_triggered: bool        = False
    fallback_strategy:  Optional[str] = None
    fallback_attempt:   int         = 0
    fallback_ok:        bool        = False

    final_output:   Optional[dict]  = None
    export_format:  str             = "json"
    export_ok:      bool            = False

    status:         str             = "initialized"
    errors:         list            = field(default_factory=list)
    warnings:       list            = field(default_factory=list)
    steps_completed: list           = field(default_factory=list)
    needs_manual_review: bool       = False


    def add_error(self, step: str, msg: str):
        self.errors.append({"step": step, "error": msg})

    def add_warning(self, step: str, msg: str):
        self.warnings.append({"step": step, "warning": msg})

    def mark_step(self, step: str, ok: bool = True):
        self.steps_completed.append({"step": step, "ok": ok})

    def to_log_dict(self) -> dict:
        return {
            "case_id":           self.case_id,
            "route":             self.route,
            "task_type":         self.task_type,
            "status":            self.status,
            "steps_completed":   [s["step"] for s in self.steps_completed],
            "execute_output":    self.execute_output,
            "validation_ok":     self.validation_ok,
            "validation_issues": self.validation_issues,
            "fallback_triggered":self.fallback_triggered,
            "fallback_strategy": self.fallback_strategy,
            "final_output":      self.final_output,
            "errors":            self.errors,
            "warnings":          self.warnings,
            "needs_manual_review": self.needs_manual_review,
        }