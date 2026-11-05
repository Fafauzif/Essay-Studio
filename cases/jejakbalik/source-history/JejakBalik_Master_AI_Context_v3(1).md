# JejakBalik — Master AI Context Pack

**Current release: 3.0.0. Updated: 4 November 2026, Asia/Jakarta.**

This is the standalone continuation record for JejakBalik's return-trip network overhaul. Read the current sections before relying on an earlier brief. This pack records adopted decisions, the intended service, implemented software, evidence boundaries, source lineage and continuation requirements. It does not turn fictional inputs into observed operations or transfer project ownership from the author.

## 1. Project and current direction

JejakBalik is an innovation proposal and interactive prototype for electronics returns. Its central mechanism is matching eligible electronics with available capacity on journeys logistics providers already intend to make, then coordinating the decisions and handoffs required to reach an accepted recovery destination.

The initial real-service proposition remains institution-funded community collection. A campus, office/community host or program sponsor funds a bounded service. Residents receive access within that scope. Three logistics-provider types contribute different transport capabilities. Qualified downstream operators handle receiving, inspection, reuse/repair, material or specialist pathways. No such real agreement is secured by this prototype.

The core question is: which existing journey can carry this device to an accepted destination with defensible additional travel, time and cost? A nearby vehicle with empty space is insufficient if the receiver, handling, timing, permission or funding is unsuitable.

The owner explicitly asked for a substantial overhaul of both function and 3D design, not a feature list or calendar-based MVP. Preserve the warm miniature identity while giving the city a real operational role. The owner approved fictional partners and routes. Do not invent access to Grab, an e-commerce platform, a carrier API, a real receiver, or Lintasarta's internal data.

## 2. Current delivery contract

Two requested outputs:

1. A complete source ZIP whose contents extract directly into the existing repository root with replacement enabled. No extra wrapper directory and no manual obsolete-file deletion should be required.
2. This updated standalone Markdown context pack. The ZIP also contains the current master at root and under docs.

The user will upload/replace repository contents and deploy through their existing workflow. No external push, production deployment, partner outreach, payment, publication or physical collection is implied by the build instruction.

The source ZIP contains application source, public assets, API/server code, tests, configuration, lockfile and factual setup/evidence documentation. It excludes credentials, node_modules, compiled dependencies and internal reviewer scores/critique conversations.

## 3. Repository and lineage

Current source was cloned successfully from `https://github.com/Fafauzif/JejakBalik-Prototype` at base commit `be9066de5e4f1abeed649c255075a4e4cdfb8898`. This resolves the historical access problem for the different earlier URL `https://github.com/Fafauzif/JejakBalik`, which had returned 404. Do not conflate those repositories.

The base package was version 2.0.0. Prior release history included 1.0, 1.1, 1.2, 1.3.1 and 2.0 source archives. The electronics project is unrelated to the accidentally supplied historical Jejaka/Surabaya learning project and E-Fest/Unilever material; those are not current requirements.

The previous complete master is preserved at `docs/history/v2_COMPLETE_MASTER_CONTEXT.md`. The previous UX contract is archived alongside it. Earlier source, numerical fixtures, test records and brand materials remain for lineage; their presence does not make them active version 3 behavior.

Owner-supplied public site: `https://jejakbalik.vercel.app/network`. It may serve an older version. No new deployment is established by producing the ZIP. Verify the deployed URL and release before updating that status.

## 4. What changed strategically

Earlier JejakBalik emphasized a broad free-to-household collection experience, seven coordination characters, a moving city, authored 48-device story, financial sandbox and fictional annual history. Later work narrowed the payer and initial scope to institution-funded collection.

The current refinement makes cross-provider journey matching the central contribution. Institutional funding is the supporting resource arrangement. Custody, receiving acceptance and exception handling make the transport promise accountable.

The owner correctly identified two weaknesses: the 3D world looked appealing but offered too little meaningful control, and the agent constellation looked like arrows rather than useful coordination. Version 3 addresses those through editable planning inputs, calculated alternatives, route preview, explicit approval and inspectable exception cases.

Backhauling, shared-trip delivery, pickup/delivery routing and traceability are established concepts. JejakBalik's proposed novelty is the contextual configuration across providers, electronics-specific constraints, funded access and accountable handoffs. Do not claim invention of reverse logistics or worldwide first status.

## 5. Intended real operating picture

A host commissions a bounded collection program with categories, service windows, responsibilities and an identified budget. Logistics providers contribute eligible journey offers with existing origins/stops/destinations, recovery capacity, additional-time tolerance and compensation. A receiver declares its acceptance, receiving window and capacity. Owners submit device information and instructions.

