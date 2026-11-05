# Editable document production

This guide describes the portable tools shipped with Essay Studio. These tools
format supplied content; they do not verify research, invent an APA reference,
translate prose or decide whether a business model is credible. Use the writing,
evidence and review workflow before authoring the final project JSON.

## Contents

1. Commands and dependencies
2. Project structure and formatting
3. Content blocks and links
4. Tables, figures and QR access
5. References and appendices
6. Page counts and verification
7. Private comment extraction
8. Example and limitations

## Commands and dependencies

Run commands from the repository root using the Python environment that has the
declared dependencies installed. The scripts use relative file paths and the
system PATH; no ChatGPT workspace path is required.

```bash
python skills/write-innovation-essays/scripts/build_docx.py \
  examples/short-demo.json --output output/essay.docx

python skills/write-innovation-essays/scripts/render_document.py \
  output/essay.docx --out-dir output/render

python skills/write-innovation-essays/scripts/audit_document.py \
  output/essay.docx --pdf output/render/essay.pdf \
  --project examples/short-demo.json --output output/audit.json
```

Required Python libraries are `python-docx`, `Pillow`, `PyMuPDF` and `lxml`.
QR generation additionally uses `qrcode`. LibreOffice (`soffice` or
`libreoffice`) must be available for DOCX-to-PDF conversion. Font availability
is an independent environment requirement: check the actual exported PDF for
substitution. A browser-only model cannot execute these commands without an
appropriate tool environment.

When a supplied project contains QR blocks, the audit can independently decode
their embedded image bytes if optional OpenCV and NumPy are available. It
compares decoded payloads with the declared URLs and keeps live access marked
`not_checked`. Without those optional libraries, QR verification is explicitly
unverified and must be completed separately.

The renderer accepts an existing PDF as input when an author has exported it
manually. It rasterizes every page and records what it actually did. An absent
converter produces `status: unavailable` and exit code 2; it never reports a
visual pass from an unrendered DOCX.

## Project structure and formatting

The complete runnable example is `examples/short-demo.json`. A minimal project
is:

```json
{
  "title": "A specific subject and proposal",
  "format": {
    "font": "Times New Roman",
    "body_pt": 12,
    "table_pt": 10,
    "page_width_cm": 21,
    "page_height_cm": 29.7,
    "margin_cm": 2.5,
    "line_spacing": 1.5,
    "first_line_cm": 1,
    "paragraph_after_pt": 0
  },
  "body": [{"type": "paragraph", "text": "Author-approved prose."}],
  "references": [],
  "appendices": []
}
```

The default house style reflects this user's preferences. **It is not a claim
that every competition permits these settings.** Read the current guidebook
and override the relevant values, especially paper size, type size, line
spacing, table type and appendix eligibility. A new project does not inherit
JejakBalik's five-page limit, cover arrangement, QR-first requirement or
permission for 10 pt appendix tables.

Supported format settings:

| Field | Default | Meaning |
|---|---:|---|
| `page_width_cm`, `page_height_cm` | 21, 29.7 | A4 portrait dimensions |
| `margin_cm` | 2.5 | All four margins |
| `margins_cm` | absent | Optional object with `top`, `bottom`, `left`, `right` overrides |
| `font` | Times New Roman | Requested family; verify actual PDF family |
| `body_pt`, `title_pt`, `heading_pt` | 12, 16, 12 | Native Word text sizes |
| `table_pt`, `caption_pt` | 10, 12 | Table and caption sizes |
| `line_spacing` | 1.5 | Normal prose spacing |
| `paragraph_after_pt` | 0 | Normal paragraph after-spacing |
| `first_line_cm` | 1 | Narrative first-line indent; labels/headings are unindented |
| `table_header_fill` | E8EFEA | Light sage header; text remains black |
| `table_border` | D9D9D9 | Thin light-grey native grid |
| `references_new_page` | true | A clean boundary for reference material |
| `appendices_new_page` | false | Continuous appendix flow |
| `page_numbers` | true | Centred PAGE field |
| `header_distance_cm`, `footer_distance_cm` | 0.7, 1 | Positions outside the main text region |

Set the reader-facing language labels explicitly. `language` records intent;
it does not translate content or choose a dictionary automatically.

