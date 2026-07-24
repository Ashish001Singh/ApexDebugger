# LWC Best Practices

## General

- Prefer Lightning Web Components (LWC) over Aura.
- Follow Salesforce official best practices only.
- Report only genuine issues; avoid false positives.
- Ignore formatting or stylistic preferences unless they affect quality.
- Keep recommendations concise and actionable.

## Data Access

- Prefer Lightning Data Service (LDS) for standard CRUD operations.
- Use `@wire` for reactive, cacheable data retrieval.
- Use imperative Apex only when user interaction or dynamic execution is required.
- Mark read-only Apex methods with `@AuraEnabled(cacheable=true)`.
- Minimize server round trips.

## Error Handling

- Wrap `async/await` Apex calls in `try/catch`.
- Always use `.catch()` for Promise-based Apex calls.
- Display user-friendly errors using `lightning/toast` or equivalent.

## Performance

- Avoid duplicate Apex calls.
- Cache data whenever possible.
- Avoid unnecessary component re-renders.
- Do not perform expensive computations inside getters.
- Use client-side filtering/sorting when appropriate.
- Lazy load large datasets.

## Reactivity

- Prefer reactive properties over manual DOM updates.
- Update state instead of manipulating HTML.
- Use getters only for derived values.

## DOM

- Avoid direct DOM manipulation.
- Prefer template directives (`if:true`, `lwc:if`, `for:each`).
- Use `this.template.querySelector()` only when necessary.
- Use `lwc:dom="manual"` only for approved third-party integrations.

## Security

- Follow Lightning Web Security (LWS) guidelines.
- Prevent XSS vulnerabilities.
- Avoid unsafe HTML injection (`innerHTML`).
- Validate all external input.
- Respect CRUD/FLS in Apex.

## Templates

- Always provide a unique `key` in `for:each`.
- Avoid duplicate IDs.
- Use semantic HTML.
- Prefer Lightning Base Components over custom HTML.

## JavaScript

- Remove unused variables, imports, and methods.
- Avoid duplicated logic.
- Use optional chaining where appropriate.
- Use `const` unless reassignment is required.
- Keep methods small and focused.

## Component Design

- Prefer composition over inheritance.
- Keep components reusable.
- Separate UI, business logic, and data access.
- Avoid tightly coupled components.

## Accessibility

- Use accessible Lightning Base Components.
- Provide labels and alternative text.
- Ensure keyboard accessibility.
- Preserve semantic HTML.
