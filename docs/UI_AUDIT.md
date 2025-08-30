# UI Heuristic Audit

![Run form](images/run_form.png)
![Trace viewer](images/trace_viewer.png)

TODO: replace with live screenshots.

| Heuristic | Issue | Impact | Priority | Location |
| --- | --- | --- | --- | --- |
| Visibility of system status | Progress spinner absent on long runs | Users may think app hung | P0 | [app/__init__.py](../app/__init__.py) |
| Match with real world | Domain jargon in labels | Confuses new users | P1 | [app/ui/sidebar.py](../app/ui/sidebar.py) |
| User control & freedom | No cancel button for runs | Forces reload | P1 | [app/agent_runner.py](../app/agent_runner.py) |
| Consistency & standards | Mixed button styles | Slows scanning | P2 | [app/ui/components.py](../app/ui/components.py) |
| Error prevention | Run form accepts empty fields | Leads to failures | P0 | [app/__init__.py](../app/__init__.py) |
| Recognition vs. recall | Filters require manual typing | High cognitive load | P2 | [app/ui/trace_viewer.py](../app/ui/trace_viewer.py) |
| Flexibility & efficiency | No keyboard shortcuts | Slows power users | P2 | [app/ui/a11y.py](../app/ui/a11y.py) |
| Aesthetic & minimalist design | Dense trace table | Hard to parse | P1 | [app/ui/trace_viewer.py](../app/ui/trace_viewer.py) |
| Help users recover from errors | Toast lacks retry link | Blocks flow | P1 | [app/ui/components.py](../app/ui/components.py) |
| Help & documentation | No inline help | Increases support load | P2 | [app/ui/sidebar.py](../app/ui/sidebar.py) |

Coverage includes information architecture, clear labels, affordances, feedback for loading and empty states, and basic accessibility (contrast, focus order, text size, motion, color reliance).
