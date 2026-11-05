from pathlib import Path
import json,subprocess,sys,numpy as np,csv
ROOT=Path('/workspace/scratch/91cdcc6b9385');OUT=ROOT/'production/assets/figures';SRC=ROOT/'production/figures'
# Reuse common TikZ typography and renderer, without executing the existing plots.
ns={};text=(SRC/'build_figures.py').read_text();exec(text[:text.index("build('main_system'")],ns)
build=ns['build'];data=json.loads((ROOT/'production/finance.json').read_text())
old=json.loads((OUT/'manifest.json').read_text()) if (OUT/'manifest.json').exists() else []

def fmt(n,dec=1):return f'{n:,.{dec}f}'.replace(',','x').replace('.',',').replace('x','.')
market=data['market']
code=r'''\begin{tikzpicture}[x=1cm,y=1cm]
\fill[forest!38](3.1,3.1)circle(3.05);
\fill[forest!18](3.1,2.25)circle(2.2);
\fill[sand](3.1,1.35)circle(1.3);
\node[align=center,font=\fontsize{12}{14}\selectfont]at(3.1,5.2){\textbf{TAM}\\RpTAMVALUE miliar};
\node[align=center,font=\fontsize{12}{14}\selectfont]at(3.1,3.7){\textbf{SAM}\\RpSAMVALUE miliar};
\node[align=center,font=\fontsize{12}{14}\selectfont]at(3.1,1.35){\textbf{SOM}\\RpSOMVALUE juta};
\draw[ink!50](5.15,5.2)--(7.0,5.2);
\draw[ink!50](5.05,3.7)--(7.0,3.7);
\draw[ink!50](4.4,1.35)--(7.0,1.35);
\node[anchor=west,text width=7.2cm,font=\fontsize{11}{13}\selectfont]at(7.2,5.2){\textbf{Pasar perguruan tinggi nasional}\\TAMCOUNT institusi $\times$ satu paket tahunan acuan.};
\node[anchor=west,text width=7.2cm,font=\fontsize{11}{13}\selectfont]at(7.2,3.55){\textbf{Cakupan penawaran Jabodetabek}\\SAMCOUNT program sasaran sebagai estimasi tim.};
\node[anchor=west,text width=7.2cm,font=\fontsize{11}{13}\selectfont]at(7.2,1.35){\textbf{Layanan tahun ketiga}\\SOMMONTHS bulan-kontrak; SOMDEVICES perangkat.\\SOMHOSTS program aktif pada akhir tahun.};
\end{tikzpicture}'''
for token,value in {'TAMVALUE':fmt(market['tam_value']/1e9,2),'SAMVALUE':fmt(market['sam_value']/1e9,2),'SOMVALUE':fmt(market['som_year3_revenue']/1e6,2),'TAMCOUNT':fmt(market['tam_institutions'],0),'SAMCOUNT':str(market['sam_programs']),'SOMMONTHS':str(market['som_year3_hostmonths']),'SOMDEVICES':fmt(market['som_year3_devices'],0),'SOMHOSTS':str(market['closing_hosts_year3'])}.items():code=code.replace(token,value)
build('tam_sam_som',code,'TAM perguruan tinggi, SAM cakupan penawaran tim dan SOM tahun ketiga dari model; ukuran lingkaran skematis.')
annual=data['base']['annual'];revenue=[a['revenue']/1e6 for a in annual];cost=[(a['direct_cost']+a['fixed_cost']+a['onboarding'])/1e6 for a in annual];surplus=[a['ebitda']/1e6 for a in annual]
code=r'''\begin{tikzpicture}\begin{axis}[width=15.8cm,height=7cm,ybar,bar width=17pt,ymin=-90,ymax=800,xtick={2027,2028,2029},xticklabels={2027,2028,2029},xlabel={Tahun},ylabel={Rp juta},axis lines*=left,ymajorgrids=true,grid style={gridgray},legend style={draw=none,at={(.5,1.04)},anchor=south,legend columns=3,font=\fontsize{10}{11}\selectfont},tick label style={font=\fontsize{10}{11}\selectfont},label style={font=\fontsize{11}{12}\selectfont},nodes near coords,nodes near coords style={font=\fontsize{10}{11}\selectfont,text=black},point meta=explicit symbolic]
'''
for vals,col,leg in [(revenue,'forest!60','Pendapatan'),(cost,'black!25','Biaya operasi'),(surplus,'clay!60','Surplus operasi')]:
 code+=r'\addplot[fill='+col+r',draw=none,area legend]coordinates{'+''.join(f'({2027+i},{v:.4f})[{fmt(v)}]' for i,v in enumerate(vals))+r'};\addlegendentry{'+leg+'}\n'