JejakBalik compares compatible journey/receiver combinations before promising a collection. An authorized operator approves the selected proposal. Handoffs connect the device or lot to its current custodian. Inspection may change the appropriate disposition, with owner review where required. An unresolved device keeps an assigned responsibility and funded follow-up rather than disappearing from reports.

Institutions buy a defined service: coordination, scheduled access, handoff reconciliation, exception follow-up and reporting. Recovery proceeds are supplementary and conditional on ownership, actual settlement and agreed sharing. Donation and repair-and-return do not automatically generate sales revenue.

The prototype represents this arrangement. Real operation would additionally need accepted contracts, competent handling, applicable permissions, authenticated roles, shared records, incident response and ongoing funding. Software cannot confer those authorities.

## 6. Current application structure

The active entry point is `src/app/App.tsx`, which lazily loads `src/recovery/RecoveryApp.tsx`. The current workspaces are Network, Requests, Decisions and Results. Earlier links resolve into these current surfaces. Retained earlier components are not the authority for version 3 scenario state.

All workspaces read one editable Scenario. Selection and camera changes do not mutate custody or approvals. A route preview is separate from approval. A relevant input change forces a fresh proposal. Visual playback is an inspection aid; explicit simulated service progression owns custody events.

The starting scenario uses three fictional transport providers, six journeys and 18 sample device requests across all ten existing device categories. Providers and receivers are different entities. Current provider names and costs are scenario design choices, not real-company claims or quotations.

The visitor can inspect requests, compare eligible journeys, preview a chosen assignment, approve a revision, edit collection windows, recovery capacity, compensation, provider availability, receiver capacity and funding, and inspect the recomputed results. Unmatched work remains visible. The user-controlled guide follows the same editable system rather than a separate fabricated result path.

## 7. Domain model and planning

Canonical files:

- `src/recovery/types.ts`: entity, plan, event and scene contracts.
- `src/recovery/seed.ts`: fictional providers, journeys, receivers, requests and cost assumptions.
- `src/recovery/model.ts`: planning, options, approval, mutation and simulated service progression.
- `src/recovery/persistence.ts`: strict data parsing, local storage and export.

Coordinates form a fixed complete orthogonal street grid at −36, −24, −12, 0, 12, 24 and 36 on each axis. One coordinate unit represents 0.1 km. Service minutes are offsets from 09:00 WIB. Travel speed, dwell, device masses/slots, offered capacity, driver rates and handling allowances are authored planning assumptions.

Original journey origin, ordered forward stops and destination are retained. Recovery pickup must precede receiving. Candidate insertions are checked for owner consent, vehicle/handling compatibility, mass/slots, pickup/receiving windows, provider/receiver availability, additional-time tolerance, receiver allocation and budget. Choices are deterministic; no global-optimality or learned-traffic claim is made.

Capacity is offered recovery capacity. The model does not simulate every forward parcel's weight or volume. The grid is fictional and does not reproduce Jakarta road conditions. Journey changes cannot alter city geography.

The current conservative boundary is pre-departure assignment and replanning. New work is not inserted into a journey whose start time has already passed. Physically represented custody remains attached to its carrier. This is not GPS-based continuous rerouting from an observed live vehicle position.

## 8. Approval and custody integrity

Approval is scoped to the current revision and calculated proposal. Stale or modified proposals must be rejected. A click on a device, camera movement, playback, import or navigation never grants approval.

Service advancement applies the next chronologically eligible simulated event and preserves monotonic event time. Collection precedes receiving; completion additionally requires consent and data clearance where relevant. Repeated advancement cannot duplicate events.

Completed decision evidence cannot be silently undone. A cancellation does not put a collected device back at a household or reassign its custodian by animation. It produces an outstanding obligation requiring an appropriate resolution.

A data-clearance control records a fictional review decision. It does not erase data, run a sanitization method, issue a certificate or prove regulatory compliance. No processor certificate or signature is fabricated.

## 9. Persistence and local authority

The new version 3 storage namespace is separate from the inherited version 1 records. Inputs and custody history are validated as data. Invalid imports preserve the currently usable session or recover safely, with an explanatory status. Imported cached plans are not executable authority: uncollected assignments require a fresh calculation and approval. Physical history must retain consistent identity, actor and chronological relationships. Accepted imported history is user-provided fictional data, not authenticated evidence of real custody.

