from pathlib import Path
import json,subprocess,os
ROOT=Path('/workspace/scratch/91cdcc6b9385')
OUT=ROOT/'production/assets/figures';SRC=ROOT/'production/figures'
PRE=r'''\documentclass[tikz,border=3pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{mathptmx}
\usepackage{tikz,pgfplots}
\usetikzlibrary{arrows.meta,positioning,calc,fit,backgrounds,shapes.geometric}
\pgfplotsset{compat=1.18}
\definecolor{forest}{HTML}{346E57}
\definecolor{sage}{HTML}{E8EFEA}
\definecolor{clay}{HTML}{AC653F}
\definecolor{sand}{HTML}{F4EAE2}
\definecolor{ink}{HTML}{252525}
\definecolor{light}{HTML}{F5F5F3}
\definecolor{gridgray}{HTML}{D8DAD6}
\tikzset{box/.style={draw=ink!70,line width=.5pt,rectangle,rounded corners=1pt,fill=white,align=center,font=\fontsize{11}{12}\selectfont,inner sep=6pt}, flow/.style={-{Latex[length=2.4mm]},line width=.7pt,draw=ink!80}, data/.style={flow,densely dashed,draw=forest}, label/.style={font=\fontsize{10}{11}\selectfont,fill=white,inner sep=2pt,align=center}}
\hyphenpenalty=10000\exhyphenpenalty=10000\begin{document}
'''
POST='\n\\end{document}\n'
manifest=[]
def build(name,code,job,dpi=280):
 if os.environ.get('JEJAK_FIGURE_ONLY') and name!=os.environ['JEJAK_FIGURE_ONLY']:return
 p=SRC/(name+'.tex');p.write_text(PRE+code+POST)
 r=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',str(OUT),str(p)],capture_output=True,text=True)
 if r.returncode: raise RuntimeError(name+'\n'+r.stdout[-4000:])
 subprocess.run(['pdftoppm','-png','-singlefile','-r',str(dpi),str(OUT/(name+'.pdf')),str(OUT/name)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 import fitz
 doc=fitz.open(OUT/(name+'.pdf'));rect=doc[0].rect
 manifest.append(dict(name=name,png=str(OUT/(name+'.png')),pdf=str(OUT/(name+'.pdf')),tex=str(p),width_cm=round(rect.width/72*2.54,2),height_cm=round(rect.height/72*2.54,2),job=job))
 print(name,manifest[-1]['width_cm'],manifest[-1]['height_cm'])

build('main_system',r'''\begin{tikzpicture}[x=1cm,y=1cm]
\node[box,text width=3.2cm,fill=sage] (host) at (0,2.4) {Institusi pemesan\\\textbf{Lingkup dan anggaran}};
\node[box,text width=3.7cm,fill=sage] (coord) at (5.5,2.4) {Koordinator JejakBalik\\\textbf{Cocokkan dan setujui}};
\node[box,text width=3.2cm] (owner) at (0,0) {Pemilik perangkat\\Informasi dan persetujuan};
\node[box,text width=3.7cm] (carrier) at (5.5,0) {Penyedia perjalanan\\Kapasitas yang ditawarkan};
\node[box,text width=3.3cm,fill=sand] (receiver) at (11.15,0) {Penerima sesuai kategori\\Terima, periksa, tindak lanjuti};
\draw[flow] (host)--node[label,above=3pt]{Biaya\\layanan}(coord);

\draw[data] (coord)--node[label,right]{Penugasan dan\\kompensasi}(carrier);
\draw[flow] (owner)--node[label,above]{Serah terima}(carrier);
\draw[flow] (carrier)--node[label,above]{Serah terima}(receiver);
\draw[data] (receiver.north)|-node[label,near start,right]{Penerimaan dan\\penyelesaian}(coord.east);
\draw[data] (owner.north east)--node[label,above,sloped]{Instruksi pemilik}(coord.south west);
\end{tikzpicture}''','Menghubungkan aktor, pembiayaan, penugasan dan serah terima dalam sistem yang diusulkan.')

build('issue_tree',r'''\begin{tikzpicture}[x=1cm,y=1cm]
\node[box,text width=14.4cm,fill=sage,font=\fontsize{12}{14}\selectfont] (problem) at (7.9,11.6) {\textbf{Pengembalian perangkat pascapakai belum terhubung secara andal}\\dengan pemanfaatan kembali dan pengolahan yang sesuai};
\foreach \x/\id/\text in {2.5/A/{Perangkat tertahan\\pada pemilik},7.9/B/{Penjemputan sulit\\dipenuhi bersama},13.3/C/{Penyelesaian layanan\\belum terjamin}} {
\node[box,text width=4.35cm,fill=sand,minimum height=1.25cm] (\id) at (\x,9.3) {\textbf{\text}};
\draw[flow] (problem.south)--++(0,-.45)-|(\id.north);
}
\node[box,text width=4.25cm,minimum height=3cm] (A1) at (2.5,5.8) {\textbf{A1. Tujuan pengembalian\\tidak jelas}\\24,6\% pada kelompok penyimpan perangkat rumah tangga};
\node[box,text width=4.25cm,minimum height=3cm] (A2) at (2.5,2.0) {\textbf{A2. Keputusan perbaikan\\dan data belum selesai}\\32,5\% ingin memperbaiki kemudian; privasi memerlukan penanganan};
\node[box,text width=4.25cm,minimum height=3cm] (B1) at (7.9,5.8) {\textbf{B1. Akses belum cocok\\dengan waktu dan perjalanan}\\Rute, jendela waktu dan kapasitas harus terpenuhi bersama};
\node[box,text width=4.25cm,minimum height=3cm] (B2) at (7.9,2.0) {\textbf{B2. Kebutuhan perangkat\\dan penerima berbeda}\\Kategori penanganan, kapasitas serta waktu terima membatasi pilihan};
\node[box,text width=4.25cm,minimum height=3cm] (C1) at (13.3,5.8) {\textbf{C1. Biaya layanan\\memerlukan penanggung}\\Pengangkutan, penanganan dan tindak lanjut memakai sumber daya};
\node[box,text width=4.25cm,minimum height=3cm] (C2) at (13.3,2.0) {\textbf{C2. Tanggung jawab\\antaraktor belum tersambung}\\Persetujuan, penerimaan dan penyelesaian perlu direkonsiliasi};
\foreach \id in {A,B,C}{\draw[flow](\id.south)--++(0,-.5)-|(\id1.north);\draw[flow](\id.south)--++(-2.45,-.5)|-(\id2.west);}
\end{tikzpicture}''','Pohon masalah dengan tiga submasalah dan enam penyebab; rincian bukti dan batas inferensi berada dalam tabel sumber pendamping.')

build('service_swimlane',r'''\begin{tikzpicture}[x=1cm,y=1cm]
\foreach \x/\title in {0/{Pemilik},3.9/{JejakBalik},7.8/{Pengangkut},11.7/{Penerima}}{
\fill[sage] (\x-1.85,0) rectangle(\x+1.85,.9);\node[font=\fontsize{12}{14}\selectfont\bfseries]at(\x,.45){\title};
\draw[gridgray] (\x-1.85,-9.4)rectangle(\x+1.85,0);}
\node[box,text width=2.9cm](input)at(0,-1.1){Informasi perangkat, waktu dan instruksi};
\node[box,text width=2.9cm](offers)at(7.8,-1.1){Tawarkan perjalanan dan kapasitas};
\node[box,text width=2.9cm](accept)at(11.7,-1.1){Tetapkan kategori, waktu dan kapasitas};
\node[box,text width=2.9cm,fill=sage](match)at(3.9,-2.6){Periksa kecocokan dan anggaran};
\node[box,text width=2.9cm](review)at(3.9,-4.15){Tinjau dan setujui penugasan};
\node[box,text width=2.9cm](pickup)at(7.8,-5.65){Jemput; catat serah terima dan pembawa};
\node[box,text width=2.9cm](receive)at(11.7,-7.15){Terima dan periksa perangkat};
\node[box,text width=2.9cm](decision)at(0,-7.15){Tinjau perubahan jalur bila diperlukan};
\node[box,text width=2.9cm,fill=sand](close)at(3.9,-8.7){Rekonsiliasi hasil atau tindak lanjut};
\draw[flow](input.east)-|(match.north);\draw[data](offers.west)-|(match.north);\draw[data](accept.west)--++(-.15,0)|-(match.east);
\draw[flow](match)--(review);\draw[flow](review.south)|-(pickup.west);\draw[flow](pickup.south)|-(receive.west);
\draw[data](receive.south)|-(close.east);\draw[data](decision.east)--(3.9,-7.15)--(close.north);
\draw[data](match.west)--++(-.2,0)--++(0,-6.1)--(close.west);
\node[label,rotate=90]at(1.75,-5.2){Belum cocok: tetap dalam daftar tindak lanjut};
\end{tikzpicture}''','Alur tanggung jawab dari informasi awal hingga penerimaan dan rekonsiliasi, termasuk permintaan yang belum cocok.')

build('gantt_year1',r'''\begin{tikzpicture}[x=.77cm,y=.85cm]
\def\rows{9}
\foreach\m in{1,...,12}{\draw[gridgray,line width=.35pt](\m,0)--(\m,-9.5);\node[font=\fontsize{10}{11}\selectfont]at(\m+.5,.35){\m};}
\node[anchor=east,font=\fontsize{10}{11}\selectfont]at(.8,.35){Bulan};
\foreach\y/\s/\e/\lab in {1/1/2/{Lingkup, operator dan institusi},2/1/2/{Penawaran perjalanan dan penerima},3/1/2/{Biaya dan kontrak layanan},4/1/2/{Rekaman bersama dan prosedur},5/2/2/{Pelatihan dan kesiapan penanganan},6/3/4/{Layanan UI/Depok pertama},7/3/12/{Rekonsiliasi dan pembaruan kontrak},8/5/10/{Program institusi berikutnya},9/9/12/{Kapasitas dan pembiayaan tahun kedua}}{
\node[anchor=east,text width=5cm,align=right,font=\fontsize{10}{11}\selectfont]at(.75,-\y){\lab};\fill[forest!65](\s,-\y-.22)rectangle(\e+1,-\y+.22);}
\foreach\x/\lab in{3/{Komisioning},13/{Rencana lanjutan}}{\draw[clay,densely dashed](\x,.05)--(\x,-9.5);\node[anchor=south,rotate=0,font=\fontsize{9}{10}\selectfont,text=black]at(\x,.75){\lab};}
\end{tikzpicture}''','Jadwal kerja tahun pertama; bulan relatif sejak persiapan dimulai, bukan tanggal komitmen yang telah disetujui.')

build('gantt_decade',r'''\begin{tikzpicture}[x=1cm,y=.85cm]
\foreach\y in{1,...,10}{\draw[gridgray,line width=.35pt](\y,0)--(\y,-7.6);\node[font=\fontsize{10}{11}\selectfont]at(\y+.5,.4){\y};}
\node[anchor=east,font=\fontsize{10}{11}\selectfont]at(.75,.4){Tahun};
\foreach\r/\s/\e/\lab in{1/1/1/{Layanan pertama UI/Depok},2/1/3/{Kontrak dan mutu layanan berulang},3/2/5/{Program institusi Jabodetabek},4/2/5/{Perluasan penyedia dan penerima},5/4/7/{Standar layanan lintas wilayah},6/6/10/{Replikasi wilayah yang siap},7/1/10/{Rekonsiliasi dan pendanaan}}{
\node[anchor=east,text width=5.1cm,align=right,font=\fontsize{10}{11}\selectfont]at(.75,-\r){\lab};
\ifnum\s>5\fill[forest!20](\s,-\r-.23)rectangle(\e+1,-\r+.23);\draw[forest,densely dashed](\s,-\r-.23)rectangle(\e+1,-\r+.23);\else\fill[forest!65](\s,-\r-.23)rectangle(\e+1,-\r+.23);\fi}
\draw[clay,densely dashed](6,.05)--(6,-7.6);
\node[font=\fontsize{10}{11}\selectfont,anchor=south]at(6,.85){Replikasi mengikuti kesiapan lokal};
\end{tikzpicture}''','Horizon strategis sepuluh tahun; bar replikasi bersyarat dibedakan dari pekerjaan awal.')

scenario=json.loads((ROOT/'JejakBalik-Prototype/docs/V3_REFERENCE_SCENARIO.json').read_text())['plan']
def coords_with_labels(values):
 return ' '.join('('+str(v)+','+str(i)+')['+f'{v:.1f}'.replace('.',',')+']' for i,v in enumerate(values,1))
comparison=r'''\begin{tikzpicture}
\begin{axis}[width=6.6cm,height=5.2cm,xbar,xmin=0,xmax=135,ytick={1,2},yticklabels={Pengumpulan terjadwal,JejakBalik},ymin=.4,ymax=2.6,bar width=11pt,xlabel={Tambahan perjalanan pemulihan (km)},xlabel style={font=\fontsize{10}{11}\selectfont},tick label style={font=\fontsize{10}{11}\selectfont},axis lines*=left,xmajorgrids=true,grid style={gridgray},nodes near coords,nodes near coords style={font=\fontsize{10}{11}\selectfont,text=black},point meta=explicit symbolic]
\addplot[fill=forest!65,draw=none]coordinates{KMVALUES};
\end{axis}
\begin{axis}[at={(7.3cm,0)},anchor=south west,width=6.5cm,height=5.2cm,xbar,xmin=0,xmax=780,ytick=\empty,ymin=.4,ymax=2.6,bar width=11pt,xlabel={Biaya layanan (ribu rupiah)},xlabel style={font=\fontsize{10}{11}\selectfont},tick label style={font=\fontsize{10}{11}\selectfont},axis lines*=left,xmajorgrids=true,grid style={gridgray},nodes near coords,nodes near coords style={font=\fontsize{10}{11}\selectfont,text=black},point meta=explicit symbolic]
\addplot[fill=clay!65,draw=none]coordinates{COSTVALUES};
\end{axis}
\end{tikzpicture}'''
comparison=comparison.replace('KMVALUES',coords_with_labels([scenario['baselineKm'],scenario['addedKm']])).replace('COSTVALUES',coords_with_labels([scenario['baselineCostIdr']/1000,scenario['totalCostIdr']/1000]))
build('prototype_comparison',comparison,'Perbandingan skenario fiktif: kedua cara melayani 18 permintaan; perjalanan maju diasumsikan tetap berlangsung.')

risk_appendix=next(a for a in json.loads((ROOT/'production/appendix_content.json').read_text()) if a['id']=='J.1')
risk_rows=risk_appendix['tables'][0]['rows']
import re
risk_cells={}
risk_codes=[]
for row in risk_rows:
 code,title,initial,target,owner=row
 match=re.fullmatch(r'(\d+)\s*×\s*(\d+)\s*=\s*(\d+)',initial)
 if not match:raise ValueError('Unrecognized risk rating: '+initial)
 likelihood,impact,score=map(int,match.groups())
 assert likelihood*impact==score and 1<=likelihood<=5 and 1<=impact<=5
 risk_cells.setdefault((likelihood,impact),[]).append(code)
 risk_codes.append(code)
risk_tex=r'\begin{tikzpicture}[x=1.30cm,y=1.15cm]'+'\n'
for likelihood in range(1,6):
 for impact in range(1,6):
  score=likelihood*impact
  col='forest!12' if score<=4 else 'sand' if score<=9 else 'clay!20' if score<=16 else 'clay!35'
  risk_tex+=r'\fill['+col+f']({likelihood-1},{impact-1})rectangle({likelihood},{impact});'+r'\draw[white,line width=1pt]'+f'({likelihood-1},{impact-1})rectangle({likelihood},{impact});\n'
risk_tex+=r'''\foreach\n in{1,...,5}{\node[font=\fontsize{10}{11}\selectfont]at(\n-.5,-.25){\n};\node[font=\fontsize{10}{11}\selectfont]at(-.25,\n-.5){\n};}
\node[font=\fontsize{11}{12}\selectfont]at(2.5,-.75){Kemungkinan};\node[font=\fontsize{11}{12}\selectfont,rotate=90]at(-.85,2.5){Dampak};
'''
for (likelihood,impact),codes in risk_cells.items():
 label=', '.join(codes) if len(codes)<3 else ', '.join(codes[:2])+r'\\'+', '.join(codes[2:])
 risk_tex+=r'\node[align=center,font=\fontsize{10}{11}\selectfont]at('+str(likelihood-.5)+','+str(impact-.5)+'){'+label+'};\n'
legend=r'\\'.join(code+r'\quad '+title.replace('&',r'\&') for code,title,*rest in risk_rows)
risk_tex+=r'\node[anchor=north west,font=\fontsize{10}{12}\selectfont,text width=7cm]at(5.5,4.9){'+legend+'};\n'
risk_tex+=r'\end{tikzpicture}'
assert len(risk_rows)==10 and set(risk_codes)==set('R'+str(i) for i in range(1,11))
build('risk_heatmap',risk_tex,'Sepuluh risiko inheren, kode dan penilaian persis dari Lampiran J.1; skala ordinal estimasi tim, dengan sasaran pengendalian dalam tabel pendamping.')

old=json.loads((OUT/'manifest.json').read_text()) if (OUT/'manifest.json').exists() else []
(OUT/'manifest.json').write_text(json.dumps(list({item['name']:item for item in old+manifest}.values()),ensure_ascii=False,indent=2))
