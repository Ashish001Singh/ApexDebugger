# Salesforce Apex Best Practices

<!-- Curated grounding for the LLM reviewer. Keep tight — this whole file is
     stuffed into the prompt on every review (small-corpus RAG, no vector DB).
     Each section should map to a RuleId so grounded reasoning speaks our vocabulary. -->

## Governor Limits

- SOQL: 100 queries per transaction. Never query inside a loop (`soql_in_loop`) —
  collect IDs, query once with an `IN` clause.
- DML: 150 statements per transaction. Never DML inside a loop (`dml_in_loop`) —
  collect records in a List, one DML after the loop.
- api call is 100 in per transaction so look out for that
- heap size for synchronous call is 6 mb and async call 12 mb

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
- avoid lots of Schema calls
- Proper naming of methods, classes and variables
- Code should be bulkified(it should handle not for one record but may record)
- separatiuon of work should be there like Selector class should contain class
- unit of work done separate
- handler class separate
- Use a Single Trigger per SObject Type
- Use SOQL for Loops
- Test Multiple Scenarios
- Modularize Your Code
- Avoid Business Logic in Triggers
- Avoid Returning JSON to Lightning Components

## Exception Safety

- DML can throw `DmlException` — handle or justify (`exception_risk`).
- inserting setup and non setup object can make mixed DML exceptions
  DmlException Any problem with a DML statement, such as an insert statement missing a required field on a record.
  DuplicateMessageException Attempt to enqueue job with duplicate queueable signature
  FinalException Any attempt to mutate a read-only collection or record such as an sObject in an after-update trigger, or a final variable. This exception causes execution to halt.
  IllegalArgumentException An illegal argument was provided to a method call. For example, a method that requires a non-null argument throws this exception if a null value is passed into the method.
  InvalidHeaderException An illegal header argument was provided to an Apex REST call. For example, a call to the RestResponse.addHeader(name, value) method throws this exception if the header name is cookie.
  LimitException A governor limit has been exceeded. This exception can’t be caught.
  JSONException Any problem with JSON serialization and deserialization operations. For more information, see the methods of System.JSON, System.JSONParser, and System.JSONGenerator.
  ListException Any problem with a list, such as attempting to access an index that is out of bounds.
  MathException Any problem with a mathematical operation, such as dividing by zero.
  NoAccessException Any problem with unauthorized access, such as trying to access an sObject that the current user doesn’t have access to. This exception is used with Visualforce pages.
  NoDataFoundException This exception is used with both Visualforce pages and Salesforce Functions.
  Salesforce Functions: The exception is thrown when the project or function name provided in the functionName parameter to the Function.get() method can't be found. For more information on Salesforce functions, see Function.get().
  NoSuchElementException This exception is thrown if you try to access items that are outside the bounds of a list. This exception is used by the Iterator next method. For example, if iterator.hasNext() == false and you call iterator.next(), this exception is thrown. This exception is also used by the Apex Flex Queue methods and is thrown if you attempt to access a job at an invalid position in the flex queue.
  NullPointerException Any problem with dereferencing null. For an example, see NullPointerException Example.
  QueryException Any problem with SOQL queries, such as assigning a query that returns no records or more than one record to a singleton sObject variable.
  SearchException Any problem with SOSL queries executed with SOAP API search() call, for example, when the searchString parameter contains fewer than two characters. For more information, see the SOAP API Developer Guide.
  SecurityException Any problem with static methods in the Crypto utility class. For more information, see Crypto Class.
  SerializationException Any problem with the serialization of data. This exception is used with Visualforce pages.
  SObjectException Any problem with sObject records, such as attempting to change a field in an update statement that can only be changed during insert.
  StringException Any problem with Strings, such as a String that is exceeding your heap size.
  TransientCursorException A transient problem with an Apex cursor transaction. The failed transaction can be retried.
  TypeException Any problem with type conversions, such as attempting to convert the String 'a' to an Integer using the valueOf method.
  UnexpectedException A non-recoverable internal error within Salesforce has occurred. This exception causes execution to halt.
  XmlException Any problem with the XmlStream classes, such as failing to read or write XML.
- Guard null dereference and list index bounds.
