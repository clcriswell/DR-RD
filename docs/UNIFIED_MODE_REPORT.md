# Unified Mode Report

## Findings
No logs found; using static analysis only.

## Deprecation Classification
| path | role | used_by | mode-conditional? | duplicate_of | canonical_target | action | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| orchestrators/router.py | router shim |  | no | core/router.py | core.router | safe_delete | re-export removed |
| core/agents_registry.py | agent registry shim |  | no | core/agents/unified_registry.py | core.agents.unified_registry | safe_delete | unified registry |
| config/mode_profiles.py | profile shim |  | yes | config/modes.yaml | standard profile | safe_delete | single profile |
| evaluators/* | evaluator package |  | no | dr_rd/evaluators/* | dr_rd.evaluators | migrate_copy | package relocated |
