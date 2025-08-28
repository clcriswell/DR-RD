# Simulation Subsystem

This package exposes a small registry of simulators under `dr_rd.simulation`.

## Adding a simulator
1. Implement a subclass of `Simulator` in `dr_rd/simulation/`.
2. Register it via `sim_core.register(domain, simulator)`.
3. Simulators accept a `SimulationSpec` and return a `SimulationResult`.

## Domains
- `mechanical` – simple beam/plate approximation.
- `materials` – trade-off lookup using `materials_db`.
- `finance` – wraps Monte Carlo and NPV tools.

## Schema
Results conform to `dr_rd/schemas/simulation_v1.json`.
