# Build Spec & Work Plan

DR-RD emits a build specification package alongside the final proposal. The package contains:

- `SDD.md` – System Design Doc with requirements, interfaces and risks.
- `ImplementationPlan.md` – work items, milestones and rollback notes.
- `bom.csv` – lightweight bill of materials.
- `budget.csv` – phase-level budget summary.
- `interface_contracts/` – markdown stubs for each interface contract.

All files are written under `audits/<project_slug>/build/`.

The build spec and work plan are generated automatically. After a run completes, download links for these files appear in the app.
