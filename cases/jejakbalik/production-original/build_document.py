from pathlib import Path
import json,re,copy,math,io,os,zipfile
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PIL import Image
P=Path(__file__).resolve().parent; OUT=P/'output';OUT.mkdir(exist_ok=True)
A=P/'assets'; F=A/'figures'; S=A/'screenshots'
main=json.loads((P/'main.json').read_text()); finance=json.loads((P/'finance.json').read_text());ft=json.loads((P/'finance_tables.json').read_text())
refpath=P/'evidence.json'
evidence=json.loads(refpath.read_text()) if refpath.exists() else {}
source=next((P.parent/'upload').glob('David*.docx'))
doc=Document(source)
body=doc._element.body
for e in list(body):
 if e.tag!=qn('w:sectPr'):body.remove(e)
# Remove inherited unused media and links after clearing template content.
for rid,rel in list(doc.part.rels.items()):
 if rel.reltype.endswith('/image') or rel.reltype.endswith('/hyperlink') or rel.reltype.endswith('/customXml'): doc.part.drop_rel(rid)
sec=doc.sections[0];sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Cm(2.5)
sec.header_distance=Cm(.7);sec.footer_distance=Cm(1)
for st in doc.styles:
 if st.type==1:
  st.font.name='Times New Roman';st.font.size=Pt(12);st.font.color.rgb=RGBColor(0,0,0)
  st.paragraph_format.space_before=Pt(0);st.paragraph_format.space_after=Pt(4);st.paragraph_format.line_spacing=1.5
  for el in list(st.element.xpath('./w:pPr/w:pBdr')):el.getparent().remove(el)
for name in ['normal']:
 st=doc.styles[name];st.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
for name in ['Heading 1','Heading 2','Heading 3']:
 st=doc.styles[name];st.font.bold=True;st.font.size=Pt(12);st.paragraph_format.space_before=Pt(8);st.paragraph_format.space_after=Pt(4);st.paragraph_format.keep_with_next=True
st=doc.styles['Title'];st.font.size=Pt(16);st.font.bold=True;st.paragraph_format.line_spacing=1.1;st.paragraph_format.space_after=Pt(10)
for hf in [sec.header,sec.footer]:
 for el in list(hf._element): hf._element.remove(el)
# The official original logos are inserted without altering their identity.
hp=sec.header.add_paragraph();hp.paragraph_format.line_spacing=1;hp.paragraph_format.space_after=Pt(0)
logos=[A/'logos'/'dlh-bemui-black.png',A/'logos'/'lintasarta-black.png']
if all(p.exists() for p in logos):
 t=sec.header.add_table(rows=1,cols=2,width=Cm(16));t.autofit=False;t.columns[0].width=Cm(8);t.columns[1].width=Cm(8)
 for i,path in enumerate(logos):
  cell=t.cell(0,i);p=cell.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.LEFT if i==0 else WD_ALIGN_PARAGRAPH.RIGHT;p.paragraph_format.line_spacing=1
  p.add_run().add_picture(str(path),height=Cm(.65))
else:
 hp.add_run('Departemen Lingkungan Hidup BEM UI 2026').font.size=Pt(9);hp.add_run('\tLintasarta').font.size=Pt(9)
fp=sec.footer.add_paragraph();fp.alignment=WD_ALIGN_PARAGRAPH.CENTER;fp.paragraph_format.line_spacing=1
r=fp.add_run();fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');r._r.addnext(fld)
sec.different_first_page_header_footer=True
# Clean inherited first-page header/footer.
for hf in [sec.first_page_header,sec.first_page_footer]:
 for el in list(hf._element):hf._element.remove(el)
bookmark_id=10; targets=set();links=[];figcounter=0;pending_break=False

def add_p(*args,**kwargs):
 global pending_break
 p=doc.add_paragraph(*args,**kwargs)
 if pending_break:p.paragraph_format.page_break_before=True;pending_break=False
 return p

def anchor(p,key):
 global bookmark_id
 key='a_'+key.replace('.','_').replace('-','_');targets.add(key);bookmark_id+=1
 s=OxmlElement('w:bookmarkStart');s.set(qn('w:id'),str(bookmark_id));s.set(qn('w:name'),key)
 e=OxmlElement('w:bookmarkEnd');e.set(qn('w:id'),str(bookmark_id));p._p.insert(0,s);p._p.append(e)

def linkrun(p,text,key,size=12,bold=False):
 key='a_'+key.replace('.','_').replace('-','_');links.append(key)
 h=OxmlElement('w:hyperlink');h.set(qn('w:anchor'),key)
 r=OxmlElement('w:r');pr=OxmlElement('w:rPr');fonts=OxmlElement('w:rFonts');fonts.set(qn('w:ascii'),'Times New Roman');fonts.set(qn('w:hAnsi'),'Times New Roman');pr.append(fonts)
 c=OxmlElement('w:color');c.set(qn('w:val'),'000000');pr.append(c);r.append(pr);t=OxmlElement('w:t');t.text=text;r.append(t);h.append(r);p._p.append(h)
 sz=OxmlElement('w:sz');sz.set(qn('w:val'),str(size*2));pr.append(sz)
 if bold:pr.append(OxmlElement('w:b'))