Local browser persistence is not a multi-organization backend. There is no production account system, live carrier feed, real booking or payment. Independent browser sessions are separate demonstrations.

## 10. 3D and interaction design

Retained identity: warm light canvas, forest actions, clay emphasis, locally bundled Plus Jakarta Sans, existing logo and original character assets. The owner chose detailed miniature style and user-controlled exploration. Avoid dark command-center styling, generic glowing AI dashboards, decorative gradients, repetitive feature-card grids and forced timed navigation.

New scene ownership:

- `RecoveryWorld.tsx`: immediate interactive SVG map, deferred WebGL loading, view controls and fallback.
- `world-scene.tsx`: fixed composed miniature, vehicles, route layers, camera control, receiving interior and device studio.
- `world-style.css`: world UI and legend treatment.

The fixed world includes residential/ruko/campus/highrise composition, receiver compounds, six recognizable vehicles and roads independent of planned paths. Original journeys use a dashed treatment; planned recovery routes use a solid treatment. Selection focuses the relevant relationship. Vehicle inspection exposes a schematic cargo area and associated planned manifest. Cargo geometry is an explanation, not a measured physical load.

City, vehicle, hub and device views retain selected identity. Hub inventory reflects the relevant simulated phase; requested devices are not represented as already received. Existing ten-category device models support component inspection. Semantic controls and lists provide alternatives to scene gestures. Reduced motion and explicit playback remain supported.

Automatic, Light and High quality settings use the existing preference owner. Light disables shadows and uses lighter geometry; Automatic uses conservative resolution and can reduce work under sustained slow rendering; High permits higher resolution/shadow detail. The 3D renderer is dynamically loaded after the shell/map. Startup or context failure leaves the map usable. Software-rendered WebGL checks establish what was actually rendered in that environment; they do not establish physical laptop or phone performance.

Planning computations run in a dedicated Web Worker. Exact-input keys and request sequences discard stale results. Approvals stay disabled while the current proposal is pending. A disclosed local fallback remains available if workers fail or are unavailable. This changes responsiveness, not the authority of the planning rules.

## 11. Interface and writing

Default language is Bahasa Indonesia with an English control. Domain identifiers and fictional proper names retain identity. Numbers and currency use locale formatting. Use plain actor/action language and explain functions before branded labels.

Main controls express their actual effect: compare journeys, preview pickup, approve assignment, revise a constraint, inspect a handoff. Keep implementation chatter, reviewer scores, assistant introductions, prompt references and generic offers out of the product. Short methodology and assumptions disclosures belong near the results they qualify, not in repeated warnings across every interaction.

Requests provide search, category/status filtering, bounded pagination, creation and inspection. Decisions focus on specific cases rather than a seven-agent diagram. Results derive from the same current scenario and expose coverage, modeled costs, additional travel and outstanding work. Mobile layout preserves usable controls and selection through the shared dialog foundation.

## 12. AI role and budget

Optional server-side assistance uses the inherited controlled endpoint: browser panel → `/api/assistant` → server validation → fixed OpenRouter endpoint → schema-checked suggestion. It supports provisional intake, missing fields, flags and safe next-review advice. It cannot write operational state or authorize collection, consent, data clearance, capacity, payments or outcomes.

Previously adopted budget: USD 1 total on a NEW dedicated provider key. The provider-side total cap is the budget boundary. `OPENROUTER_API_KEY` and `AI_DEMO_ACCESS_CODE` are server-only Vercel variables; never use `VITE_` prefixes. A shared presenter code is for a controlled demonstration, not public production identity. Local review remains available without model access.

The existing helper limits schema/input/output, applies a timeout, avoids automatic retries and labels local fallback distinctly. Paid-model quality and real deployed requests require actual observations. Tests with synthetic upstream responses cannot establish live integration or field safety.

## 13. Economics and comparison

Current numerical inputs are planning assumptions. The demonstration separates provider compensation from category handling allowances. No retained device value automatically becomes platform revenue. Deferred/held work stays in the obligation view.

The comparator uses grouped scheduled collection for the accepted workload. It is an authored alternative, not an observation of an actual partner. Baseline coverage and feasibility must be displayed. When the baseline cannot meet the same service conditions, cost/distance values do not establish an equivalent-service saving. Do not revive the earlier comparison against 41 separate trips as proof of JejakBalik's incremental advantage.

Earlier canonical model figures belonged to a separate 48-device / 189.64 kg authored cohort: 75.2 km grouped versus 319 km separate trips, Rp1,678,174 batch contribution under assumed funding and 20% recovery share. Those are historical fixtures, not current version 3 outputs or field results. The earlier model's remaining 80% settlement was not contracted, and its value-retention figures were not measured useful-life effects.

