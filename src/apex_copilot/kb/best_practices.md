# Salesforce Apex Best Practices

<!-- Curated grounding for the LLM reviewer. Keep tight — this whole file is
     stuffed into the prompt on every review (small-corpus RAG, no vector DB).
     Each section should map to a RuleId so grounded reasoning speaks our vocabulary. -->

## Governor Limits
- SOQL: 100 queries per transaction. Never query inside a loop (`soql_in_loop`) —
  collect IDs, query once with an `IN` clause.
- DML: 150 statements per transaction. Never DML inside a loop (`dml_in_loop`) —
  collect records in a List, one DML after the loop.

## Security — CRUD/FLS and Sharing
- Enforce CRUD/FLS (`missing_crud_fls`): `WITH USER_MODE` (SOQL), `as user` (DML),
  `WITH SECURITY_ENFORCED`, or explicit `isAccessible()/isCreateable()` checks.
- Sharing (`missing_sharing_declaration`): declare `with` / `without` / `inherited sharing`
  at the CLASS level. USER_MODE/SYSTEM_MODE are operational, not class declarations.
- System mode (`explicit_system_mode`): `WITH SYSTEM_MODE` / `as system` bypasses
  security deliberately — must be justified.

## Performance
- Cyclomatic complexity (`high_complexity`): class ≤ 40, method ≤ 25.
- Nested loops (`nested_loop_2` / `nested_loop_deep`): 2 levels = review, 3+ = CPU/heap risk.
- Consolidate redundant DB calls (`unbatched_db_calls`).

## Maintainability
- No duplicate methods (`duplicate_method`).
- Hoist repeated literals into constants (`missing_static_constant`).
- No hardcoded IDs (`hardcoded_id` / `hardcoded_external_id`) — org-specific, breaks deploys.

## Exception Safety
- DML can throw `DmlException` — handle or justify (`exception_risk`).
- Guard null dereference and list index bounds.