def para(text='',size=12,align=None,after=4,bold=False):
 text=readable(text)
 p=add_p();p.paragraph_format.space_after=Pt(after)
 p.paragraph_format.widow_control=True;p.paragraph_format.keep_together=False
 if align is not None:p.alignment=align
 last=0
 for m in re.finditer(r'Lampiran ([A-L]\.\d+)|https?://\S+',text):
  p.add_run(text[last:m.start()])
  if m.group(1):linkrun(p,m.group(0),m.group(1))
  else:
   url=m.group(0).rstrip('.,;');h=OxmlElement('w:hyperlink');h.set(qn('r:id'),doc.part.relate_to(url,RT.HYPERLINK,is_external=True));r=OxmlElement('w:r');pr=OxmlElement('w:rPr');c=OxmlElement('w:color');c.set(qn('w:val'),'000000');pr.append(c);r.append(pr);t=OxmlElement('w:t');t.text=url;r.append(t);h.append(r);p._p.append(h)
   if len(url)<len(m.group(0)):p.add_run(m.group(0)[len(url):])
  last=m.end()
 p.add_run(text[last:])
 for r in p.runs:r.font.size=Pt(size);r.font.name='Times New Roman';r.font.bold=bold;r.font.color.rgb=RGBColor(0,0,0)
 return p

def heading(text,key=None,level=1):
 p=add_p(text,style=f'Heading {level}')
 if key:anchor(p,key)
 return p

def table(headers,rows,widths=None,title=None):
 if title:
  p=para(title,bold=True);p.paragraph_format.keep_with_next=True
 n=len(headers); widths=widths or ([16/n]*n)
 # Rebalance supplied widths without changing column proportions.
 widths=[16*w/sum(widths) for w in widths]
 t=doc.add_table(rows=1,cols=n);t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 for i,w in enumerate(widths):t.columns[i].width=Cm(w)
 props=t._tbl.tblPr
 borders=OxmlElement('w:tblBorders')
 for edge in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'666666');borders.append(e)
 props.append(borders)
 margins=OxmlElement('w:tblCellMar')
 for edge,val in [('top',65),('bottom',65),('left',80),('right',80)]:
  e=OxmlElement('w:'+edge);e.set(qn('w:w'),str(val));e.set(qn('w:type'),'dxa');margins.append(e)
 props.append(margins)
 for ri,row in enumerate([headers]+rows):
  cells=t.rows[0].cells if ri==0 else t.add_row().cells
  trpr=cells[0]._tc.getparent().get_or_add_trPr()
  no=OxmlElement('w:cantSplit');trpr.append(no)
  if ri==0:trpr.append(OxmlElement('w:tblHeader'))
  for i,val in enumerate(row):
   cells[i].width=Cm(widths[i]);cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   tcpr=cells[i]._tc.get_or_add_tcPr();sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'FFFFFF');tcpr.append(sh)
   p=cells[i].paragraphs[0];p.paragraph_format.line_spacing=1;p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0);p.alignment=WD_ALIGN_PARAGRAPH.LEFT
   if val is None or str(val)=='None':val='Tidak tercapai dalam 36 bulan'
   val=readable(str(val))
   if ri>0 and i in [0,2] and re.fullmatch('[A-L]',val):linkrun(p,val,val+'.1',10)
   else:p.add_run(val)
   for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(10);r.font.bold=ri==0;r.font.color.rgb=RGBColor(0,0,0)
 return t

def figure(name,caption,note=None,width=16,maxheight=12):
 path=F/(name+'.png')
 if not path.exists():print('MISSING FIG',name);return
 im=Image.open(path);w,h=im.size;wc=min(width,maxheight*w/h)
 p=add_p();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1;p.paragraph_format.keep_with_next=True
 p.add_run().add_picture(str(path),width=Cm(wc))
 p=para(caption,align=WD_ALIGN_PARAGRAPH.CENTER,after=3);p.paragraph_format.line_spacing=1.15
 if note:para(note,size=12,after=5).paragraph_format.line_spacing=1.15

def shot(file,caption,note=None):
 path=S/file
 if not path.exists():return
 im=Image.open(path);w,h=im.size
 p=add_p();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.line_spacing=1;p.paragraph_format.keep_with_next=True
 width=7.8 if file=='17-intake-detail.png' else (13 if file=='11-owner-vehicle.png' else (13.5 if file=='01-network.png' else 16))
 p.add_run().add_picture(str(path),width=Cm(width))
 para(caption,align=WD_ALIGN_PARAGRAPH.CENTER).paragraph_format.line_spacing=1.15
 if note:para(note)

def shotpair(files):
 t=doc.add_table(rows=1,cols=2);t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER
 for i,(file,caption) in enumerate(files):
  t.columns[i].width=Cm(8);c=t.cell(0,i);c.width=Cm(8);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.TOP
  p=c.paragraphs[0];p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(4);p.paragraph_format.keep_with_next=True
  p.add_run().add_picture(str(S/file),width=Cm(7.6))
  p=c.add_paragraph(caption);p.alignment=WD_ALIGN_PARAGRAPH.LEFT;p.paragraph_format.line_spacing=1.15;p.paragraph_format.space_after=Pt(2)
  for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(12)

def npv_equation():
 p=add_p();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 op=OxmlElement('m:oMathPara');om=OxmlElement('m:oMath');op.append(om)
 def mr(text):
  r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=text;r.append(t);return r
 def sub(base,idx):
  n=OxmlElement('m:sSub');e=OxmlElement('m:e');e.append(mr(base));n.append(e);s=OxmlElement('m:sub');s.append(mr(idx));n.append(s);return n
 om.append(mr('NPV = −I + '));n=OxmlElement('m:nary');pr=OxmlElement('m:naryPr');ch=OxmlElement('m:chr');ch.set(qn('m:val'),'∑');pr.append(ch);n.append(pr)
 for tag,text in [('sub','t = 1'),('sup','36')]:e=OxmlElement('m:'+tag);e.append(mr(text));n.append(e)
 e=OxmlElement('m:e');fr=OxmlElement('m:f');num=OxmlElement('m:num');num.append(sub('CF','t'));fr.append(num);den=OxmlElement('m:den');power=OxmlElement('m:sSup');base=OxmlElement('m:e');base.append(mr('(1 + 0,12)'));power.append(base);sup=OxmlElement('m:sup');sup.append(mr('t/12'));power.append(sup);den.append(power);fr.append(den);e.append(fr);n.append(e);om.append(n);p._p.append(op)

