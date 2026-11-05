#!/usr/bin/env python3
"""Render DOCX to PDF and atomic PNGs using an isolated LibreOffice profile.

python render_document.py essay.docx --out-dir render --dpi 144
Exit 2 means conversion is unavailable/failed. A report never implies visual QA.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import fitz

def atomic(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"wb")as f:f.write(raw)
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def render(source,out,dpi=144,timeout=120,executable=None):
    source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    if not source.is_file():raise FileNotFoundError(source)
    report={"input":str(source),"input_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"status":"not_rendered","visual_review":"not_performed_by_script","dpi":dpi}
    command=executable or shutil.which("libreoffice")or shutil.which("soffice")
    if source.suffix.lower()==".pdf":pdfraw=source.read_bytes()
    else:
        if not command:
            report.update(status="unavailable",reason="LibreOffice/soffice not found. Install it or export DOCX manually, then run this tool on the PDF.")
            atomic(out/"render-report.json",json.dumps(report,indent=2).encode());return report
        with tempfile.TemporaryDirectory(prefix="essay-render-")as temp:
            temp=Path(temp);profile=temp/"profile";conversion=temp/"pdf";conversion.mkdir()
            cmd=[command,"-env:UserInstallation="+profile.as_uri(),"--headless","--convert-to","pdf:writer_pdf_Export","--outdir",str(conversion),str(source)]
            env=os.environ.copy();env["SAL_USE_VCLPLUGIN"]="gen"
            started=time.monotonic()
            try:r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,env=env)
            except (OSError,subprocess.TimeoutExpired)as e:
                report.update(status="failed",reason=str(e));atomic(out/"render-report.json",json.dumps(report,indent=2).encode());return report
            report.update(converter=Path(command).name,returncode=r.returncode,stdout=r.stdout.strip(),stderr=r.stderr.strip(),seconds=round(time.monotonic()-started,2))
            pdf=conversion/(source.stem+".pdf")
            if not pdf.is_file()or pdf.stat().st_size==0:
                report.update(status="failed",reason="Converter did not produce a nonempty PDF");atomic(out/"render-report.json",json.dumps(report,indent=2).encode());return report
            pdfraw=pdf.read_bytes()
    output=out/(source.stem+".pdf");atomic(output,pdfraw)
    pages=[]
    with fitz.open(stream=pdfraw,filetype="pdf")as doc:
        for i,page in enumerate(doc):
            path=out/f"page-{i+1:03d}.png";raw=page.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False).tobytes("png");atomic(path,raw)
            pages.append({"page":i+1,"image":path.name,"width_pt":round(page.rect.width,2),"height_pt":round(page.rect.height,2),"words":len(page.get_text().split())})
    for old in out.glob("page-*.png"):
        if old.name not in {p["image"]for p in pages}:old.unlink()
    report.update(status="rendered_requires_visual_inspection",pdf=str(output),pdf_sha256=hashlib.sha256(pdfraw).hexdigest(),page_count=len(pages),pages=pages)
    atomic(out/"render-report.json",json.dumps(report,ensure_ascii=False,indent=2).encode());return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("source",type=Path);p.add_argument("--out-dir",required=True,type=Path);p.add_argument("--dpi",type=int,default=144);p.add_argument("--timeout",type=int,default=120);p.add_argument("--libreoffice")
    a=p.parse_args()
    if not 72<=a.dpi<=600:p.error("--dpi must be 72..600")
    r=render(a.source,a.out_dir,a.dpi,a.timeout,a.libreoffice);print(json.dumps({k:r[k]for k in ["status","page_count","pdf","reason"]if k in r}))
    raise SystemExit(0 if r["status"]=="rendered_requires_visual_inspection"else 2)

if __name__=="__main__":main()
