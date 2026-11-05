# Independent chart gallery review

Reviewer: document production agent, independent of the chart author. Scope: the 13 shipped examples covering 12 chart families, the source generator, the usage guide, and one additional long-label Gantt stress fixture. This is a visual and mechanical review of reusable figures, not a verification of the illustrative business assumptions.

## Review method

Opened every actual gallery PNG, checked the corresponding one-page PDF and generated TEX, and compared displayed labels/values with the example JSON. Read the generator and guide. Recomputed the distribution's 24 histogram bins and P10/P50/P90 using NumPy, checked the cash series arithmetic, measured PDF text bounds and effective point sizes, compared stored source hashes with actual JSON, and exercised invalid size/font/number input rejection. Created a separate Gantt fixture outside the package using ordinary long Indonesian task labels, then compiled and opened the result.

Files reviewed: cash, comparison, drivers, gantt_strategy, gantt_year1, issue_tree, market_layers, npv_distribution, positioning, risk_heatmap, service_flow, stakeholder_structure, and value_proposition, each under `skills/write-innovation-essays/assets/charts/{examples,previews}/`.

## First-pass findings

1. **Distribution reference lines inherited the histogram bar style.** In `scripts/charts.py`, `distribution()` placed percentile coordinate pairs with `addplot` inside an axis whose global style was `ybar`. The actual PNG displayed three dashed rectangles, with both a left and a right edge, instead of three single vertical percentile references. The histogram's counts and percentile calculations themselves were correct. Requested explicit line style override and a real re-render.

2. **Long Gantt labels could silently overlap.** `gantt()` fixed all row heights at 0.67 cm while allowing unconstrained wrapped task labels. The shipped examples remained readable, but a separate fixture with 94–97-character Indonesian task labels compiled successfully and produced overlapping labels across neighboring rows. Requested adaptive row heights or a clear pre-render limit. Repro input and opened result: `qa_chart_review/long-gantt.json` and `qa_chart_review/review_gantt_long.png`, outside the deliverable tree.

3. **Nominal font size needed a clearer explanation.** Node-based diagrams use `resizebox`, so the configured `font_pt` does not guarantee the same effective point size after placing the image in Word. At the supplied 14–16 cm sizes the gallery is readable; shrinking a dense VPC or Gantt to 12 cm would reduce its text to roughly 7 pt. Requested an explicit guide note about resizing, actual placement width, and splitting/reflow where a guidebook specifies a minimum figure font. This is a documentation improvement, not a defect in the current 16 cm examples.

## Data and layout checks

- All 13 actual PDFs are one page, their input hashes match the shipped JSON, and all extracted text bounding boxes lie within their page bounds.
- Histogram: 1,200 observations; the 24 bin counts agree exactly with NumPy. Linear percentile values independently agree: P10 7.1536, P50 98.879, P90 202.9138, in the figure's stated illustrative NPV unit of million rupiah.
- Cash: each funded value equals its corresponding unfunded value plus Rp100 million, throughout all 24 ordered periods. Axis units match the JSON.
- Comparison: 30 km and 115 km use a common zero baseline. Drivers preserve the seven supplied signed associations and explicitly identify Spearman association rather than causation.
- Gantt: the shipped first-year and strategy bars use inclusive period bounds matching their input. The strategic chart covers the ten supplied years; it does not imply that every project needs ten years.
- Risk positions match each supplied impact/likelihood score. The diagram is an ordinal prioritization display rather than a measured probability chart.
- TAM/SAM/SOM arithmetic agrees with the displayed bases: 2,000 × Rp60 million = Rp120 billion; 100 × Rp60 million = Rp6 billion; 8 × Rp60 million = Rp480 million. The guide correctly describes nested circles as schematic, not area proportional.
- Issue tree preserves one goal, multiple subproblems, issues and root causes, with distinct orthogonal connectors. The example's hypotheses are identified as demonstration content in metadata/guidance, not falsely cited research.
- Service flow has six ordered stages, a visible exception/held-case branch and a return path. Positioning axes and point locations agree with the supplied qualitative assessment. Stakeholder parent/child relations agree with the JSON. The VPC uses readable phrases and restrained structure rather than slide banners.
- Current gallery text is generally around 9–11 pt in the actual PDFs; the histogram's percentile labels are about 8 pt. `font_pt` alone is not proof of competition-format compliance at another placement size.
- Zero/NaN width, zero height, zero/bool font size, font-name TeX injection and invalid hex color values are rejected. Literal TeX-sensitive labels escape the tested characters, and the compilation command disables shell escape. These are bounded robustness checks, not a security audit.

## Revision verification

- Re-opened the corrected histogram PNG: the three percentile references are now single vertical lines at the correct values. TEX explicitly overrides the inherited bar style with `sharp plot`. The author also groups coincident quantile labels; that additional case was inspected in source/pure-data tests, not visually rendered by this reviewer.
- Re-opened both revised shipped Gantts and the exact separately supplied long-label stress case under `qa_chart_review/corrected/`. Rows now follow actual TikZ text boxes; no neighboring labels overlap, and each bar is centered on its associated label. The long case expands vertically instead of shrinking the text.
- Read the updated guide note: `font_pt` is explicitly nominal for diagrams scaled as a whole. It instructs the author to verify effective text size, place wide, reflow or split, and follow the current guidebook.
- Repeated current-file PDF bounds and source-hash checks after the repairs: all 13 remain one page with matching inputs and no extracted text beyond page bounds. Checked all 123 ordinary supplied label strings in the generated TEX; none missing.
- Ran the generator's 14 pure-data/escaping/PNG regression checks and independently exercised seven malformed size/font/color configurations; they passed/rejected as expected. This does not replace actual render inspection.

Selected measured effective minimum point sizes after proportional placement (includes ticks/annotations):

| Figure | At 16 cm | At 12 cm |
|---|---:|---:|
| Issue tree | 10.34 | 7.75 |
| Service flow | 8.95 | 6.72 |
| Value proposition | 9.20 | 6.90 |
| Gantts | 8.74 | 6.55 |
| Positioning | 9.42 | 7.07 |

These figures support wide placement of dense diagrams. They do not establish that a particular competition permits those sizes. A submission imposing a larger minimum needs reflow, splitting or different geometry and a new render check.

## Assessment

The initial faults were substantive enough to prevent approval of the first pass. After correction, no known critical defect or unmet requirement remains within this review scope. The actual gallery is suitable as a reusable starting point, with each project's own evidence and final placed-size check.

| Dimension | Final score | Observable basis |
|---|---:|---|
| Task fulfillment | 9.0 | Twelve requested chart families, two useful Gantt configurations, actual editable TEX and rendered previews; restrained essay figures instead of slide banners. |
| Correctness | 8.9 | Values, signs, periods, units, histogram counts and percentiles checked; reference-line fault fixed on the actual render. Examples remain illustrative inputs, not verified business forecasts. |
| Completeness | 8.9 | Working source/schema/guidance and outputs cover the supplied visual patterns; native tables are recommended for table-shaped content. No claim that arbitrary future input has been validated. |
| Clarity and usability | 8.8 | Long-label Gantt repair demonstrated on a separate case; meaningful labels, units, readable multi-actor diagrams, and explicit nominal/effective font guidance. Dense charts need wide placement. |
| Presentation and execution | 8.9 | Actual PNGs opened, no page clipping, consistent serif typography, limited palette, clean edges; no decorative headings or generic callouts. Final competition document still requires its own all-page layout check. |

These are evaluator judgments supported by the bounded checks above, not measured performance scores or a claim of perfection.