def newpage():
 global pending_break
 pending_break=True
def readable(text):
 if 'http' in text:return text
 if re.fullmatch(r'(?:R\d+|[A-L]\.\d+)',text):return text
 text=re.sub(r'([a-zÀ-ž])(\d)',r'\1 \2',text)
 text=re.sub(r'(\d)([a-zÀ-ž])',r'\1 \2',text)
 text=re.sub(r'(?<=[a-z])Rp', ' Rp', text)
 text=re.sub(r'\b(TAM|SAM|SOM|USD)(?=\d)',r'\1 ',text)
 text=re.sub(r'%(?=[A-Za-z])','% ',text)
 text=re.sub(r'(?<=[a-z%]),(?=\d)',', ',text)
 text=text.replace('3 PL','3PL').replace('perpermintaan','per permintaan').replace('tambahanjarak','tambahan jarak').replace('tahunketiga','tahun ketiga').replace('Kasakhir','Kas akhir').replace('Piutangakhir','Piutang akhir').replace('Kasbersih','Kas bersih')
 for old,new in [('danRp','dan Rp'),('sebesarRp','sebesar Rp'),('bertahapRp','bertahap Rp'),('rencanaRp','rencana Rp'),('diJabodetabek','di Jabodetabek'),('jutaRp','juta Rp'),('NPVjuta','NPV juta'),('PerubahanNPV','Perubahan NPV'),('Danajuta','Dana juta'),('pengeluaranawal','pengeluaran awal'),('jeda perangkat','jeda perangkat'),('tariftetap','tarif tetap'),('jedaperangkat','jeda perangkat')]:text=text.replace(old,new)
 for old,new in [('akhirperiode','akhir periode'),('perperangkat','per perangkat'),('setiapempat','setiap empat'),('bukanjaminan','bukan jaminan'),('perbulan','per bulan'),('hostbaru','institusi baru'),('Peralatanawal','Peralatan awal'),('perangkatlunak','perangkat lunak'),('danunit','dan unit'),('danaP90','dana P90'),('rentangP90','rentang P90'),('5,7,dan10','5, 7, dan 10'),('Downside:bulan','Downside: bulan')]:text=text.replace(old,new)
 return text
def money(v):return 'Rp'+f'{v:,.0f}'.replace(',','.')
def rootpage(id,title,ps=None,tables=None,fig=None):
 return dict(id=id,title=title,return_to='gagasan',paragraphs=ps or [],tables=tables or [],figure=fig)
def tconv(key):
 t=ft[key];result=dict(title=t['title'],headers=t['columns'],rows=t['rows'],note=t.get('note'))
 if key=='H5':result['widths']=[0.8,1.6,1.2,2.4,2,2,2,2]
 if key=='H6':result['widths']=[1.7,1.6,1.2,2.3,2.3,2.3,2.3,2.3]
 if key.startswith('L'):
  result['rows']=[[str(v).replace('%',' %').replace('.',',') if '%' in str(v) else v for v in row] for row in result['rows']]
 return result
