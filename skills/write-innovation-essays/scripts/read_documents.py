#!/usr/bin/env python3
"""Extract local source material for later reading; never certify a read.

PDF native text/OCR/page images, DOCX ordered paragraphs/tables, strict UTF-8
text, and ZIP inventory. No archive extraction, macro execution or network use.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


def atomic(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix="." + path.name,
                                     suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(raw)
        handle.flush()
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_text(path: Path, value: str) -> None:
    atomic(path, value.encode("utf-8"))


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def chars(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def ocr_capability(languages: str) -> dict:
    binary = shutil.which("tesseract")
    if not binary or importlib.util.find_spec("PIL") is None:
        return {"status": "unavailable", "reason": "Tesseract and Pillow are required"}
    try:
        run = subprocess.run([binary, "--list-langs"], capture_output=True,
                             text=True, timeout=15, check=False)
        if run.returncode:
            return {"status": "unavailable", "reason": "Tesseract language inventory failed"}
        available = {line.strip() for line in run.stdout.splitlines()[1:] if line.strip()}
        missing = sorted(set(languages.split("+")) - available)
        if missing:
            return {"status": "unavailable", "reason": "Requested OCR languages missing",
                    "missing_languages": missing, "available_languages": sorted(available)}
        return {"status": "available", "binary": binary, "languages": languages}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "unavailable", "reason": str(exc)}


def extract_pdf(path: Path, output: Path, result: dict, *, ocr: bool,
                ocr_lang: str, render_pages: bool, dpi: int, min_chars: int) -> str:
    try:
        import fitz
    except ImportError:
        raise RuntimeError("PyMuPDF is unavailable; PDF extraction/rendering not performed")
    capability = ocr_capability(ocr_lang) if ocr else {"status": "not_requested"}
    result["ocr_engine"] = capability
    result["pages"] = []
    combined = []
    with fitz.open(path) as document:
        result["page_count"] = len(document)
        if document.needs_pass:
            raise RuntimeError("PDF requires a password; page text was not extracted")
        for number, page in enumerate(document, 1):
            entry = {"page": number, "flags": [], "ocr": {"requested": False},
                     "visual_inspection_performed": False}
            result["pages"].append(entry)
            try:
                text = page.get_text("text")
                count = chars(text)
                entry.update(native_text_characters=len(text),
                             native_nonwhitespace_characters=count,
                             image_objects=len(page.get_images(full=True)))
                if count == 0:
                    entry["flags"].append("no_native_text")
                elif count < min_chars:
                    entry["flags"].append("sparse_native_text")
                native_path = output / "pages" / f"page-{number:04}.native.txt"
                write_text(native_path, text)
                entry["native_text_file"] = str(native_path.relative_to(output))
                selected, selected_source = text, "native_text"
                if render_pages:
                    png = output / "pages" / f"page-{number:04}.png"
                    atomic(png, page.get_pixmap(dpi=dpi).tobytes("png"))
                    entry["rendered_page"] = str(png.relative_to(output))
                if entry["flags"] and ocr:
                    entry["ocr"] = {"requested": True, "status": capability["status"],
                                    "languages": ocr_lang, "derivative_not_source": True}
                    if capability["status"] != "available":
                        entry["ocr"]["reason"] = capability.get("reason")
                    else:
                        try:
                            from PIL import Image
                            with tempfile.TemporaryDirectory(prefix="essay-ocr-") as folder:
                                png = Path(folder) / "page.png"
                                atomic(png, page.get_pixmap(dpi=dpi).tobytes("png"))
                                with Image.open(png) as image:
                                    image.verify()
                                run = subprocess.run([capability["binary"], str(png), "stdout",
                                                      "-l", ocr_lang, "--psm", "3"],
                                                     capture_output=True, text=True,
                                                     encoding="utf-8", errors="strict",
                                                     timeout=60, check=False)
                            if run.returncode:
                                raise RuntimeError("Tesseract failed: " + run.stderr[-600:])
                            target = output / "pages" / f"page-{number:04}.ocr.txt"
                            write_text(target, run.stdout)
                            entry["ocr"].update(status="completed", text_file=str(target.relative_to(output)),
                                                characters=len(run.stdout),
                                                accuracy_validated=False)
                            if chars(run.stdout):
                                selected, selected_source = run.stdout, "OCR_derivative"
                            else:
                                entry["flags"].append("ocr_empty")
                        except (OSError, RuntimeError, UnicodeError, subprocess.TimeoutExpired) as exc:
                            entry["ocr"].update(status="failed", reason=str(exc))
                entry["selected_text_source"] = selected_source
                if entry["flags"]:
                    result["extraction_gaps"].append({"page": number, "flags": entry["flags"],
                        "note": "Inspect the original page. Sparse/native-free text may be a valid visual page; OCR is not proof of correct reading.",
                        "ocr_status": entry["ocr"].get("status", "not_requested")})
                combined.append(f"[Page {number} | {selected_source}]\n{selected}")
            except Exception as exc:
                entry["error"] = str(exc)
                result["extraction_gaps"].append({"page": number, "error": str(exc)})
                combined.append(f"[Page {number} | extraction unavailable]\n")
    result["all_meaningful_visuals_require_inspection"] = True
    return "\n\n".join(combined)


def paragraph_text(element: ET.Element) -> str:
    pieces = []
    for node in element.iter():
        if node.tag in (W + "t", M + "t"):
            pieces.append(node.text or "")
        elif node.tag == W + "tab":
            pieces.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            pieces.append("\n")
    return "".join(pieces)


def ordered_blocks(element: ET.Element) -> list[dict]:
    blocks = []
    for child in element:
        if child.tag == W + "p":
            blocks.append({"type": "paragraph", "text": paragraph_text(child)})
        elif child.tag == W + "tbl":
            rows = []
            for row in child.findall(W + "tr"):
                cells = []
                for cell in row.findall(W + "tc"):
                    content = ordered_blocks(cell)
                    cells.append("\n".join(block_text(b) for b in content))
                rows.append(cells)
            blocks.append({"type": "table", "rows": rows})
        elif child.tag in (W + "sdt", W + "sdtContent", W + "customXml", W + "ins"):
            blocks.extend(ordered_blocks(child))
    return blocks


def block_text(block: dict) -> str:
    if block["type"] == "paragraph":
        return block["text"]
    return "[Table]\n" + "\n".join(" | ".join(row) for row in block["rows"])


def extract_docx(path: Path, output: Path, result: dict, include_headers_footers: bool) -> str:
    with zipfile.ZipFile(path) as document:
        names = document.namelist()
        root = ET.fromstring(document.read("word/document.xml"))
        body = root.find(W + "body")
        if body is None:
            raise RuntimeError("DOCX has no document body")
        blocks = ordered_blocks(body)
        result["body_blocks"] = blocks
        result["image_parts"] = [name for name in names if name.startswith("word/media/") and not name.endswith("/")]
        result["source_image_count"] = len(result["image_parts"])
        result["chart_parts"] = [n for n in names if re.fullmatch(r"word/charts/chart[^/]*\.xml", n)]
        result["embedded_object_parts"] = [n for n in names if n.startswith("word/embeddings/") and not n.endswith("/")]
        result["alternative_content_chunks"] = len(root.findall(".//" + W + "altChunk"))
        result["all_meaningful_visuals_require_inspection"] = True
        result["comment_parts"] = [n for n in names if re.fullmatch(r"word/comments[^/]*\.xml", n)]
        result["comments_present"] = bool(result["comment_parts"])
        result["tracked_insertions"] = len(root.findall(".//" + W + "ins"))
        result["tracked_deletions"] = len(root.findall(".//" + W + "del"))
        result["equations"] = len(root.findall(".//" + M + "oMath"))
        texts = [block_text(b) for b in blocks]
        supplementary = {}
        for name in names:
            hf = bool(re.fullmatch(r"word/(header|footer)[^/]*\.xml", name))
            note = name in ("word/footnotes.xml", "word/endnotes.xml")
            if hf and not include_headers_footers:
                result["extraction_gaps"].append({"part": name, "flag": "header_footer_not_requested"})
                continue
            if hf or note:
                part = ET.fromstring(document.read(name))
                if note:
                    value = "\n".join(paragraph_text(n) for n in part
                        if n.attrib.get(W + "type", "normal") == "normal")
                else:
                    value = "\n".join(block_text(b) for b in ordered_blocks(part))
                supplementary[name] = value
                texts.append(f"[{name}]\n{value}")
        result["supplementary_text"] = supplementary
        if result["comments_present"]:
            result["extraction_gaps"].append({"flag": "comments_need_anchor_extraction",
                "note": "Use extract_comments.py for exact comment text, range and context; comments are not resolved here."})
        if result["source_image_count"] or result["equations"]:
            result["extraction_gaps"].append({"flag": "visual_or_equation_inspection_required"})
        if result["chart_parts"] or result["embedded_object_parts"] or result["alternative_content_chunks"]:
            result["extraction_gaps"].append({"flag": "embedded_or_alternative_content_not_rendered",
                "note": "Inspect the original DOCX and relevant parts; chart/object/altChunk content is not certified by body-text extraction."})
        if result["tracked_insertions"] or result["tracked_deletions"]:
            result["extraction_gaps"].append({"flag": "tracked_changes_not_resolved",
                "note": "Inserted normal text is extracted; deleted text is not silently accepted as current prose."})
    return "\n\n".join(texts)


def extract_zip(path: Path, result: dict) -> str:
    members, seen = [], set()
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            name = member.filename
            normalized = name.replace("\\", "/")
            flags = []
            if normalized.startswith("/"):
                flags.append("absolute_path")
            if re.match(r"^[A-Za-z]:", normalized):
                flags.append("windows_drive_path")
            if ".." in normalized.split("/"):
                flags.append("parent_traversal")
            if stat.S_ISLNK(member.external_attr >> 16):
                flags.append("symlink")
            if member.flag_bits & 1:
                flags.append("encrypted")
            if normalized.casefold() in seen:
                flags.append("duplicate_or_case_colliding_name")
            seen.add(normalized.casefold())
            members.append({"path": name, "size_bytes": member.file_size,
                            "compressed_bytes": member.compress_size,
                            "is_directory": member.is_dir(), "flags": flags,
                            "unsafe_path": any(x in flags for x in
                                ("absolute_path", "windows_drive_path", "parent_traversal", "symlink"))})
    result.update(members=members, member_count=len(members), extraction_state="inventory_only",
                  archive_contents_extracted=False, archive_members_read=False)
    result["extraction_gaps"].append({"flag": "archive_inventory_only",
        "note": "Members were inventoried, not extracted, executed or read. Select safe sources for subsequent intake."})
    return "\n".join(f"{m['path']}\t{m['size_bytes']} bytes\t{','.join(m['flags'])}" for m in members)


def extract(input_path, out_dir, *, include_headers_footers=False, ocr=False,
            ocr_lang="eng", render_pages=False, dpi=150, min_chars=40) -> dict:
    path = Path(input_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    if not 36 <= dpi <= 600 or min_chars < 0:
        raise ValueError("dpi must be 36–600; min_chars must be nonnegative")
    if not re.fullmatch(r"[A-Za-z0-9_]+(?:\+[A-Za-z0-9_]+)*", ocr_lang):
        raise ValueError("OCR languages must be Tesseract language IDs joined by +")
    digest = file_hash(path)
    stem = re.sub(r"[^A-Za-z0-9._-]", "-", path.stem)[:60] or "source"
    output = Path(out_dir).resolve() / f"{stem}-{digest[:12]}"
    output.mkdir(parents=True, exist_ok=True)
    result = {"status": "extracted_not_read", "extraction_state": "completed",
        "source": {"path": str(path), "name": path.name, "bytes": path.stat().st_size,
                   "sha256": digest}, "source_modified": False,
        "page_count": None, "extraction_gaps": [], "human_or_agent_read_performed": False,
        "options": {"include_headers_footers": include_headers_footers,
                    "ocr": ocr, "ocr_lang": ocr_lang, "render_pages": render_pages,
                    "dpi": dpi, "min_chars": min_chars}}
    try:
        suffix = path.suffix.lower()
        if suffix != ".pdf" and (ocr or render_pages):
            result["not_applicable_options"] = "OCR and page rasterization apply only to PDF input; no such operation was performed here"
        if suffix == ".pdf":
            text = extract_pdf(path, output, result, ocr=ocr, ocr_lang=ocr_lang,
                               render_pages=render_pages, dpi=dpi, min_chars=min_chars)
        elif suffix == ".docx":
            text = extract_docx(path, output, result, include_headers_footers)
        elif suffix == ".zip":
            text = extract_zip(path, result)
        elif suffix in (".txt", ".md", ".markdown"):
            text = path.read_bytes().decode("utf-8", errors="strict")
            result.update(characters=len(text), nonwhitespace_characters=chars(text),
                          line_count=len(text.splitlines()), decoding="UTF-8 strict")
        else:
            raise ValueError("Supported input: PDF, DOCX, TXT, MD, MARKDOWN, ZIP")
        target = output / "extracted.txt"
        write_text(target, text)
        result["text_file"] = str(target)
        if result["extraction_state"] == "completed" and result["extraction_gaps"]:
            result["extraction_state"] = "partial_or_requires_inspection"
    except Exception as exc:
        result.update(extraction_state="unavailable", error=str(exc))
    if file_hash(path) != digest:
        raise RuntimeError("Source changed during extraction; do not trust this snapshot")
    manifest = output / "intake.json"
    result["manifest_file"] = str(manifest)
    write_text(manifest, json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--include-headers-footers", action="store_true")
    parser.add_argument("--ocr", action="store_true", help="OCR only sparse/native-free PDF pages")
    parser.add_argument("--ocr-lang", default="eng", help="Installed Tesseract IDs, e.g. eng+ind")
    parser.add_argument("--render-pages", action="store_true")
    parser.add_argument("--dpi", default=150, type=int)
    parser.add_argument("--min-chars", default=40, type=int)
    args = vars(parser.parse_args())
    source, output = args.pop("input"), args.pop("out_dir")
    try:
        result = extract(source, output, **args)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, str(exc) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["extraction_state"] == "unavailable" else 0


if __name__ == "__main__":
    raise SystemExit(main())