code+=r'\end{axis}\end{tikzpicture}'
build('finance_annual',code,'Pendapatan, biaya dan surplus operasi sebelum pajak dari tiga tahun estimasi tim.')
monthly=data['monthly'];coords=lambda key:''.join(f"({a['month']},{a[key]/1e6:.4f})" for a in monthly)
code=r'''\begin{tikzpicture}\begin{axis}[width=15.8cm,height=7cm,xmin=1,xmax=36,ymin=-110,ymax=460,xtick={1,6,12,18,24,30,36},xlabel={Bulan sejak persiapan},ylabel={Rp juta},axis lines*=left,ymajorgrids=true,grid style={gridgray},legend style={draw=none,at={(.03,.97)},anchor=north west,font=\fontsize{10}{11}\selectfont},tick label style={font=\fontsize{10}{11}\selectfont},label style={font=\fontsize{11}{12}\selectfont}]
'''
for key,col,style,leg in [('closing_financed_cash','forest','thick','Kas dengan pendanaan rencana Rp110 juta'),('closing_unfinanced_cash','black!65','dashed','Kas sebelum pendanaan'),('cash_floor','clay','densely dotted,thick','Cadangan operasi minimum')]:
 code+=r'\addplot[color='+col+','+style+r']coordinates{'+coords(key)+r'};\addlegendentry{'+leg+'}\n'
code+=r'\end{axis}\end{tikzpicture}'
build('finance_cash',code,'Kas sebelum pendanaan dan dengan pendanaan rencana; tidak menyatakan pendanaan sudah berkomitmen.')
labels={'Volume perangkat -20%':'Perangkat -20\%','Volume perangkat +20%':'Perangkat +20\%','Bulan kontrak -20%':'Bulan kontrak -20\%','Bulan kontrak +20%':'Bulan kontrak +20\%','Tarif tetap -15%':'Tarif tetap -15\%','Tarif tetap +15%':'Tarif tetap +15\%','Biaya langsung +20%':'Biaya langsung +20\%','Biaya langsung -20%':'Biaya langsung -20\%','Biaya bersama +15%':'Biaya bersama +15\%','Biaya bersama -15%':'Biaya bersama -15\%','Tagihan perangkat tertunda 2 bulan':'Jeda tagihan 2 bulan'}
ss=sorted(data['sensitivity'],key=lambda x:x['delta_npv']);n=len(ss)
code=r'\begin{tikzpicture}\begin{axis}[width=14cm,height=9cm,xbar,bar width=10pt,xmin=-145,xmax=145,ymin=.3,ymax='+str(n+.7)+r',ytick={'+','.join(str(i+1)for i in range(n))+r'},yticklabels={'+','.join('{'+labels[x['label']]+'}' for x in ss)+r'},xlabel={Perubahan NPV dari dasar (Rp juta)},axis lines*=left,xmajorgrids=true,grid style={gridgray},tick label style={font=\fontsize{10}{11}\selectfont},label style={font=\fontsize{11}{12}\selectfont},nodes near coords,nodes near coords style={font=\fontsize{10}{11}\selectfont,text=black},point meta=explicit symbolic]'+'\n'
for sign,col in [(False,'clay!65'),(True,'forest!65')]:
 code+=r'\addplot[fill='+col+r',draw=none]coordinates{'+''.join(f"({a['delta_npv']/1e6:.4f},{i+1})[{fmt(a['delta_npv']/1e6)}]"for i,a in enumerate(ss)if(a['delta_npv']>=0)==sign)+'};\n'
