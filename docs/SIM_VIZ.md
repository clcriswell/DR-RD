# Simulation / Digital Twin Visualization

The Simulation panel displays results from `simulate()` calls.

## Single Run
If a single run is returned, numeric keys are rendered as metrics in a result
card.

## Parameter Sweeps
When multiple runs vary a single scalar key, the panel renders a line chart of
`param → output`. Runs are downsampled to `CHART_MAX_POINTS`.

## Monte Carlo
When no single sweep key is detected, outputs are treated as Monte Carlo
samples. A histogram is shown along with mean, median, standard deviation and
5/50/95th percentiles. Runs may be downsampled to `CHART_MAX_POINTS` with a note.

## Caps
Charts downsample above `CHART_MAX_POINTS`. Statistics are computed via
`core.sim.summary.summarize_runs`.
