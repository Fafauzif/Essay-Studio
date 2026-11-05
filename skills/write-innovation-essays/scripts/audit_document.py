#!/usr/bin/env python3
"""Check DOCX structure and optional PDF. Visual inspection remains required.

python audit_document.py essay.docx --pdf render/essay.pdf --project project.json --output audit.json
Exit 1 means at least one automated error; warnings do not certify compliance.
"""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
from lxml import etree as ET
from docx import Document
import fitz
NS={"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
def parse(raw):return ET.fromstring(raw,parser=ET.XMLParser(resolve_entities=False,no_network=True,load_dtd=False))

def norm(s):return re.sub(r"\s+"," ",s).strip()
def audit(path,pdf=None,project=None):
    path=Path(path);errors=[];warnings=[];data=path.read_bytes()
    result={"docx":str(path),"docx_sha256":hashlib.sha256(data).hexdigest(),"errors":errors,"warnings":warnings,"visual_review":"not_performed_by_script"}
    with zipfile.ZipFile(path)as z:
        bad=z.testzip()
        if bad:errors.append("Corrupt ZIP member: "+bad)
        root=parse(z.read("word/document.xml"));names=root.xpath("//w:bookmarkStart/@w:name",namespaces=NS);links=root.xpath("//w:hyperlink/@w:anchor",namespaces=NS)
        missing=sorted(set(links)-set(names));result.update(bookmarks=len(names),internal_links=len(links),unresolved_links=missing,table_count=len(root.findall(".//w:tbl",NS)))
        if missing:errors.append("Unresolved internal hyperlinks: "+", ".join(missing))
        if len(names)!=len(set(names)):errors.append("Duplicate bookmark names")
        ncomments=len(parse(z.read("word/comments.xml")).findall("w:comment",NS))if"word/comments.xml"in z.namelist()else 0
        tracked=len(root.findall(".//w:ins",NS))+len(root.findall(".//w:del",NS));result.update(comments=ncomments,tracked_changes=tracked)
        if ncomments:warnings.append(f"Document retains {ncomments} comments; review whether the requested output is an annotated or clean version.")
        if tracked:warnings.append(f"Document retains {tracked} tracked-change elements.")
    d=Document(path);result["sections"]=[{"page_width_cm":round(s.page_width/360000,3),"page_height_cm":round(s.page_height/360000,3),"margins_cm":{k:round(getattr(s,k+"_margin")/360000,3)for k in ["top","bottom","left","right"]}}for s in d.sections]
    normal=d.styles["Normal"];result["normal_style"]={"font":normal.font.name,"size_pt":normal.font.size.pt if normal.font.size else None,"line_spacing":normal.paragraph_format.line_spacing,"after_pt":normal.paragraph_format.space_after.pt if normal.paragraph_format.space_after else 0}
    config={};source={}
    if project:source=json.loads(Path(project).read_text(encoding="utf-8"));config=source.get("format",{})
    qr_expected=set()
    for b in source.get("body",[])+[b for s in source.get("appendices",[])for b in s.get("blocks",[])]:
        if b.get("type")=="qr":qr_expected.add(b["url"])
    if qr_expected:
        try:
            import cv2
            import numpy as np
            decoded=set()
            with zipfile.ZipFile(path)as z:
                for name in z.namelist():
                    if name.startswith("word/media/")and name.lower().endswith((".png",".jpg",".jpeg")):
                        im=cv2.imdecode(np.frombuffer(z.read(name),dtype=np.uint8),cv2.IMREAD_COLOR)
                        if im is not None:
                            value,_,_=cv2.QRCodeDetector().detectAndDecode(im)
                            if value:decoded.add(value)
            result["qr"]={"expected":sorted(qr_expected),"decoded":sorted(decoded),"live_access":"not_checked"}
            if qr_expected-decoded:errors.append("Embedded QR payload could not be verified: "+", ".join(sorted(qr_expected-decoded)))
        except ImportError:
            warnings.append("QR payload not decoded: optional OpenCV and NumPy are unavailable; verify it independently")
    for key,actual in [("font",normal.font.name),("body_pt",result["normal_style"]["size_pt"]),("line_spacing",result["normal_style"]["line_spacing"])]:
        if key in config and config[key]!=actual:errors.append(f"Normal style {key}: expected {config[key]!r}, got {actual!r}")
    if pdf:
        pdf=Path(pdf);p=fitz.open(pdf);result["pdf"]={"path":str(pdf),"sha256":hashlib.sha256(pdf.read_bytes()).hexdigest(),"page_count":len(p),"internal_links":0,"fonts":[],"collapsed_grid_segments":0};fonts=set();grid_color=config.get("table_border","D9D9D9");rgb=tuple(int(grid_color[i:i+2],16)/255 for i in [0,2,4]);texts=[]
        for i,pg in enumerate(p):
            text=pg.get_text();texts.append(text)
            for l in pg.get_links():
                if l["kind"]==fitz.LINK_GOTO:
                    result["pdf"]["internal_links"]+=1
                    if not 0<=l["page"]<len(p):errors.append(f"PDF page {i+1} internal link outside document")
            for block in pg.get_text("dict")["blocks"]:
                if block["type"]!=0:continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        fonts.add(span["font"])
                        if span["text"].strip()and(span["bbox"][0]<-1 or span["bbox"][2]>pg.rect.width+1):errors.append(f"PDF page {i+1} text outside horizontal page bounds")
            for drawing in pg.get_drawings():
                color=drawing.get("color");r=drawing["rect"]
                if color and len(color)==3 and all(abs(a-b)<.002 for a,b in zip(color,rgb))and r.x0<=.01 and r.x1<=.01:result["pdf"]["collapsed_grid_segments"]+=1
        result["pdf"]["fonts"]=sorted(fonts)
        if result["pdf"]["collapsed_grid_segments"]:errors.append("PDF table grid collapsed to page edge; re-export in a fresh isolated profile and re-inspect")
        fm=source.get("audit",{})
        start=fm.get("body_start_text",source.get("title"));end=fm.get("body_end_before_text")
        refs=bool(source.get("references"))
        if not end and refs:end=config.get("references_heading","Daftar Pustaka")
        if start:
            starts=[i+1 for i,t in enumerate(texts)if norm(start)in norm(t)]
            ends=[i+1 for i,t in enumerate(texts)if any(norm(end)==norm(line)for line in t.splitlines())]if end else[]
            if len(starts)==1 and(not end or len(ends)==1):
                stop=(ends[0]-1 if fm.get("end_starts_new_page",refs and config.get("references_new_page",True))else ends[0])if ends else len(p)
                count=stop-starts[0]+1;result["pdf"]["body_pages"]={"first":starts[0],"last":stop,"count":count,"method":"explicit text markers"}
                limit=source.get("limits",{}).get("max_body_pages")
                if limit is not None and count>limit:errors.append(f"Body has {count} pages, exceeds limit {limit}")
            else:warnings.append("Body page markers absent or ambiguous; main-page count not verified")
        else:warnings.append("No project/body marker supplied; main-page count not verified")
        expected=config.get("font")
        if expected:
            plain=lambda x:re.sub(r"[^a-z]","",x.lower())
            if not any(plain(expected)in plain(f)for f in fonts):warnings.append(f"Expected font {expected!r} not identified in PDF fonts; verify substitution before delivery.")
    else:warnings.append("No PDF supplied; render, body-page count and font appearance not verified")
    result["status"]="automated_checks_failed"if errors else"automated_checks_passed_visual_review_required"
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("docx",type=Path);p.add_argument("--pdf",type=Path);p.add_argument("--project",type=Path);p.add_argument("--output",required=True,type=Path);a=p.parse_args();r=audit(a.docx,a.pdf,a.project)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2), encoding="utf-8");print(json.dumps({"status":r["status"],"errors":r["errors"],"warnings":r["warnings"]}));raise SystemExit(1 if r["errors"]else 0)

if __name__=="__main__":main()
