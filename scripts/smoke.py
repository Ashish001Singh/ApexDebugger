"""Quick smoke test — runs review() on a known-bad Apex snippet and prints output."""
from src.apex_copilot.review import review

BAD_APEX = """\
public class AccountHelper {
    public void processContacts(List<Id> accountIds) {
        for (Id accId : accountIds) {
            List<Contact> contacts = [SELECT Id, Name FROM Contact WHERE AccountId = :accId];
            for (Contact c : contacts) {
                c.Title = 'Updated';
                update c;
            }
        }
    }
}"""

if __name__ == "__main__":
    result = review(BAD_APEX, filename="AccountHelper.cls")
    print(f"File: {result.filename}")
    print(f"Findings: {len(result.findings)}\n")
    for f in result.findings:
        print(f"  [{f.severity.value.upper()}] L{f.line} {f.rule}: {f.message}")
    if not result.findings:
        print("No findings — smoke test may be broken.")
        raise SystemExit(1)
    print("\nSmoke test PASSED")
