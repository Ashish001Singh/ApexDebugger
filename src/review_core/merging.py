from src.review_core.models import Finding
from src.review_core.models import RuleId  # if not already imported


def merge_findings(regex: list[Finding], llm: list[Finding], regex_owned: set[RuleId]) ->list[Finding]:
  seen = {(f.rule.value,f.line) for f in regex}

  extra_findings = list(regex)
  for f in llm:
    if f.rule in regex_owned:
      continue
    if(f.rule.value,f.line) in seen:
      continue
    extra_findings.append(f)

  return extra_findings