No avoided-carbon figure, profitable operation, guaranteed collection saving or environmental impact is established. Whole-device input mass is not extracted material yield. A completed simulated pathway is not field proof of reuse placement, recycling or safe treatment.

## 14. Competition context

Competition: #AksiCintaBumi Essay Competition 2026, Departemen Lingkungan Hidup BEM UI 2026 in collaboration with Lintasarta. Theme: Reclaiming E-waste for a Regenerative Future. The owner confirmed a submission deadline of 8 November 2026. The owner explicitly rejected deadline-driven scope reduction for this overhaul.

The supplied guidebook is authoritative for its contents; newer organizer amendments take precedence where actually established. Eligibility is active UI student, individual participation. Main essay: Bahasa Indonesia, 3–5 pages excluding cover/references/appendices, PDF, A4, justified, 1.5 line spacing and 2.5 cm margins on every side. Use Times New Roman: title 16 pt bold, subheadings 12 pt bold, body 12 pt. References use APA 7. The cover includes title and participant name; the header includes the Departemen Lingkungan Hidup BEM UI 2026 and Lintasarta logos. File naming: `#AksiCintaBumi_Nama Peserta`.

The guidebook's essay sequence is title, opening, problem analysis, proposed idea and implementation, impact, and closing. Registration evidence includes participant biodata, current student ID, following `@ui.gogreen`, and sharing the official poster to a personal Instagram story with the specified tags. Submission link: https://bemui.link/SubmissionAksiCintaBumi . Consult the supplied full guidebook for the administrative wording and any organizer amendments; the prototype does not complete these actions.

Base rubric: problem relevance 25%; originality 15%; data/argumentation 20%; clarity/writing 15%; impact/feasibility 25%. There is no universal prototype, PoC, field-pilot or working-AI entry minimum in the supplied guidebook. A prototype supports the main argument; the essay must remain understandable without opening it.

Bonus terms must be relevant and accurate: Lintasarta Peduli Negeri, +10; #AksiCintaBumi, +10; Greener Action, +10. Optional eligible media publication and personal-blog publication can add 10 each. Publication must precede submission and match the submitted manuscript. This build does not authorize publication or outreach.

AI assistance is permitted for research, outlining and editing; the participant's original ideas and factual responsibility remain essential. Do not present this software build as permission to submit a wholly AI-generated essay.

## 15. Company facts and claim boundaries

Official fact sheet: https://www.lintasarta.net/berita/official-fact-sheet-pengelolaan-perangkat-elektronik-dan-e-waste-di-lintasarta/

The program and corporate disposal streams are different. #AksiCintaBumi has a 380 kg collection target, not an established achievement, and five listed dropbox locations. Corporate 48% refers to dismantled devices received at the warehouse that are repaired and returned to production. Formally disposed corporate assets follow a different scrap cohort. Zero NBV is an accounting condition, not zero economic value.

Do not claim Lintasarta currently uses AI for disposal, donates its retired laptops to schools, has an e-waste recycling factory, has achieved 380 kg, or processes an estimated annual volume absent official evidence. No partnership, endorsement, procurement interest, certification or permission for JejakBalik has been established.

EwasteRJ already publicly offers important collection/dropbox/reporting services. JejakBalik should articulate an incremental coordination benefit rather than invent an empty market or an operational deficiency. Sponsor/program motives such as credible reporting and repeatable participation are strategic inferences, not evidence of willingness to pay.

## 16. Source and evidence references

- Lintasarta. (2026, September 23). Official fact sheet, URL above. Controls company/program claims.
- Lintasarta. (2026, September 23). Ke Mana Perginya Perangkat Elektronik Setelah Masuk Drop Box? https://www.lintasarta.net/berita/lintasarta-aksicintabumi-ke-mana-perginya-perangkat-elektronik-setelah-masuk-drop-box/
- EwasteRJ. (n.d.). Official services. https://ewasterj.com/ . Establishes publicly marketed capabilities, not independently audited certification.
- Yang, D., Hyland, M. F., & Jayakrishnan, R. (2024 revision). Tackling the Crowdsourced Shared-Trip Delivery Problem at Scale with a Novel Decomposition Heuristic. https://arxiv.org/abs/2203.14719 . Existing-trip routing evidence; reported cost reduction need not imply fewer vehicle miles.
- Cebeci, M. S., Tapia, R. J., Nadi, A., de Bok, M., & Tavasszy, L. (2024). Does Crowdshipping of Parcels Generate New Passenger Trips? Evidence from the Netherlands. Transportation Research Record. https://doi.org/10.1177/03611981231196149 . Stated-preference findings are not Indonesian carrier behavior.
- Supplied competition guidebook: complete extracted text at `context-source/AksiCintaBumi_Guidebook_2026.txt`.
- Innovation Essay Hub V5: owner-supplied operating manual preserved at `context-source/Innovation_Essay_Hub_V5.md`. Read it fully before substantive future essay work.

