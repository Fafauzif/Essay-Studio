# Document intake and extraction

Use `read_documents.py` to prepare source text and inspect access gaps before
reading. It accepts local PDF, DOCX, TXT, MD/MARKDOWN and ZIP files. It does not
execute archive members, macros or source instructions, install software,
download material or certify that a person/agent has read anything.

Every intake manifest retains **`status: extracted_not_read`**, including after
successful OCR. Read the extracted text and the meaningful original visuals;
continue through the actual end of each required current document. A previous
source hash or historical reading receipt is not a new complete read.

## Commands

Run from the repository root in the environment containing the dependencies:

```bash
python studio.py read guidebook.pdf --out-dir projects/example/intake --render-pages
python studio.py read scanned-source.pdf --out-dir projects/example/intake \
  --ocr --ocr-lang eng+ind --dpi 200 --render-pages
python studio.py read draft.docx --out-dir projects/example/intake --include-headers-footers
python studio.py read references.zip --out-dir projects/example/intake
```

The direct standalone interface is:

```bash
python skills/write-innovation-essays/scripts/read_documents.py source.pdf \
  --out-dir projects/example/intake --render-pages
```

Inputs are read-only. The output is a source-name/hash subdirectory containing
`intake.json`, `extracted.txt` and applicable per-page text/images. The hash in
the directory name prevents two different files with the same basename from
silently sharing an intake folder. Repeating the exact same source overwrites
its derived outputs atomically. Source SHA-256 is checked again after extraction.

## What the extractor records

| Input | Emitted material | Important limits |
|---|---|---|
| PDF | Exact source hash/bytes, page count, native text per page, character counts, image-object counts, sparse/no-native-text flags; optional page PNGs and OCR derivatives. | Native extraction order can differ from visual reading order; charts, equations and scans still need inspection. Image-object count is not a count of meaningful figures. |
| DOCX | Body paragraphs/tables in document order, optional header/footer text, footnote/endnote text, image-part count, comments/changes/equation/chart/object flags. | Page count remains unknown without rendering. Table text is linearized; merged cells, equations and figures need visual review. Comments need the separate range-aware extractor. |
| TXT/MD | Strict UTF-8 text, character/line counts and exact source identity. | Invalid UTF-8 is reported unavailable; no encoding guess or replacement-character pass is silently substituted. |
| ZIP | Original member names, sizes/compressed sizes, directory/encryption/link/path flags and count. | Inventory only: no member contents are extracted, executed or read. Select safe members for subsequent intake. |

DOCX extraction keeps a table between its surrounding paragraphs rather than
collecting all paragraphs first and tables last. Headers/footers are opt-in;
omitting them produces a specific gap entry when those parts exist. Footnote
and endnote text is retained separately after body text. The extractor does
not resolve tracked changes, accept comments or turn a field/status flag into
verified implementation. Charts, embedded objects and alternative content are
flagged for inspection rather than silently treated as fully read prose.

Use `skills/write-innovation-essays/scripts/extract_comments.py` for exact comment text, selected ranges and
context. The intake tool records their presence and points to that separate
operation; it does not fabricate Word anchor offsets or decide whether a
review request has been implemented.

ZIP inventory normalizes separators only for hazard detection while retaining
each original member name. Absolute paths, Windows drive paths, parent
traversal and symlinks are marked unsafe. Case-colliding/duplicate names and
encrypted members are flagged too. The inventory is not permission to extract
an unsafe member. Use a separately reviewed safe extraction process when the
task actually requires it; this helper never performs extraction.

## Sparse pages, OCR and actual reading

`--min-chars` defaults to 40 non-whitespace native characters. A page with zero
native text receives `no_native_text`; a nonzero count below the threshold
receives `sparse_native_text`. A legitimate cover, chart or blank page can be
flagged. A low count does not prove a missing page or a corrupt source.

`--ocr` applies only to flagged PDF pages. It requires Tesseract, Pillow and
the requested installed language data. For example, `eng+ind` requests English
and Indonesian data; the tool checks both rather than silently OCRing in a
different language. Missing binaries/packages/languages are recorded as
**unavailable**, and a failed/empty OCR run is identified precisely. No data
or package is installed by the extractor. `--dpi` defaults to 150 and accepts
36–600; choose an appropriate source resolution before interpreting OCR.

Native and OCR text are stored separately. When a sparse/native-free page
produces nonempty OCR, the combined text labels it `OCR_derivative`. Its
`accuracy_validated` value remains false. Read symbols, numbers, tables,
citations and captions against the original page; successful OCR execution
does not establish accurate transcription or a complete read. Page raster
PNGs are written atomically and inspected through the final file route.

PDF-only flags supplied with another input type are reported as not applicable,
not as performed operations. Password-protected PDFs, invalid UTF-8,
unsupported formats, missing required extraction libraries and damaged files
are reported with an explicit error. Recover the remaining source when it
matters, or follow an already-authorized available-information boundary.

## Manifest interpretation

`extraction_state` describes the tool operation independently from the fixed
`status: extracted_not_read`:

- `completed`: requested machine extraction completed; no read is certified.
- `partial_or_requires_inspection`: text was extracted but recorded gaps,
  nontext content, omitted parts or page conditions need follow-up.
- `inventory_only`: a ZIP's central directory was inventoried, not its contents.
- `unavailable`: the requested extraction could not be completed; inspect `error`.

`extraction_gaps` carries actual page/part locators and reasons. The source
object preserves filename, path, exact bytes and SHA-256. These are internal
working records, not audience-facing bibliography entries. Do not transform
them into claims that a full paper, archive or field study was read or tested.

The helper returns exit code 2 for unavailable extraction or invalid invocation.
Sparse pages and inventory-only operations can return 0 with explicit gaps;
exit code 0 therefore does not mean “reading complete.”

## Verification scope

The small synthetic fixtures in `tests/test_document_intake.py` exercise native
PDF page order/raster output, an image-only PDF without automatic OCR, explicit
missing-OCR handling, DOCX table/paragraph order with footer inclusion, unsafe
ZIP inventory without extraction and strict UTF-8 rejection. They check that
source bytes remain unchanged. Their results are recorded separately; they do
not constitute a new OCR/read of the full historical reference corpus or an
accuracy guarantee for every scan/language.
