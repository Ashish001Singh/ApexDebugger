import re
from src.review_core.models import Finding, RuleId, Severity
from pathlib import Path

_APEX_IMPORT = re.compile(r"@salesforce/apex/(\w+)\.\w+")
_SECURITY_RULES = {"missing_crud_fls", "missing_sharing_declaration"}

def correlate(results , lwc_sources) -> list[Finding]:
  insecure = {
    Path(r.filename).stem 
    for r in results
    if any(f.rule.value in _SECURITY_RULES for f in r.findings)
  }
  findings = []
  for lwc_file, js in lwc_sources.items():
    for controller in set(_APEX_IMPORT.findall(js)):
      if controller in insecure:
         findings.append(Finding(
                    rule=RuleId.cross_language_security_risk.value,
                    severity=Severity.HIGH,
                    line=1,
                    message=f"{Path(lwc_file).name} calls Apex controller '{controller}', which has no CRUD/FLS or sharing enforcement.",
                    suggestion=f"Enforce access in {controller} (WITH USER_MODE / as user / Schema checks) before exposing it to the client.",
                ))
  return findings