| Label | Indonesian default | English example |
|---|---|---|
| `references_heading` | Daftar Pustaka | References |
| `appendices_heading` | Daftar Lampiran | Appendix index |
| `appendix_label` | Lampiran | Appendix |
| `return_label` | Esai | Essay |
| `index_label` | Daftar lampiran | Appendix index |

An optional `template` path supplies styles. Existing body content, document
relationships for old content and author metadata are cleared before the new
project is written. Always review inherited styles and metadata in the actual
output; do not use a reference essay's participant identity as the new author.

`skills/write-innovation-essays/assets/templates/neutral_essay.docx` is a clean style starter with only an
`[Essay title]` placeholder. It does not contain competition-specific logos,
author names, research or a boilerplate essay.

For a project JSON stored in `examples/`, its relative template value is
`../skills/write-innovation-essays/assets/templates/neutral_essay.docx`.

Optional cover and logos:

```json
{
  "cover": {"enabled": true, "lines": ["[Essay title]", "[Participant name]"]},
  "header": {
    "logos": [{"path": "assets/organizer.png", "height_cm": 0.65}]
  }
}
```

Asset paths resolve relative to the project JSON's directory. Absolute local
paths are accepted for an explicitly supplied asset but should be replaced by
relative paths before sharing a reproducible project. Never embed a private
signed URL, token or temporary machine path in an audience-facing caption.

## Content blocks and links

`body` and each appendix's `blocks` accept these types:

| Type | Required fields | Optional fields |
|---|---|---|
| `paragraph` | `text` or `runs` | `id`, `indent` (default true) |
| `heading` | `text` | `id`, `level` (1–3) |
| `table` | `headers`, `rows` | `title`, `widths_cm`, `alignments`, `font_pt`, `note` |
| `image` | `path` | `caption`, `width_cm`, `max_height_cm` |
| `image_pair` | `items` | `widths_cm` |
| `qr` | `url`, `label` | `visible_url`, `width_cm` |
| `page_break` | none | Use only where the document requires a deliberate break |

A heading `id` is a stable destination, not visible numbering. Avoid reserved
IDs `essay`, `references` and `appendix_index`. Long IDs are shortened with a
stable hash suffix to fit Word bookmark constraints; conflicting IDs produce
an error rather than silently taking the reader elsewhere.

In ordinary paragraphs and table cells, `Lampiran A.1` and `Appendix A.1`
automatically become black bold underlined hyperlinks to appendix `A.1`.
Headings are not automatically linked to themselves. Unknown destinations
cause a build error. For deliberate labels or external links, use spans:

```json
{
  "type": "paragraph",
  "runs": [
    {"text": "The unit calculation is shown "},
    {"text": "in Appendix B.1", "target": "B.1"},
    {"text": ". "},
    {"text": "The primary source", "url": "https://example.org/source"}
  ]
}
```

The example URL above is syntax illustration, not a research source.
Plain spans can set `bold` and `italic`. Put appendix calls beside the claim
they support; the formatter cannot decide whether a target actually supports
that claim. A structurally valid link can still be semantically wrong.

## Tables, figures and QR access

Provide intentional widths in centimetres. The sum must fit the current text
region. Every row must contain the same number of cells as the header. The
builder rejects invalid dimensions rather than shrinking the required type.

Use `alignments` entries `left`, `right`, `center`, or `justify`. If omitted,
numeric body cells align right; short labels align left; longer narrative
cells are justified. Explicit alignment is preferable when a narrow column
contains codes or long Indonesian labels.

Tables use native editable cells, repeating headers, white body rows and no
fixed row heights. A note occupies one merged final row. The last data row
stays with its note to avoid a continuation that contains only a repeated
header and source line. Caption/source text is authored input: distinguish
observations, estimates and constructed examples where interpretation needs
that distinction, without adding generic warnings to every exhibit.

Images retain their aspect ratio and are centred with captions. A figure's
width is clamped to the text region; `max_height_cm` can constrain its height.
Choose those dimensions by the final placed text size. A high-resolution
screenshot still becomes unreadable when a full interface is printed too
small. Crop to the relevant real state before inserting it; do not recreate a
real prototype result through image generation.

`image_pair.items` contains ordinary image objects. Default columns split the
text width equally; supply `widths_cm` for an asymmetric pair. The entire row
is kept together, so a pair taller than a page must be rethought before
delivery. The tool does not automatically replace a complex interface with a
fake simplified screenshot.

