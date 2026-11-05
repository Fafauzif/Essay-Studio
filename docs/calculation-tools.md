# Calculation tools

Run `python studio.py analyze --help`. These are optional supporting tools; do not make every essay into a financial plan or weighted-scoring exercise. A framework needs a stated decision, an interpretable scale and accountable inputs.

## Weighted matrices

```bash
python studio.py analyze score examples/weighted-score.json --output projects/example/output/scores.json
```

Supply `status`, `rating_range` and named factors with explicit `weight` and `rating`. Weights must sum to 1. The calculator rejects mismatches rather than silently normalizing them. Different frameworks have different meanings: an IFE weakness/strength rating is not an EFE response rating or a PESTEL priority. Make the scale and source/team judgment visible in the exhibit. A weighted score does not establish market evidence.

## Cash-flow planning

```bash
python studio.py analyze finance examples/finance-plan.json --output projects/example/output/finance.json
```

`months`, `units`, `unit_price`, `unit_variable_cost` and `fixed_cost` are required model inputs. Scalars repeat over the horizon; arrays must match the horizon exactly. Label money using `currency` and `price_year`, and state `price_basis` in the input/assumption record. Match constant-price cash flows with a real discount rate and nominal flows with a nominal rate; the calculator does not infer inflation or discount type from a year label. Optional inputs: retainer, other_cost, setup_cost, annual_discount_rate, receipts_lag_months, retainer_prepaid, planned_financing and reserve_months_fixed. Retainer receipts use the specified same-month prepaid share and one-month delay for the remainder. Unit receipts use the specified integer lag.

The tool distinguishes accrued revenue, cash receipts, receivables, operating cost, project cash before financing and cash with planned financing. Planned financing is not revenue. NPV uses cash flow, initial investment, and the annual effective discount raised to month/12. Sustained payback is the first nonnegative project-cash month after which it remains nonnegative through the horizon. Funding need includes the specified fixed-cost reserve. Unknown input keys are rejected, so a misspelled timing assumption cannot silently become a different model. Put additional explanatory fields under metadata.

This intentionally simple general model does not automatically add workforce capacity, onboarding, taxes, debt, depreciation, resale proceeds or terminal value. Add them as explicit inputs or extend the project-specific model when they affect the argument. Do not present its generic output as a full financial feasibility conclusion. JejakBalik's more specific preserved model lives in its case directory and includes its own funded-work checks; its rates and acquisition schedule are not global defaults.

## Conditional Monte Carlo

Add `uncertainty` with draws, seed and a stable ordered factors object. Supported factors: units_factor, price_factor, variable_cost_factor, fixed_cost_factor and retainer_factor. Marginals may be uniform or triangular with explicit finite bounds/mode. One sampled factor vector is held across the full horizon for each run; factors are not redrawn monthly.

Optional `latent_correlation` is a symmetric positive-semidefinite correlation matrix in the printed factor order. The method is a Gaussian copula with the requested marginal inverse CDFs. This is **latent-normal dependence**, not a claim that the transformed marginal Pearson or Spearman correlations equal that matrix. State why a dependence choice makes sense; do not add sophisticated distributions just for appearance.

The output preserves seed, generator, NumPy version, factor order, marginals and dependence, conditional frequencies, P10/P50/P90 and Spearman rank associations. Frequencies are conditional on specified team distributions and model structure; they are not measured probabilities of commercial success. Undefined associations for constant inputs/results are null, not fabricated correlations. Simulations stream scalar outcomes rather than retaining all monthly reports, and reject work above 5,000,000 month-draws. Reduce horizon/draws deliberately when needed; the tool never silently reduces statistical effort. Keep example inputs clearly illustrative. Obtain decision-useful parameter ranges and compare sensitivities before using a simulation in a real entry.

The repository examples use constructed planning data. They have no external empirical source and must not be cited as research.