code+=r'\end{axis}\end{tikzpicture}'
build('finance_sensitivity',code,'Sensitivitas satu input terhadap NPV tiga tahun; dasar perhitungan sama dengan model keuangan.')
rows=list(csv.DictReader((ROOT/'production/finance_mc_draws.csv').open()));print('MC fields',list(rows[0]))
def histogram(name,field,xlabel,zero,job):
 vals=np.array([float(r[field])/1e6 for r in rows]);counts,edges=np.histogram(vals,bins=36);centres=(edges[:-1]+edges[1:])/2
 ymax=max(counts/len(vals)*100)*1.3
 ticks='80,100,120,140,160,180,200,220,240' if zero else '-200,-100,0,100,200,300,400'
 code=r'\begin{tikzpicture}\begin{axis}[width=15.8cm,height=7cm,ybar interval,x tick label as interval=false,xtick={'+ticks+r'},xticklabel style={font=\fontsize{10}{11}\selectfont},yticklabel style={font=\fontsize{10}{11}\selectfont},label style={font=\fontsize{11}{12}\selectfont},xlabel={'+xlabel+r'},ylabel={Frekuensi skenario (\%)},axis lines*=left,ymajorgrids=true,grid style={gridgray},ymin=0,ymax='+str(ymax)+r',legend style={draw=none,at={(.97,.97)},anchor=north east,font=\fontsize{10}{11}\selectfont}]'+'\n'
 code+=r'\addplot[fill=forest!45,draw=white]coordinates{'+''.join(f'({e:.4f},{v:.4f})'for e,v in zip(edges,np.r_[counts/len(vals)*100,0]))+'};\n'
 if zero:
  marker=[(110,'black','densely dashed','Rencana 110,0'),(data['monte_carlo']['required_funding']['p50']/1e6,'forest','thick','P50 '+fmt(data['monte_carlo']['required_funding']['p50']/1e6)),(data['monte_carlo']['required_funding']['p90']/1e6,'clay','thick','P90 '+fmt(data['monte_carlo']['required_funding']['p90']/1e6))]
 else:marker=[(0,'black','densely dashed','NPV nol'),(data['monte_carlo']['npv']['p50']/1e6,'clay','thick','P50 '+fmt(data['monte_carlo']['npv']['p50']/1e6))]
 # Exclude histogram from marker legend with an empty legend placeholder.
 code+=r'\addlegendentry{10.000 skenario}'+'\n'
 for x,col,style,label in marker:
  code+=r'\draw['+col+','+style+r'](axis cs:'+str(x)+',0)--(axis cs:'+str(x)+','+str(ymax)+');\n'
  code+=r'\addlegendimage{line legend,'+col+','+style+'}'+r'\addlegendentry{'+label+'}\n'
 # clean marker descriptors as anchored text below axis; full values remain in native table
 code+=r'\end{axis}\end{tikzpicture}'
 build(name,code,job)
# CSV columns are generated by canonical financial model.
histogram('mc_funding','funding_need_idr','Kebutuhan pendanaan (Rp juta)',True,'Distribusi kebutuhan pendanaan dari 10.000 skenario asumsi tim; garis rencana Rp110 juta, P50 dan P90.')
histogram('mc_npv','npv_idr','NPV tiga tahun (Rp juta)',False,'Distribusi NPV 10.000 skenario asumsi tim; nol dan median ditandai.')
assoc=data['monte_carlo']['rank_associations'];assoc=sorted(assoc,key=lambda x:x['spearman'])
code=r'\begin{tikzpicture}\begin{axis}[width=14cm,height=7cm,xbar,bar width=11pt,xmin=-.62,xmax=1,xtick={-.6,-.4,-.2,0,.2,.4,.6,.8,1},ytick={'+','.join(str(i+1)for i in range(len(assoc)))+r'},yticklabels={'+','.join('{'+a['label']+'}'for a in assoc)+r'},xlabel={Korelasi peringkat Spearman dengan NPV},axis lines*=left,xmajorgrids=true,grid style={gridgray},tick label style={font=\fontsize{10}{11}\selectfont,/pgf/number format/use comma},label style={font=\fontsize{11}{12}\selectfont},nodes near coords,nodes near coords style={font=\fontsize{10}{11}\selectfont,text=black},point meta=explicit symbolic]'+'\n'
for sign,col in [(False,'clay!65'),(True,'forest!65')]:code+=r'\addplot[fill='+col+r',draw=none]coordinates{'+''.join(f"({a['spearman']:.4f},{i+1})[{fmt(a['spearman'],2)}]"for i,a in enumerate(assoc)if(a['spearman']>=0)==sign)+'};\n'
code+=r'\end{axis}\end{tikzpicture}'
build('mc_drivers',code,'Asosiasi peringkat pada skenario yang memiliki faktor bersama; bukan pengaruh sebab-akibat yang teridentifikasi.')
(OUT/'manifest.json').write_text(json.dumps(list({item['name']:item for item in old+ns['manifest']}.values()),ensure_ascii=False,indent=2))
