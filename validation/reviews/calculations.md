# Independent quantitative review — final analysis tools

Reviewed the repaired `essay-studio/skills/write-innovation-essays/scripts/analysis.py` and updated `docs/calculation-tools.md` after the round-one findings. Current analysis source SHA-256:

`1966d3d6c904ce83b678cea1789da0af68af07f93dc9539b72d7ee0424556f60`

No packaged source was edited by this reviewer. This review is limited to the optional calculation tools and their documented interpretation, not the entire repository, all chart renderers or the archived JejakBalik model.

## Final verdict

All three round-one issues are repaired in the actual current source and verified behavior. The original 21 independent hand-derived/CLI/distribution checks still pass. Seven targeted repair checks and all 11 current unit tests also pass. No further quantitative or execution defect requiring repair was found in this scope.

The accounting formulas and conditional-simulation meaning remain correct for the documented inputs: accrued revenue, cash collection, receivables, operating costs, setup, financing, reserves, NPV and sustained payback remain distinct. Weighted scores preserve stated weights/scales without silent normalization. The simulation reports latent-normal dependence honestly and does not call its conditional frequencies measured market probabilities.

## Confirmed repairs

| Round-one issue | Actual current behavior | Verification |
|---|---|---|
| Misspelled optional financial input silently ignored | Unknown top-level finance keys are rejected with an explicit message. | `receipts_lag_month:1` now raises `Unknown financial input keys`; the real CLI exits 2 and creates no new result file. |
| Unknown uncertainty setting could fall back silently | Unrecognized uncertainty keys are rejected. | A supplied `sed` instead of `seed` raises `Unknown uncertainty settings`. |
| Full monthly result retained for every draw | Monte Carlo writes only NPV/funding scalars into arrays and requests `include_monthly=False` from the financial calculation. | Source inspected; scalar-only result equals all non-monthly fields of the ordinary output; bounded memory probe below confirms the presentation-history retention is removed. |
| Accepted draw/horizon combination could be excessive | Work above 5,000,000 month-draws is rejected explicitly. | The old extreme 100,000-draw × 1,200-month configuration raises the budget message before sampling; no large simulation was executed. |
| Named-factor documentation not enforced | A nonempty string factor label is required. | Anonymous weighted row now raises the factor-label error. |

The new metadata escape preserves harmless explanatory input without silently turning it into a model parameter. A case with `metadata.author_note` returns exactly the same financial result as the corresponding case without metadata.

## Bounded memory evidence

The same small probes were used before and after the repair, holding draws at 100. These measure Python allocations through `tracemalloc`, not complete operating-system resident memory.

| Horizon | Before repair | After repair |
|---|---:|---:|
| 12 months | 630,159 bytes | 15,546 bytes |
| 24 months | 1,192,630 bytes | 14,603 bytes |

The earlier near-doubling from stored monthly dictionaries is absent. The small difference between the two repaired measurements is allocation/probe variation; it is not a claim that longer horizons always use less memory. The sampler still allocates factor/sample/output arrays proportional to draws and factor count, and the explicit month-draw ceiling bounds the accepted work. No maximal-budget performance or out-of-memory test was needed or performed.

## Checks rerun and preserved

The review reran all 21 independent checks from `analysis-review-work/independent_checks.py`. They cover mixed retainer/unit timing, one-month versus horizon-wide lag, setup, receivables, separate planned financing, changing reserve needs, sustained rather than temporary payback, twelve-month effective annual discount, weighted products/invalid sums, uniform/triangular inverse CDFs including endpoint modes, seeded repeatability, constant-output null rank association and singular positive/negative copula dependence. Real CLI finance/score paths and error exits are included.

Seven additional targeted repair checks exercised unknown finance and uncertainty keys, anonymous factors, combined effort bound, accepted explanatory metadata, scalar-only/full-output equality and the real CLI's invalid-key behavior. All passed. The repository's 11 analysis tests also passed.

The financial example's previously checked aggregate identities remain appropriate: 425 illustrative units, 85 million IDR accrued revenue, 68.25 million operating cost, 72 million receipts, 13 million receivables and −4.25 million closing project cash after setup. This reviewer did not redundantly rerun the full example's 10,000 draws solely to inspect input validation; the producer is separately recomputing/comparing that existing example. No claim is made here of independently certifying every 10,000-draw result or cross-platform SVD bit identity.

## Final scores within this scope

| Dimension | Score /10 | Observable basis |
|---|---:|---|
| Task fulfillment | 8.9 | General, optional weighted/cash/simulation functions and working CLI fulfill the requested calculation role without introducing case-specific commercial assumptions. |
| Quantitative correctness | 9.0 | Independent hand calculations, inverse-CDF identities, dependence bounds and accounting/CLI tests remain correct; repairs do not change the defined method. |
| Completeness | 8.9 | Important input/status/timing/method distinctions are documented, factor labels are required and the simplified model's exclusions remain explicit. |
| Clarity/usability | 8.8 | Typos now yield clear errors, metadata has an explicit place and conditional-frequency interpretation is accurate. |
| Execution robustness | 8.9 | Streaming scalar outputs removes the observed memory retention; effort is explicitly bounded and meaningful invalid inputs are rejected. |

Scores reflect the inspected implementation and evidence rather than a guarantee about every future financial model or runtime. There is no known outstanding critical error or unmet requirement in this calculation-tool review. No further repair is requested here.
