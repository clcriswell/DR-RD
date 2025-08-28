# Red Teaming

A small harness replays curated jailbreak payloads located in
`dr_rd/safety/jailbreaks.yaml` against agent prompts. The harness asserts that
safety guardrails remain in place, outputs stay JSON valid, and no system or
developer prompts leak.

## Extending
Add new payloads to `jailbreaks.yaml` to simulate prompt injections, role
overrides, JSON escapes, or Unicode tricks. Run the harness via
`python -m evaluators.redteam_jailbreak` or through tests.

## Local Use
The harness uses locally mocked outputs and performs no network calls.