A `qr` block generates a real code for its supplied URL and prints the honest
label plus a clickable visible URL. The build does not verify live access or
whether the current deployment matches screenshots. Check both separately.
For a project that explicitly needs access before the appendix index, set
top-level `appendix_index_position` to `after_first` and make the first
appendix the access section. This is optional, not a generic essay rule.

## References and appendices

`references` accepts finished strings or objects with `text` or `runs`.
Entries receive a hanging indent. Spans allow a journal/work title to be
italicized and a DOI to be a real external hyperlink; preserve the supplied
bibliographic facts. Example syntax:

```json
{"runs": [
  {"text": "Author, A. (2026). "},
  {"text": "Work title", "italic": true},
  {"text": ". Publisher. "},
  {"text": "https://doi.org/verified-doi", "url": "https://doi.org/verified-doi"}
]}
```

This is a structural placeholder, not a valid citation. Replace it with a
verified source entry. The builder does not sort entries, fetch research,
resolve DOI metadata or certify APA 7 correctness.

Each appendix has `id`, `title`, `return_to` and `blocks`. The index links
every individual section. Each appendix has explicit return links to its
relevant body anchor and to the index. Sections flow continuously; no implicit
page break is inserted for each appendix. Keep only exhibits with a useful
evidence or implementation job.

## Page counts and verification

The builder writes a `.build.json` manifest with selected formatting, image
sizes and link counts. This records production, not a visual pass.

The audit checks ZIP integrity, bookmark uniqueness, resolved internal links,
comments/tracked-change presence, page dimensions, selected style settings,
PDF link destinations, requested font family identification, horizontal text
bounds and collapsed table-grid rules at the page edge. It does not prove
that rows make a valid argument, that source figures are correct, or that all
text remains readable at its placed size.

With a project JSON and references beginning on a new page, the audit counts
the essay from its title page to the page before the reference heading.
`limits.max_body_pages` enforces the specified limit. For unusual layouts,
provide explicit `audit.body_start_text`, `audit.body_end_before_text` and
`audit.end_starts_new_page` values. Marker text must be unambiguous in the PDF.
If a cover repeats the title or a running header repeats the marker, choose
a distinct body-start phrase. Ambiguity is reported as unverified, not passed.

If there is no reference or appendix boundary, the audit counts from a unique
start marker to the end of the document. If references/appendices share the
last essay page, set `end_starts_new_page` to false so that page remains counted.
Do not silently exclude a partly shared page to satisfy a limit.

After rendering, inspect **every final page** at readable scale. Check actual
font appearance, paragraph rhythm, image labels, source notes, margins,
awkward page breaks and every moved exhibit. Fix the content/layout and
render again. Never raise a score merely to clear a threshold. The output
status `automated_checks_passed_visual_review_required` is deliberately not a
submission-ready label.

## Private comment extraction

```bash
python skills/write-innovation-essays/scripts/extract_comments.py \
  review.docx --output output/comments.json
```

This read-only tool records each original comment ID, exact comment text,
selected range text, nearby paragraph, author/date when present and any modern
comment metadata parts. Ranges crossing paragraphs keep a newline. Point-only
comments are distinguished from ranges; absent anchors remain absent. The
source file SHA-256 is included, and the source bytes are checked unchanged.

The output is private review material. Do not put reviewer identities, raw
comment text or process notes in the submission unless requested. Create an
action/closure ledger and verify each requested repair against the actual
revised output. Existing comments are not automatically accepted or deleted
by this extraction tool.

## Example and limitations

`examples/short-demo.json` demonstrates English and Indonesian paragraphs,
explicit and automatic internal links, native tables, numerical alignment,
source/assumption notes and two linked appendices. Its numerical data are
constructed and clearly identified. It is a formatting demonstration rather
than a reusable argument or a claimed successful pilot.

`examples/short-demo.docx` and `examples/short-demo.pdf` are the generated
two-page example. Its main essay occupies one page; the source note and
continuous linked appendices occupy the second. `examples/figure-demo.json`
is an additional runnable placement example referencing the chart gallery's
cash preview. It can be built with the same command by changing the input
filename and output path.

The neutral template and short example were actually produced and rendered
in the package build. The generic builder does not supply research, financial
projections, a media-sanitization service, a live prototype deployment or a
guaranteed page count in every Word/PDF environment. Fonts and renderer
differences can change pagination; inspect the actual final export.
