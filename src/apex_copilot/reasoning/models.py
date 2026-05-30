from enum import Enum
from pydantic import BaseModel


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Finding(BaseModel):
    rule: str
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
