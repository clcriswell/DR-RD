# Redaction

The redaction system centralizes placeholder mapping for sensitive data.

## Modes
- **light**: removes secrets, email, phone numbers and IP addresses. Person names are
  replaced with placeholders. Organization names and addresses remain.
- **heavy**: applies all light rules and additionally replaces organization names,
  street addresses and device identifiers.

## Placeholders
Entities are replaced with numbered tokens such as `[PERSON_1]`, `[ORG_1]`,
`[ADDRESS_1]`, `[IP_1]` and `[DEVICE_1]`. The mapping is stable within a run so
repeated entities get the same token.

## Allowlists
A global allowlist and optional role-specific allowlists permit certain terms to
pass untouched. For example the Regulatory role whitelists `FAA`, `FDA`, `ISO`,
`IEC` and `CE`.