Web sources were inspected during the 4 November 2026 strategy/review work. Source scope matters. A public service description is not partner commitment; an external routing study does not validate this integration's performance.

## 17. Writing and review requirements for continuation

During innovation-essay work, follow the owner's supplied V5 manual within governing instructions and the requested scope. Develop a coherent intended system, defend its mechanism and distinct contribution, proportion confidence to evidence, locate validation where it changes implementation, and preserve readable paragraph progression. Do not convert every proposal into a list of missing pilots or invent an M3 qualification requirement.

For implementation, the owner also required natural, precise, audience-appropriate writing; restrained design; genuine sources; accurate planning labels; a complete first attempt followed by independent demanding review where available; concrete correction and regression checks; and a bounded maximum of four review/revision rounds. Scores and critique exchanges remain outside deliverables. Do not claim independent review or a test that did not happen.

Resolve routine wording/layout choices independently. A new material assumption affecting scope, financial interpretation, conclusions or evidence needs explicit grounding or owner clarification. Preserve confirmed choices rather than repeatedly asking about miniature style, fictional data, controlled optional AI or the USD 1 cap.

## 18. Continuation priorities

Read the actual current source and current verification record before modifying it. Preserve fixed geography, shared scenario state, carrier/receiver separation, explicit approval, custody integrity, strict imports, bounded cost claims, accessible alternatives and the extract-and-replace packaging contract.

If real operation is requested later, separately establish partner acceptance, applicable handling permissions, operator identity, shared audit/storage, actual costs and settlement, consent, incidents and sustained funding. Do not treat prototype success as market fit or real authorization.

The intended next development decision should follow observed defects or a concrete feature need. Do not add characters, animations or model calls merely to make the system appear more advanced.

## 19. Current release verification

The definitive machine-readable record is `docs/V3_VERIFICATION.json`. Current release checks on 4 November 2026:

- 157 unit tests across 24 files passed, including 17 current recovery-domain tests and three route-overlay tests.
- TypeScript and the Vite production build passed. Formatting passed. The design-token checker passed all 71 checks. The strict static UI audit reported zero findings.
- Design-context lint reported zero errors and eight orphaned-token warnings. These warnings remain documented; they were not silently treated as a clean lint result.
- All bundle-budget checks passed: initial Network JavaScript 155,457 gzip bytes; deferred renderer 265,961 gzip bytes. The WebGL renderer remains outside the initial static graph.
- All nine browser tests passed with no skipped, unexpected or flaky results. They covered request validation, preview versus approval, cancellation, preserved custody, chronological progression, data hold/clearance/completion, JSON/CSV, invalid and valid import, reload, mobile/English/keyboard behavior, legacy links, four actual WebGL views and renderer recovery.
- Automated axe WCAG A/AA and 2.1 AA checks found zero violations on the initial Network map and Add Device dialog. This is bounded automated coverage, not a complete accessibility certification.
- Actual WebGL initialization failure retained the interactive map. Genuine `WEBGL_lose_context` recovered through the map and an explicit 3D retry.
- A complete archive was extracted over a clean checkout of the original repository baseline. Fresh dependency installation, all 157 tests, production build and bundle checks passed without manually deleting old source files. Final release documentation and the current formatted browser test are included in the completed overlay.

Browser evidence used Chromium 153.0.8010.0 with ANGLE/SwiftShader software rendering, including 1440 × 1000 desktop and 390px-wide mobile checks. The scenes were inspected. No physical-device FPS, battery or thermal benchmark is established. No live paid-model request, field collection, real partner integration or external deployment was performed.

For the starting fictional scenario, the calculation matches 18 of 18 requests, adds 28.8 km to existing journeys and models Rp438,700 in service cost. The grouped comparator serves the same 18 within its modeled constraints at 112.8 km and Rp662,400. These are reproducible authored-scenario outputs, not measured operating savings or a forecast. The reference values are preserved in `docs/V3_REFERENCE_SCENARIO.json`.

**End of current master context.**
