from enum import Enum
from pydantic import BaseModel


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class RuleId(str,Enum):
  soql_in_loop="soql_in_loop"
  dml_in_loop="dml_in_loop"
  hardcoded_id="hardcoded_id"
  hardcoded_external_id="hardcoded_external_id"
  missing_crud_fls="missing_crud_fls"
  missing_sharing_declaration="missing_sharing_declaration"
  high_complexity="high_complexity"
  duplicate_method="duplicate_method"
  unbatched_db_calls="unbatched_db_calls"
  missing_static_constant="missing_static_constant"
  exception_risk="exception_risk"
  best_practice_violation="best_practice_violation"
  other="other"
  explicit_system_mode = "explicit_system_mode"
  nested_loop_2 = "nested_loop_2"       # 2 levels — MEDIUM, review
  nested_loop_deep = "nested_loop_deep"       # 3+ levels — HIGH, CPU/heap risk
  unsafe_inner_html="unsafe_inner_html"
  manual_dom_manipulation="manual_dom_manipulation"
  imperative_apex_no_error_handling="imperative_apex_no_error_handling"
  missing_wire_error_handler="missing_wire_error_handler"
  apex_call_in_loop="apex_call_in_loop"


class Finding(BaseModel):
    rule: RuleId
    severity: Severity
    line: int
    message: str
    suggestion: str
    doc_url: str | None = None  # Phase 3: populated from KB retrieval


class ReviewResult(BaseModel):
    filename: str
    findings: list[Finding]
    summary: str | None = None  # Phase 2: LLM-generated summary
    llm_explanation: str | None = None  # Phase 2: Claude reasoning output


class LLMReviewOutput(BaseModel):
  findings: list[Finding]
  summary: str