# Cover deliberately left for participant.
for _ in range(5):para('',after=10)
p=para('[JUDUL ESAI]',size=16,bold=True,align=WD_ALIGN_PARAGRAPH.CENTER)
para('[NAMA PESERTA]',align=WD_ALIGN_PARAGRAPH.CENTER)
new=doc.add_section(WD_SECTION_START.NEW_PAGE);new.different_first_page_header_footer=False
num=OxmlElement('w:pgNumType');num.set(qn('w:start'),'1');new._sectPr.append(num)
# Five controlled main pages. Paragraphs remain native editable text.
for pi,page in enumerate(main['pages']):
 if pi:newpage()
 if pi==0:
  p=doc.add_paragraph(main['title'],style='Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 for b in page['blocks']:
  if 'heading' in b:
   k={'Pembuka':'pembuka','Analisis Masalah':'analisis','Gagasan dan Implementasi':'gagasan','Dampak':'dampak','Penutup':'penutup'}[b['heading']]
   heading(b['heading'],k)
  elif 'p' in b:para(b['p'])
  else:figure(b['figure'],b['caption'],b.get('note'),maxheight=4.6)
# References source pack normalized below.
newpage();heading('Daftar Pustaka','references')
refs=evidence.get('sources',[]) if isinstance(evidence,dict) else []
if isinstance(refs,dict):refs=list(refs.values())
for item in sorted(refs,key=lambda x:x.get('apa','').casefold()):
 text=item if isinstance(item,str) else item.get('apa',item.get('apa7',item.get('reference','')))
 if text:
  p=para(text,align=WD_ALIGN_PARAGRAPH.LEFT,after=0);p.paragraph_format.left_indent=Cm(.7);p.paragraph_format.first_line_indent=Cm(-.7);p.paragraph_format.keep_together=True
  italics={'GEM2024':'The global e-waste monitor 2024','ITU_INDONESIA':'Indonesia.','BRANDO2024':'International Journal of Sustainable Development and Planning, 19','SIRINGO2020':'Global Journal of Environmental Science and Management, 6','LINTASARTA2026':'[Official fact sheet] Pengelolaan perangkat elektronik dan e-waste di Lintasarta','EWASTERJ':'Electronic waste circular ecosystem','YANG2024':'Tackling the crowdsourced shared-trip delivery problem at scale with a novel decomposition heuristic','SARI2024':'Journal of Industrial Engineering and Management, 17','NIST2025':'Guidelines for media sanitization','CIPD2025':'PESTLE analysis','DAVID2020':'Strategic management: Concepts: A competitive advantage approach','HEI2025':'Statistik pendidikan tinggi 2025','UN_SDG12':'Goal 12: Ensure sustainable consumption and production patterns','UN_SDG17':'Goal 17: Strengthen the means of implementation and revitalize the global partnership for sustainable development'}
  target=italics.get(item.get('id'))
  if target:
   for r in list(p.runs):
    if target in r.text:
     before,after=r.text.split(target,1);r.text=before
     ri=p.add_run(target);ri.italic=True;ri.font.name='Times New Roman';ri.font.size=Pt(12);ra=p.add_run(after);ra.font.size=Pt(12);ra.font.name='Times New Roman'
     r._r.addnext(ri._r);ri._r.addnext(ra._r)
# Appendix map and all sections in numeric order.
newpage();heading('Lampiran','appendices')
para('Rujukan dalam esai membuka bagian terkait. Kode pada daftar berikut membuka awal kelompok; judul setiap lampiran mengarah kembali ke bagian esai yang menjelaskannya.')
maprows=[['A','Masalah dan akar penyebab','Bukti dan pemetaan respons'],['B','Alternatif dan kontribusi','Perbandingan layanan'],['C','Peserta dan pemangku kepentingan','Nilai, peran, dan hubungan kerja'],['D','Operasi dan keputusan','Pencocokan, persetujuan, serah terima'],['E','Prototipe','Antarmuka dan perilaku yang dijalankan'],['F','Perbandingan skenario','Cakupan, perjalanan, dan biaya'],['G','Strategi','PESTEL, IFE/EFE, TOWS, persaingan'],['H','Pasar dan pendanaan','TAM/SAM/SOM dan akun layanan'],['I','Pelaksanaan','Gantt dan tanggung jawab'],['J','Risiko','Pemicu, pengendalian, dan sumber daya'],['K','Dampak dan evaluasi','Sasaran, hasil, dan denominasi'],['L','Metode dan perhitungan','Monte Carlo dan rekonstruksi angka']]
table(['Kode','Rincian','Kode','Rincian'],[[maprows[i][0],maprows[i][1],maprows[i+6][0],maprows[i+6][1]]for i in range(6)],[1.1,6.9,1.1,6.9])
para('Sumber eksternal dirujuk ke Daftar Pustaka; angka rencana merupakan estimasi tim. Skenario prototipe memakai data rekaan.')
# Root-authored evidence, implementation evidence and finance pages.
extra=[]
extra.append(rootpage('A.1','Pohon masalah dan arah intervensi',['Tujuannya ialah menghubungkan keputusan pemilik dengan jalur penanganan yang dapat dipenuhi. Tiga cabang memisahkan akses, kesesuaian pengangkutan, dan kesinambungan penyelesaian. Penyebab pada tingkat terakhir menjadi alasan rancangan yang dijelaskan dalam Lampiran D.3 dan Lampiran H.2.'],fig='issue_tree'))
extra.append(rootpage('A.2','Bukti masalah dan hubungan dengan rancangan',['Data perilaku digunakan pada cakupan penelitiannya. Temuan mengenai penyimpanan perangkat menjelaskan alasan pilihan pemilik; temuan tersebut tidak mengukur permintaan layanan UI/Depok.'],[dict(title='Bukti akar penyebab dan respons',headers=['Penyebab','Bukti dan cakupan','Respons JejakBalik'],rows=[['Tujuan pengembalian tidak jelas','75 dari305 responden penyimpan elektronik rumah tangga tidak mengetahui tujuan pembuangan (24,6%); enam provinsi Jawa, Brando et al. (2024), Tabel6.','Pilihan penerima dan syarat penerimaan dijelaskan sebelum penjemputan.'],['Perangkat masih dipandang dapat diperbaiki','99 dari305 (32,5%) ingin memperbaiki elektronik rumah tangga kelak; Brando et al. (2024), Tabel6.','Instruksi pemilik dan pemeriksaan mempertahankan pilihan perbaikan.'],['Kemudahan akses memengaruhi pertimbangan pemilik','Survei Jakarta208responden2018: korelasi niat dengan informasi0,521; kemudahan0,411 (Siringo et al.,2020).','Akses terjadwal dan penjelasan proses terhubung pada program.'],['Data pribadi menahan pelepasan perangkat','19 dari305 (6,23%) menyebut keamanan data untuk elektronik pribadi, Brando et al.(2024),Tabel7.','Persetujuan, instruksi data, penahanan, dan rujukan penanganan kompeten.'],['Asal, tujuan, waktu dan kapasitas belum tentu selaras','Yang et al.(2024) memodelkan perjalanan bersama dengan asal/tujuan sendiri; hasil biaya tidak menjamin penurunan jarak.','Periksa tambahanjarak, durasi, kapasitas dan penerimaan bersama.'],['Penanganan patuh memerlukan sumber daya','GEM2024 membedakan biaya penanganan patuh dan biaya eksternal; Sari et al.(2024) menunjukkan kelayakan jaringan bergantung pada aliran dan investasi.','Kontrak institusi mendanai koordinasi, pemenuhan dan kasus tertahan.']],widths=[4,7,5])]))
# Screenshots selected by observed job.
for id,title,files,ps in [
 ('E.1','Jaringan dan permintaan perangkat',[('01-network.png','Gambar E1. Jaringan perjalanan dan kota pada aplikasi yang dijalankan.')],['Antarmuka versi 3.0 menampilkan tiga penyedia rekaan, enam perjalanan, dan 18 permintaan. Kota memperlihatkan hubungan permintaan, kendaraan dan penerima.']),
 ('E.2','Perbandingan pilihan dan persetujuan',[('09-options-detail.png','Gambar E2. Pilihan perjalanan yang memenuhi atau gagal memenuhi syarat.'),('03-approval.png','Gambar E3. Peninjauan rencana sebelum persetujuan eksplisit.')],['Pemilihan dan pratinjau mendahului persetujuan penugasan. Dialog peninjauan harus sesuai revisi masukan; perubahan kendala membatalkan persetujuan sebelumnya.']),
 ('E.3','Kustodi dan persoalan yang belum selesai',[('04-custody-exception.png','Gambar E4. Perangkat tetap pada pembawa setelah perjalanan dibatalkan.'),('05-data-hold.png','Gambar E5. Penerimaan tidak otomatis menyelesaikan peninjauan data.')],['Kedua keadaan berikut berasal dari skenario yang telah dimajukan. Pembatalan tidak mengembalikan perangkat secara fiktif kepada pemilik; perangkat yang telah diterima juga tetap tertahan ketika keputusan data belum selesai. Tombol peninjauan data merekam keputusan simulasi, bukan melakukan penghapusan data.']),
 ('E.4','Hasil awal dan formulir permintaan',[('08-reference-results.png','Gambar E6. Hasil rencana18permintaan sebelum pelaksanaan simulasi.'),('07-intake.png','Gambar E7. Masukan perangkat dan persetujuan pemilik.')],['Pada hasil awal,18permintaan terhubung dengan rencana, nol selesai, dan18masih menjadi kewajiban. Angka28,8km danRp438.700 adalah hasil perencanaan; formulir tambahan tetap memerlukan persetujuan pemilik.'])]:
 p=rootpage(id,title,ps);p['shots']=files;extra.append(p)
extra.append(rootpage('E.5','Akses dan batas perangkat lunak',['Prototipe versi 3.0.0 tersedia pada repositori publik berikut. Tangkapan layar lokal memperlihatkan aplikasi yang dijalankan, termasuk tampilan WebGL.','https://github.com/Fafauzif/JejakBalik-Prototype','Penyimpanan masih berada di peramban. Akun lintas organisasi, pemesanan pengangkut, pembayaran, autentikasi kustodi, dan bukti pengolahan nyata memerlukan implementasi operasi. Bantuan AI opsional memberi saran pendataan; persetujuan dan perubahan status tetap dikendalikan pengguna.','Status tuntas pada prototipe mengikuti penerimaan, persetujuan, dan keputusan data dalam model; bukti perbaikan, penempatan penggunaan kembali atau pengolahan belum menjadi syarat perangkat lunak.'],[dict(title='Fungsi yang dijalankan dan hubungannya dengan layanan',headers=['Fungsi','Perangkat lunak saat ini','Kebutuhan operasi'],rows=[['Pencocokan','Penyisipan deterministik sebelum perjalanan berangkat; penerima tetap per permintaan.','Penawaran perjalanan dan syarat penerima yang disepakati.'],['Persetujuan','Pemeriksaan revisi dan rencana sebelum kemajuan status.','Identitas dan kewenangan petugas.'],['Kustodi','Peristiwa kronologis dengan penahanan saat gangguan.','Serah terima yang diakui kedua pihak dan tindak lanjut.'],['Biaya','Kompensasi dan anggaran penanganan berbasis asumsi.','Tarif, tagihan dan pembayaran yang direkonsiliasi.']],widths=[3,6.5,6.5])]))
for id,title,file,caption,note in [
 ('E.6','Kendaraan dan kapasitas perjalanan','11-owner-vehicle.png','Gambar E8. Kendaraan terpilih dan batas perjalanan pada prototipe.','Tampilan kendaraan menggabungkan kapasitas, tambahan jarak, durasi dan kompensasi. Tangkapan layar tim dipotong pada model dan panel terkait.'),
 ('E.7','Ruang penerimaan dan pemeriksaan','12-owner-facility.png','Gambar E9. Visualisasi fasilitas penerimaan dalam prototipe.','Stasiun penerimaan, pemeriksaan, tinjauan data dan penyaluran menggambarkan urutan pekerjaan yang perlu disiapkan. Visual ini merupakan model antarmuka, bukan fasilitas yang telah beroperasi. Tangkapan layar disediakan oleh tim dan dipotong pada area fasilitas.')]:
 p=rootpage(id,title,[note]);p['shots']=[(file,caption)];extra.append(p)
extra.append(rootpage('F.1','Perbandingan beban layanan yang setara',['Skenario awal memuat18permintaan, tiga penyedia, dan enam perjalanan pada jaringan jalan rekaan. Kedua pilihan memenuhi18permintaan dalam kendala model. JejakBalik menghitung tambahan perjalanan terhadap rute yang tetap akan dijalankan, sedangkan pembanding memakai putaran pengumpulan khusus. Biaya mencakup kompensasi dan anggaran penanganan dalam model, belum biaya organisasi penuh.'],[dict(title='Hasil skenario awal',headers=['Ukuran','JejakBalik','Pengumpulan khusus berkelompok'],rows=[['Permintaan direncanakan','18 dari18','18 dari18'],['Perjalanan pemulihan','28,8km tambahan','112,8km putaran khusus'],['Biaya model','Rp438.700','Rp662.400'],['Status kesetaraan','Penerimaan dan jendela waktu terpenuhi','Penerimaan dan jendela waktu terpenuhi']],widths=[5,5.5,5.5])],fig='prototype_comparison'))
scpath=P/'prototype_scenarios.json'
if scpath.exists():
 scenarios=json.loads(scpath.read_text()); print('SCENARIO schema',type(scenarios))
else:scenarios=[]
extra.append(rootpage('F.2','Akses lintas penyedia dan gangguan kendala',['Pengujian eksploratif membatasi penyedia pada masukan perangkat yang sama. Cakupan menjadi ukuran pertama karena biaya total yang lebih kecil dapat terjadi ketika lebih sedikit perangkat dilayani. Hasil ini menguji perilaku konfigurasi rekaan, bukan tingkat ketersediaan penyedia di Depok.']))
# Financial units and schedules.
m=finance['market'];be=finance['breakeven'];base=finance['base'];mc=finance['monte_carlo']
extra.append(rootpage('H.1','Pasar institusi dan jangkauan layanan',['Pasar didefinisikan sebagai layanan program institusi, bukan nilai jual seluruh perangkat. Statistik Pendidikan Tinggi2025 mencatat4.303perguruan tinggi (Kemdiktisaintek,2026). Angka ini menjadi batas atas semesta institusi; kelayakan, anggaran dan keputusan membeli tetap harus disaring. SAM100program merupakan skenario jangkauan tim diJabodetabek, bukan hitungan institusi terverifikasi.'],[dict(title='TAM SAM SOM layanan institusi',headers=['Lapisan','Dasar perhitungan','Nilai'],rows=[['TAM','4.303institusi ×Rp65,76juta/tahun','Rp282,965miliar/tahun'],['SAM','100program ×Rp65,76juta/tahun; estimasi tim','Rp6,576miliar/tahun'],['SOM tahun3','126bulan-institusi ×Rp5,48juta; akhirperiode12institusi','Rp690,48juta pada2029']],widths=[2,9,5])],fig='tam_sam_som'))
extra.append(rootpage('H.2','Penawaran layanan dan biaya yang ditanggung',['Semua tarif dan biaya berikut merupakan estimasi tim pada rupiah konstan2027. Institusi membayarRp3juta/bulan untuk koordinasi dan biaya perperangkat yang diterima tujuan dengan serah terima direkonsiliasi. Tarif perangkat tidak merupakan sertifikat penggunaan kembali atau daur ulang selesai.','Pada bauran80% biasa,15%besar dan5%khusus, tarif rata-rataRp62.000dan biaya langsungRp44.350/perangkat. Dengan40perangkat, penerimaanRp5,48juta dan biaya langsungRp1,774juta menyisakanRp3,706juta untuk biaya bersama.'],[tconv('H1')]))
extra.append(rootpage('H.3','Biaya bersama dan kebutuhan dana',['Anggaran bersama memasukkan imbalan pendiri, petugas operasi, komunikasi, ruang kerja, sistem, dukungan profesional dan perlindungan. Modal awalRp28juta dipisahkan dari biaya bulanan. Pembiayaan dasar yang direncanakanRp110juta belum merupakan komitmen; kebutuhan dasar termasuk cadangan sebesar'+money(base['required_funding'])+'.'],[tconv('H2')]))
extra.append(rootpage('H.4','Proyeksi tiga tahun dan keberlanjutan layanan',['Tahun pertama menanggung persiapan dan pembentukan kontrak. Biaya kerja bertambah sesuai jumlah institusi dan perangkat; penjualan perangkat, kredit karbon dan nilai terminal tidak masuk penerimaan. Seluruh hasil berikut sebelum pajak, bunga dan distribusi pemilik.','NPV tiga tahun sebelum pajak pada diskonto12% sebesar'+money(base['npv'])+'; pemulihan kas proyek terjadi pada bulan'+str(base['payback_month'])+'. Pendanaan masuk dipisahkan dari kas proyek agar bukan penentu NPV.'],[tconv('H3')],fig='finance_annual'))
extra.append(rootpage('H.5','Arus kas bulanan tahun pertama',['Biaya koordinasi dibayar di muka, sedangkan tarif perangkat ditagih dengan jeda satu bulan. Saldo tanpa pembiayaan menunjukkan kebutuhan dana; saldo dengan rencana pembiayaan bukan bukti uang telah tersedia.'],[tconv('H5')]))
extra.append(rootpage('H.6','Tahap kontrak dan kas perkuartal',['Jumlah institusi pada akhir tahun berbeda dari jumlah bulan-institusi yang menghasilkan penerimaan. Model pertama dimulai pada bulan3, kemudian menambah institusi pada bulan5,7,dan10. Tahun kedua berakhir pada8institusi dan tahunketiga12institusi.'],[tconv('H6')]))
extra.append(rootpage('H.7','Skenario dan titik impas',['Perubahan kontrak, volume, harga, biaya dan pembayaran diteruskan ke jadwal kas yang sama. Skenario penurunan tetap ditampilkan sebagai dasar pembatasan komitmen dan kebutuhan pembiayaan. Rincian ketidakpastian gabungan berada pada Lampiran L.1.'],[tconv('H4'),tconv('H7')]))
extra.append(rootpage('L.1','Simulasi Monte Carlo dan kebutuhan pendanaan',['Simulasi menjalankan10.000kombinasi asumsi dengan seed20261104. Rentang tarif, jumlah kontrak, volume, biaya dan pembayaran merupakan estimasi tim. Faktor bersama mempertahankan hubungan antara kontrak dan volume serta antarbiaya. Kapasitas petugas ditambah ketika beban kerja menuntutnya.','Frekuensi NPV positif sebesar84,74% berlaku pada distribusi yang dinyatakan, bukan probabilitas keberhasilan pasar. Kebutuhan danaP90 sebesarRp155,63juta menunjukkan bahwa rencanaRp110juta tidak cukup untuk seluruh kondisi. Usulan batas pendanaan bertahapRp160juta dapat terdiri atasRp110juta dasar danRp50juta tambahan yang hanya digunakan setelah persetujuan pendanaan. Komitmen pendanaan saat ini nol.'],[tconv('L1')],fig='mc_npv'))
extra.append(rootpage('L.2','Penggerak hasil dan stabilitas numerik',['Pemeriksaan membandingkan5.000draw pertama dengan10.000draw; perubahan kuantil dinilai relatif terhadap rentangP90–P10. Stabilitas numerik tidak memverifikasi harga atau minat institusi. Hubungan peringkat membantu memilih input yang paling berguna untuk diperbaiki dalam pengadaan dan pembaruan layanan.'],[dict(title='Asosiasi peringkat dengan NPV',headers=['Penggerak','Spearman rho'],rows=[[r['label'],f"{r['spearman']:.3f}".replace('.',',')]for r in mc['rank_associations']],widths=[11,5])],fig='mc_drivers'))
extra.append(rootpage('L.3','Distribusi asumsi dan sensitivitas',["Rentang berikut merupakan estimasi tim. Faktor permintaan dan volume mempunyai ketergantungan yang dinyatakan; pengaruh biaya dan perubahan jadwal diperiksa pada model yang sama."],[tconv('L2'),tconv('L3')]))
next(x for x in extra if x['id']=='L.2')['tables'].append(tconv('L4'))
# Reconcile coded issue-tree leaves with the supporting evidence.
ap=next(x for x in extra if x['id']=='A.2')
next(x for x in extra if x['id']=='A.1')['paragraphs']=['Pohon masalah membedakan pilihan pemilik, kelayakan perjalanan, dan penyelesaian layanan. Setiap akar dipetakan pada bukti dan respons dalam Lampiran A.2.']
ap['tables'][0]['rows']=[
 ['A1 Tujuan pengembalian tidak jelas','75/305 penyimpan elektronik rumah tangga (24,6%) tidak mengetahui tujuan pembuangan; enam provinsi Jawa (Brando et al., 2024, Tabel 6).','Penerima dan syarat penerimaan dijelaskan sebelum penjemputan.'],
 ['A2 Perbaikan dan keamanan data belum selesai','99/305 (32,5%) berniat memperbaiki elektronik rumah tangga kelak; secara terpisah 19/305 (6,23%) menyebut keamanan data untuk elektronik pribadi (Brando et al., 2024, Tabel 6–7).','Pilihan perbaikan, instruksi data, penahanan dan pelaksana sanitasi.'],
 ['B1 Waktu dan perjalanan harus bertemu','Survei Jakarta n=208 pada 2018: korelasi kemudahan–niat 0,411 (Siringo et al., 2020). Asal, tujuan dan waktu membatasi model perjalanan bersama (Yang et al., 2024).','Pencocokan lintas penyedia dengan batas tambahan perjalanan dan pilihan waktu lain.'],
 ['B2 Kapasitas dan kelayakan penanganan','Kapasitas membatasi model logistik (Yang et al., 2024); kategori dan kegiatan dibedakan dalam PP 27/2020, PP 22/2021 serta Permen LHK 6/2021. Kendala sistem ini tidak mengukur kapasitas UI.','Pemeriksaan kondisi, kapasitas, kategori serta kesesuaian penyedia dan penerima.'],
 ['C1 Penanganan patuh memiliki biaya nyata','Biaya pengolahan global USD0,36/kg pada jalur sesuai standar dan USD0,12/kg pada jalur lain, di luar pengumpulan terpisah (Baldé et al., 2024). Angka ini bukan tarif Indonesia.','Kontrak institusi membiayai kesiapan, pemenuhan dan tindak lanjut.'],
 ['C2 Tanggung jawab harus tersambung','Kolaborasi aktor diperlukan dalam rancangan jaringan Indonesia (Puspita-Sari et al., 2024); tanggung jawab lingkungan dan data dirujuk pada PP 22/2021 dan UU 27/2022. Ini implikasi rancangan, bukan statistik kehilangan.','Pemilik kasus, serah terima berpasangan, bukti penerimaan dan alur pengecualian.']]
fp=next(x for x in extra if x['id']=='F.1')
fp['paragraphs'][0]=fp['paragraphs'][0].replace('Kedua pilihan memenuhi18permintaan dalam kendala model.','Kedua pilihan memenuhi 18 permintaan dengan kendala kapasitas, waktu dan penerima. Biaya pembanding Rp662.400 melampaui batas anggaran skenario Rp600.000; kesetaraan di sini menyangkut beban layanan dan kelayakan operasi, bukan kelayakan anggaran.')
hp=next(x for x in extra if x['id']=='H.1');hp['paragraphs'][0]=hp['paragraphs'][0].replace('(Kemdiktisaintek,2026)','(Kementerian Pendidikan Tinggi, Sains, dan Teknologi, 2026)')
hp['paragraphs'][0]=hp['paragraphs'][0].replace('Teknologi, 2026','Teknologi Republik Indonesia, 2026')
hp=next(x for x in extra if x['id']=='H.4');hp['paragraphs'][1]=hp['paragraphs'][1].replace('diskonto12%','diskonto riil 12% (estimasi tim)')
hp=next(x for x in extra if x['id']=='H.6');hp['paragraphs'][0]=hp['paragraphs'][0].replace('Model pertama dimulai pada bulan3','Program institusi pertama mulai beroperasi pada bulan ketiga')
fp['tables'][0]['rows'].append(['Anggaran skenario Rp600.000','Terpenuhi','Melebihi Rp62.400'])
ep=next(x for x in extra if x['id']=='E.4');ep['paragraphs'].append('Biaya Rp438.700 terdiri atas kompensasi penyedia Rp176.200 dan alokasi penanganan Rp262.500; sebelum pelaksanaan, seluruh alokasi penanganan masih menjadi kewajiban terbuka dalam model.')
for pg in extra:
 if pg['id']=='E.2':pg['shotpair']=[('19-options-compact.png','Gambar E2. Pilihan perjalanan dan batas penerimaan.'),('15-approval-detail.png','Gambar E3. Rencana yang memerlukan persetujuan eksplisit.')];pg.pop('shots',None)
 if pg['id']=='E.3':pg['shots']=[('13-custody-detail.png','Gambar E4. Kustodi bertahan setelah pembatalan perjalanan.'),('14-data-detail.png','Gambar E5. Penanganan akhir menunggu keputusan data.')]
 if pg['id']=='E.4':pg['shots']=[('18-results-detail.png','Gambar E6. Rencana awal dan kewajiban yang masih terbuka.'),('17-intake-detail.png','Gambar E7. Pendataan dan persetujuan pemilik.')]
# Build general pages and merge content.
pages=json.loads((P/'appendix_content.json').read_text())+extra
if (P/'method_appendix.json').exists():pages.append(json.loads((P/'method_appendix.json').read_text()))
pages.sort(key=lambda p:(p['id'].split('.')[0],int(p['id'].split('.')[1])))
figure_map={'C.1':'concept_service','D.2':'service_swimlane','H.5':'finance_cash','I.1':'gantt_year1','I.2':'gantt_decade','J.1':'risk_heatmap'}
lastgroup=None
for page in pages:
 group=page['id'][0]
 # Explicit visual and major-group starts, otherwise let Word paginate the related material.
 p=heading('',page['id']);linkrun(p,'Lampiran '+page['id']+' '+page['title'],page.get('return_to','gagasan'),12,True)
 for txt in page.get('paragraphs',[]):
  if page['id']=='L.4' and txt.startswith('NPV ='):
   npv_equation();txt='Diskonto'+txt.split('Diskonto',1)[1];txt=txt.replace('tingkat bulanannya (1,12)^(1/12) − 1','tingkat ekuivalen bulanannya sekitar 0,9489%')
  para(txt)
 fig=page.get('figure') or figure_map.get(page['id'])
 deferfig=fig=='concept_service'
 if deferfig:fig=None
 if fig:
  if fig=='concept_service':
   path=A/'concept_service.png'
   if path.exists():
    p=add_p();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.line_spacing=1;p.paragraph_format.keep_with_next=True;p.add_run().add_picture(str(path),height=Cm(8.5));para('Gambar C1. Konsep penerimaan perangkat dalam program institusi.',align=WD_ALIGN_PARAGRAPH.CENTER);para('Ilustrasi rancangan, bukan dokumentasi kegiatan UI atau kemitraan yang telah berjalan.')
  else:figure(fig,'Gambar '+page['id']+'. '+page['title']+'.',maxheight=12)
 for ti,t in enumerate(page.get('tables',[])):
  table(t.get('headers',t.get('columns')),t['rows'],t.get('widths'),t.get('title'))
  if t.get('note'):para(t['note'])
 if deferfig:
  p=add_p();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.line_spacing=1;p.paragraph_format.keep_with_next=True;p.add_run().add_picture(str(A/'concept_service.png'),height=Cm(8.5));para('Gambar C1. Konsep penerimaan perangkat dalam program institusi.',align=WD_ALIGN_PARAGRAPH.CENTER);para('Ilustrasi rancangan, bukan dokumentasi kegiatan UI atau kemitraan yang telah berjalan.')
 if page['id']=='L.1':figure('mc_funding','Gambar L1b. Sebaran kebutuhan dana dan batas pendanaan bertahap.',maxheight=8)
 if page.get('shotpair'):shotpair(page['shotpair'])
 for si,(filename,caption) in enumerate(page.get('shots',[])):
  shot(filename,caption)
 if page['id']=='F.2' and scenarios:
  arr=scenarios.get('results',[]) if isinstance(scenarios,dict) else scenarios
  if arr:
   table(['Kondisi','Terhubung / permintaan','Tambahan km','Biaya Rp'],[[x.get('label',x.get('name',x.get('case',''))),str(x.get('served',''))+'/18',str(x.get('addedKm',x.get('added_km',''))).replace('.',','),f"{x['totalCostIdr']:,}".replace(',','.')]for x in arr],[6,3,3,4])
   para('Setiap baris memakai 18 permintaan awal. Angka menunjukkan penugasan sebelum pelaksanaan; nol tambahan kilometer tetap dapat menimbulkan kompensasi dan biaya penanganan. Biaya dengan cakupan berbeda tidak merupakan penghematan layanan setara.')
 lastgroup=group
# Metadata and structural audit.
doc.core_properties.last_modified_by='';doc.core_properties.title=main['title'];doc.core_properties.author='';doc.core_properties.subject='Smart Recovery';doc.core_properties.comments='';doc.core_properties.keywords='JejakBalik, Smart Recovery, pengembalian elektronik'
missing=sorted(set(links)-targets)
if missing:raise ValueError('Broken anchors '+str(missing))
path=OUT/'JejakBalik_Esai_dan_Lampiran.docx'
buffer=io.BytesIO();doc.save(buffer);data=buffer.getvalue()
with zipfile.ZipFile(io.BytesIO(data)) as check:assert check.testzip() is None
temporary=OUT/'JejakBalik_verified.tmp';temporary.write_bytes(data)
assert temporary.read_bytes()==data
os.replace(temporary,path)
(P/'build_manifest.json').write_text(json.dumps({'file':str(path),'targets':sorted(targets),'internal_links':len(links),'appendix_sections':len(pages),'missing':missing},indent=2))
print(path,'appendix subsections',len(pages),'refs',len(refs),'links',len(links))
