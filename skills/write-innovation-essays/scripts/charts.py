#!/usr/bin/env python3
"""Data-driven TikZ/PGFPlots figures. Python stdlib; XeLaTeX/LuaLaTeX; pdftoppm.

Examples contain illustrative team assumptions, never empirical findings.
Run --help. Text is escaped and TeX shell escape is disabled.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

TYPES = ('issue_tree', 'service_flow', 'tam_sam_som', 'gantt', 'risk_heatmap',
         'bar_comparison', 'cash_line', 'distribution', 'drivers',
         'structure_tree', 'positioning', 'value_proposition')
COLORS = {'forest': '346E57', 'sage': 'E8EFEA', 'clay': 'B77E60',
          'gray': '718078', 'rule': 'B7C3BA', 'ink': '000000'}

def atomic_bytes(path,data):
    path=Path(path)
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.'+path.name,suffix='.tmp',delete=False)as f:
        f.write(data);temporary=Path(f.name)
    try:temporary.replace(path)
    finally:temporary.unlink(missing_ok=True)

def valid_png(data):
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Invalid PNG signature')
    cursor=8;compressed=[];ended=False
    while cursor+12<=len(data):
        length=struct.unpack('>I',data[cursor:cursor+4])[0];kind=data[cursor+4:cursor+8]
        payload=data[cursor+8:cursor+8+length];crc=data[cursor+8+length:cursor+12+length]
        if len(payload)!=length or len(crc)!=4:raise ValueError('Truncated PNG chunk')
        if zlib.crc32(kind+payload)&0xffffffff!=struct.unpack('>I',crc)[0]:raise ValueError('PNG chunk CRC failed')
        if kind==b'IDAT':compressed.append(payload)
        cursor+=12+length
        if kind==b'IEND':ended=True;break
    if not ended or not compressed:raise ValueError('PNG is missing complete image data or IEND')
    zlib.decompress(b''.join(compressed))

def text(value):
    """Literal label, not arbitrary TeX; retain Unicode under LuaLaTeX."""
    source = str(value)
    replacements = {'\\': r'\textbackslash{}', '{': r'\{', '}': r'\}',
                    '$': r'\$', '&': r'\&', '#': r'\#', '_': r'\_',
                    '%': r'\%', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(replacements.get(c, r'\\' if c == '\n' else c) for c in source)

def number(value, name='value'):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number, not {value!r}')
    return float(value)

def integer(value,name='value'):
    result=number(value,name)
    if not result.is_integer():raise ValueError(name+' must be an integer')
    return int(result)

def arr(values, name='values'):
    if not isinstance(values, list) or not values:
        raise ValueError(f'{name} must be a nonempty list')
    return [number(v, name) for v in values]

def header(spec):
    font = spec.get('font', 'Latin Modern Roman')
    if not isinstance(font,str) or not re.fullmatch(r"[\w .,'+\-]+", font):
        raise ValueError('font must be a plain installed font-family name')
    pt = number(spec.get('font_pt', 10), 'font_pt')
    if not 7 <= pt <= 18: raise ValueError('font_pt must be between 7 and 18')
    width = number(spec.get('width_cm', 16), 'width_cm')
    if not 6 <= width <= 26: raise ValueError('width_cm must be 6–26')
    if 'height_cm'in spec and not 2<=number(spec['height_cm'],'height_cm')<=24:raise ValueError('height_cm must be 2–24')
    if not isinstance(spec.get('colors',{}),dict):raise ValueError('colors must be a name-to-hex object')
    colors = COLORS | spec.get('colors', {})
    if any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9]*',k)for k in colors):raise ValueError('Color names must be simple alphabetic identifiers')
    if any(not re.fullmatch(r'[0-9A-Fa-f]{6}', v) for v in colors.values()):
        raise ValueError('colors must be six-digit HTML hex values without #')
    definitions = '\n'.join(r'\definecolor{%s}{HTML}{%s}' % (k, v) for k, v in colors.items())
    return (r'''\documentclass[border=3pt]{standalone}
\usepackage{fontspec}
\setmainfont{''' + font + r'''}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usetikzlibrary{arrows.meta,calc,positioning,shapes.geometric}
''' + definitions + r'''
\begin{document}
\hyphenpenalty=10000\exhyphenpenalty=10000
\fontsize{''' + f'{pt:g}' + r'''}{''' + f'{pt*1.2:g}' + r'''}\selectfont
\renewcommand{\small}{\fontsize{''' + f'{pt*.9:g}' + r'''}{''' + f'{pt*1.1:g}' + r'''}\selectfont}
\renewcommand{\scriptsize}{\fontsize{''' + f'{pt*.8:g}' + r'''}{''' + f'{pt:g}' + r'''}\selectfont}
''')

def wrap_tikz(body, width):
    return r'\resizebox{' + f'{width:g}' + r'cm}{!}{%' + '\n' + body + '\n}\n'

def issue_tree(spec):
    branches = spec['branches']
    if not isinstance(branches, list) or not branches: raise ValueError('branches must be nonempty')
    rows, groups, issues = [], [], []
    for bi, branch in enumerate(branches):
        start = len(rows)
        for ii, issue in enumerate(branch['issues']):
            istart = len(rows)
            for cause in issue['causes']:
                if isinstance(cause, str): cause = {'text': cause}
                label = cause['text'] + ('\n' + cause['citation'] if cause.get('citation') else '')
                rows.append((bi, ii, label))
            if len(rows) == istart: raise ValueError('Every issue needs a cause')
            issues.append((bi, ii, istart, len(rows)-1, issue['issue']))
        if len(rows) == start: raise ValueError('Every branch needs an issue')
        groups.append((bi, start, len(rows)-1, branch['subproblem']))
    if len(rows)>12: raise ValueError('Split issue trees with more than 12 leaves into linked exhibits')
    heights = [max(1.5, .40 * math.ceil(len(label)/43) + .38) for _,_,label in rows]
    ys=[]; cursor=0
    for height in heights: ys.append(-cursor-height/2);cursor += height+.16
    mid=(ys[0]+ys[-1])/2
    lines=[r'\begin{tikzpicture}[x=1cm,y=1cm,box/.style={draw=rule,line width=.45pt,fill=white,align=center,inner sep=5pt},edge/.style={draw=forest,line width=.6pt}]']
    for x,w,label in [(1.0,1.8,spec.get('goal_label','Tujuan / masalah')),(3.5,2.1,spec.get('subproblem_label','Submasalah')),(6.4,2.4,spec.get('issue_label','Isu')),(11.5,6.4,spec.get('cause_label','Akar penyebab'))]:
        lines.append(r'\node[fill=sage,text width=%scm,minimum height=.85cm,align=center,inner sep=5pt,font=\bfseries] at (%s,.52) {%s};' % (w,x,text(label)))
    lines.append(r'\node[box,text width=1.8cm] (goal) at (1,%s) {%s};' % (mid,text(spec['goal'])))
    for bi,start,end,label in groups:
        y=(ys[start]+ys[end])/2
        lines.append(r'\node[box,text width=2.1cm] (b%s) at (3.5,%s) {%s};' % (bi,y,text(label)))
        lines.append(r'\draw[edge] (goal.east) -- ++(.22,0) |- (b%s.west);' % bi)
    for bi,ii,start,end,label in issues:
        y=(ys[start]+ys[end])/2
        lines.append(r'\node[box,text width=2.4cm] (i%sx%s) at (6.4,%s) {%s};' % (bi,ii,y,text(label)))
        lines.append(r'\draw[edge] (b%s.east) -- ++(.22,0) |- (i%sx%s.west);' % (bi,bi,ii))
    for ri,(bi,ii,label) in enumerate(rows):
        lines.append(r'\node[box,text width=6.4cm,align=left,minimum height=%scm] (c%s) at (11.5,%s) {%s};' % (heights[ri],ri,ys[ri],text(label)))
        lines.append(r'\draw[edge] (i%sx%s.east) -- ++(.35,0) |- (c%s.west);' % (bi,ii,ri))
    lines.append(r'\end{tikzpicture}')
    return wrap_tikz('\n'.join(lines),spec.get('width_cm',16)), {'leaf_count':len(rows)}

def service_flow(spec):
    stages=spec['stages']
    if len(stages)!=6: raise ValueError('service_flow requires six stages; split longer operating procedures')
    coords=[(0,0),(5,0),(10,0),(10,-2.2),(5,-2.2),(0,-2.2)]
    lines=[r'\begin{tikzpicture}[box/.style={draw=rule,line width=.5pt,fill=sage,rounded corners=1pt,text width=3.55cm,minimum height=1.1cm,align=center,inner sep=6pt},edge/.style={-{Latex[length=2.2mm]},draw=forest,line width=.7pt}]']
    for i,(label,(x,y)) in enumerate(zip(stages,coords)):
        lines.append(r'\node[box] (s%s) at (%s,%s) {\textbf{%s}\par %s};' % (i,x,y,i+1,text(label)))
    for i in range(5):lines.append(r'\draw[edge] (s%s) -- (s%s);' % (i,i+1))
    exception_from=integer(spec.get('exception_from',4),'exception_from')-1
    if not 0<=exception_from<=5:raise ValueError('exception_from must be 1–6')
    if spec.get('exception_label'):
        lines.append(r'\node[draw=clay,fill=white,text width=9cm,align=center,inner sep=7pt] (held) at (5,-4.4) {%s};' % text(spec['exception_label']))
        lines.append(r'\draw[edge,draw=clay] (s%s.south) -- ++(0,-.35) -| (held.north);' % exception_from)
        if spec.get('resume_label'):
            lines.append(r'\draw[edge,dashed] (held.west) -- ++(-3,0) |- node[pos=.25,left,text width=2.3cm,align=left] {%s} (s0.west);' % text(spec['resume_label']))
    lines.append(r'\end{tikzpicture}')
    return wrap_tikz('\n'.join(lines),spec.get('width_cm',16)),{}

def tam_sam_som(spec):
    levels=spec['levels']
    if len(levels)!=3 or spec.get('schematic') is not True:raise ValueError('Three levels and schematic:true required; circles do not encode area-proportional market size')
    lines=[r'\begin{tikzpicture}[x=1cm,y=1cm]']
    for (level,cy,r,color) in zip(levels,[0,-.85,-1.7],[3.1,2.25,1.4],['forest!82','forest!42','sage']):
        lines.append(r'\fill[%s] (0,%s) circle (%s);' % (color,cy,r))
    for i,(level,y) in enumerate(zip(levels,[2.05,.42,-1.65])):
        lines.append(r'\node[align=center,font=\bfseries,text=%s] at (0,%s) {%s\\%s};' % ('white'if i==0 else'ink',y,text(level['label']),text(level['value'])))
        lines.append(r'\draw[rule,line width=.55pt] (%s,%s) -- (4.15,%s);' % ([2.35,2.1,1.2][i],y,y))
        lines.append(r'\node[anchor=west,align=left,text width=7cm,inner sep=0] at (4.35,%s) {\textbf{%s}\par %s};' % (y,text(level['description']),text(level.get('basis',''))))
    lines.append(r'\end{tikzpicture}')
    return wrap_tikz('\n'.join(lines),spec.get('width_cm',16)),{'schematic':True,'area_proportional':False}

def gantt(spec):
    periods=spec['periods'];tasks=spec['tasks'];n=len(periods)
    if not 2<=n<=24 or not tasks:raise ValueError('Gantt requires 2–24 periods and at least one task')
    step=10.6/n
    lines=[r'\begin{tikzpicture}[x=1cm,y=1cm]']
    # Each following label is positioned below the actual previous text box,
    # so ordinary three-line Indonesian task labels cannot overlap a fixed row.
    for i,task in enumerate(tasks):
        start=integer(task['start'],'start');end=integer(task['end'],'end')
        if not 1<=start<=end<=n:raise ValueError('Gantt start/end must be inclusive 1-based periods')
        location='(-.22,0)'if i==0 else'($(task%s.south east)+(0,-.18)$)'%(i-1)
        lines.append(r'\node[anchor=north east,text width=4.9cm,align=right,inner sep=2pt] (task%s) at %s {%s};'%(i,location,text(task['label'])))
        lines.append(r'\coordinate (row%s) at (0,0 |- task%s.center);'%(i,i))
        lines.append(r'\fill[%s] ($(row%s)+(%s,-.13)$) rectangle ($(row%s)+(%s,.13)$);'%('clay'if task.get('critical')else'forest!70',i,(start-1)*step+.025,i,end*step-.025))
    lines.append(r'\coordinate (gridBottom) at ($(task%s.south)+(0,-.16)$);'%(len(tasks)-1))
    for j,label in enumerate(periods):
        lines.append(r'\node[font=\small,text width=%scm,align=center,anchor=south] at (%s,.18) {%s};'%(step-.08,(j+.5)*step,text(label)))
        lines.append(r'\draw[rule!50,line width=.3pt] (%s,.1) -- (%s,0 |- gridBottom);'%(j*step,j*step))
    lines.append(r'\draw[rule!50,line width=.3pt] (10.6,.1) -- (10.6,0 |- gridBottom);')
    lines.append(r'\end{tikzpicture}')
    return wrap_tikz('\n'.join(lines),spec.get('width_cm',16)),{'periods':n,'tasks':len(tasks),'intervals':'1-based inclusive','row_heights':'actual wrapped label bounding boxes'}

def risk_heatmap(spec):
    bins={}
    for item in spec['risks']:
        p=integer(item['probability'],'probability');impact=integer(item['impact'],'impact')
        if not 1<=p<=5 or not 1<=impact<=5:raise ValueError('risk probability/impact must be 1–5')
        bins.setdefault((impact,p),[]).append(str(item['id']))
    lines=[r'\begin{tikzpicture}[x=1.1cm,y=1.1cm]']
    for p in range(1,6):
        for impact in range(1,6):
            score=p*impact;color='clay!'+str(round(8+score*1.6)) if score>=12 else 'forest!'+str(round(5+score*1.3))
            lines.append(r'\filldraw[fill=%s,draw=white,line width=.6pt] (%s,%s) rectangle (%s,%s);' % (color,impact-1,p-1,impact,p))
            labels=', '.join(bins.get((impact,p),[]))
            if len(labels)>30:raise ValueError('Too many risk IDs in one cell; use a linked register')
            if labels:lines.append(r'\node[align=center,text width=.95cm,font=\small] at (%s,%s) {%s};' % (impact-.5,p-.5,text(labels)))
    for v in range(1,6):
        lines.append(r'\node at (%s,-.25) {%s};' % (v-.5,v))
        lines.append(r'\node at (-.25,%s) {%s};' % (v-.5,v))
    lines.extend([r'\node at (2.5,-.8) {%s};'%text(spec.get('x_label','Dampak')),r'\node[rotate=90] at (-.85,2.5) {%s};'%text(spec.get('y_label','Kemungkinan'))])
    if spec.get('legend'):
        lines.append(r'\node[anchor=west,align=left,text width=6.8cm] at (5.6,2.5) {%s};' % text(spec['legend']))
    lines.append(r'\end{tikzpicture}')
    return wrap_tikz('\n'.join(lines),spec.get('width_cm',14)),{'positions':'input ordinal scores, not calibrated probabilities'}

def axis_base(spec,height=6,left_reserve=0):
    width=number(spec.get('width_cm',16))
    if left_reserve:
        width-=left_reserve
        if width<3:raise ValueError('This labelled plot needs a wider chart or shorter category labels')
    return r'\begin{tikzpicture}\begin{axis}[' + f'width={width:g}cm,height={spec.get("height_cm",height):g}cm,' + ('scale only axis=true,\n'if left_reserve else'scale only axis=false,\n') + r'''axis lines=left,axis line style={draw=rule},tick style={draw=rule},
tick label style={font=\small},label style={font=\small},
grid=major,grid style={draw=rule!35,line width=.3pt},
legend style={draw=none,fill=none,font=\small,at={(.5,-.26)},anchor=north},legend columns=-1,
'''

def ticklabels(labels):return ','.join('{'+text(x)+'}'for x in labels)

def coordinates(values):return ' '.join(f'({x:g},{y:g})'for x,y in values)

def bar_comparison(spec):
    labels=spec['categories'];series=spec['series']
    if not labels or len(series)>4 or not series:raise ValueError('Bar comparison needs labels and 1–4 series')
    ys=list(range(len(labels)))
    all_values=[v for s in series for v in arr(s['values'])]
    xmin=min(0,min(all_values))*1.15;xmax=max(0,max(all_values))*1.18
    if xmin==xmax:xmax=xmin+1
    lines=[axis_base(spec,max(3,len(labels)*.65+1.3),5.4)+r'xbar,bar width=9pt,xmin='+f'{xmin:g}'+r',xmax='+f'{xmax:g}'+r',enlarge y limits=.3,y dir=reverse,ytick={'+','.join(map(str,ys))+r'},yticklabels={'+ticklabels(labels)+r'},yticklabel style={text width=4.6cm,align=right},xlabel={'+text(spec.get('x_label',''))+r'},ymajorgrids=false,nodes near coords,point meta=x,nodes near coords align={horizontal},every node near coord/.append style={font=\small,text=ink},]']
    for i,s in enumerate(series):
        vals=arr(s['values'])
        if len(vals)!=len(labels):raise ValueError('Every series must match category count')
        lines.append(r'\addplot[draw=none,fill=%s] coordinates {%s};'%(['forest!80','clay!75','forest!40','gray!60'][i],coordinates(zip(vals,ys))))
        if len(series)>1:lines.append(r'\addlegendentry{%s}'%text(s['label']))
    lines.append(r'\end{axis}\end{tikzpicture}')
    return '\n'.join(lines),{}

def cash_line(spec):
    xs=arr(spec['periods'],'periods');series=spec['series']
    if len(xs)<2 or any(a>=b for a,b in zip(xs,xs[1:])):raise ValueError('periods must be strictly increasing numeric positions')
    if not 1<=len(series)<=4:raise ValueError('Use 1–4 line series')
    lines=[axis_base(spec,7)+r'xlabel={'+text(spec.get('x_label','Bulan'))+r'},ylabel={'+text(spec.get('y_label','Juta Rp'))+r'},]']
    for i,s in enumerate(series):
        vals=arr(s['values'])
        if len(vals)!=len(xs):raise ValueError('Each line series must match period count')
        lines.append(r'\addplot+[mark=none,color=%s,line width=.85pt] coordinates {%s};'%(['forest','clay','gray','forest!50'][i],coordinates(zip(xs,vals))))
        lines.append(r'\addlegendentry{%s}'%text(s['label']))
    lines.append(r'\end{axis}\end{tikzpicture}')
    return '\n'.join(lines),{}

def percentile(values,p):
    position=(len(values)-1)*p/100;lo=math.floor(position);hi=math.ceil(position)
    return values[lo]+(values[hi]-values[lo])*(position-lo)

def distribution(spec):
    vals=sorted(arr(spec['values']));n=integer(spec.get('bins',20),'bins')
    if not 4<=n<=60:raise ValueError('bins must be 4–60')
    lo,hi=vals[0],vals[-1]
    if lo==hi:lo-=max(1,abs(lo)*.1);hi+=max(1,abs(hi)*.1)
    step=(hi-lo)/n;counts=[0]*n
    for v in vals:counts[min(n-1,int((v-lo)/step))]+=1
    points=[(lo+(i+.5)*step,c)for i,c in enumerate(counts)]
    q={str(p):percentile(vals,p)for p in [10,50,90]}
    lines=[axis_base(spec,6)+r'ybar,bar width='+f'{step:g}'+r',xlabel={'+text(spec.get('x_label','Nilai'))+r'},ylabel={'+text(spec.get('y_label','Frekuensi'))+r'},ymin=0,ymajorgrids=true,xmajorgrids=false,]']
    # ybar uses axis-relative width only through coordinates; area remains counts.
    lines.append(r'\addplot+[ybar interval,mark=none,fill=forest!65,draw=white] coordinates {'+coordinates([(lo+i*step,c)for i,c in enumerate(counts)]+[(hi,0)])+'};')
    if spec.get('show_quantiles',True):
        ymax=max(counts)*1.12
        distinct={}
        for label,v in q.items():distinct.setdefault(v,[]).append('P'+label)
        for v,labels in distinct.items():
            lines.append(r'\addplot[sharp plot,gray,dashed,forget plot] coordinates {(%s,0)(%s,%s)};'%(v,v,ymax))
            lines.append(r'\node[anchor=south,rotate=90,font=\scriptsize] at (axis cs:%s,%s) {%s};'%(v,ymax*.72,'/'.join(labels)))
    lines.append(r'\end{axis}\end{tikzpicture}')
    return '\n'.join(lines),{'n':len(vals),'bins':n,'bin_counts':counts,'quantiles_linear':q}

def drivers(spec):
    labels=spec['labels'];values=arr(spec['values'])
    if len(labels)!=len(values):raise ValueError('Driver labels and values must match')
    if any(abs(v)>1 for v in values):raise ValueError('Spearman driver associations must be −1…1')
    ys=list(range(len(labels)))
    lines=[axis_base(spec,max(4,len(labels)*.62+.6),5.0)+r'xbar,bar shift=0pt,xmin=-1,xmax=1,bar width=10pt,ytick={'+','.join(map(str,ys))+r'},yticklabels={'+ticklabels(labels)+r'},yticklabel style={text width=4.2cm,align=right},y dir=reverse,enlarge y limits=.18,xlabel={'+text(spec.get('x_label','Spearman ρ'))+r'},ymajorgrids=false,]']
    for sign,color in [(1,'forest!75'),(-1,'clay!75')]:
        coords=[(v,y)for y,v in enumerate(values)if(v>=0)==(sign==1)]
        if coords:lines.append(r'\addplot+[draw=none,fill=%s] coordinates {%s};'%(color,coordinates(coords)))
    lines.append(r'\end{axis}\end{tikzpicture}')
    return '\n'.join(lines),{'interpretation':'rank association, not causal effect'}

def structure_tree(spec):
    nodes=spec['nodes']
    if not 2<=len(nodes)<=20:raise ValueError('Structure tree supports 2–20 nodes')
    byid={str(n['id']):n for n in nodes}
    if len(byid)!=len(nodes):raise ValueError('Structure node IDs must be unique')
    roots=[str(n['id'])for n in nodes if n.get('parent')is None]
    if len(roots)!=1:raise ValueError('Structure tree needs exactly one root')
    children={k:[]for k in byid}
    for n in nodes:
        if n.get('parent')is not None:
            parent=str(n['parent'])
            if parent not in byid:raise ValueError('Unknown structure parent '+parent)
            children[parent].append(str(n['id']))
    positions={};visiting=set();leaf_count=0
    def visit(key,depth):
        nonlocal leaf_count
        if key in visiting:raise ValueError('Cycle in structure tree')
        if depth>4:raise ValueError('Split structure trees deeper than four levels')
        visiting.add(key)
        if children[key]:
            xs=[visit(c,depth+1)for c in children[key]];x=sum(xs)/len(xs)
        else:x=leaf_count*2.75;leaf_count+=1
        positions[key]=(x,-depth*2.05);visiting.remove(key);return x
    visit(roots[0],0)
    if len(positions)!=len(nodes):raise ValueError('Disconnected or cyclic structure node')
    if leaf_count>6:raise ValueError('Split structure trees with more than six leaves')
    ordinal={key:i for i,key in enumerate(byid)}
    lines=[r'\begin{tikzpicture}[box/.style={draw=rule,fill=sage,text width=2.15cm,minimum height=1.05cm,align=center,inner sep=5pt},edge/.style={draw=forest,line width=.65pt}]']
    for n in nodes:
        if n.get('parent')is None:continue
        parent=str(n['parent']);key=str(n['id']);px,py=positions[parent];x,y=positions[key]
        lines.append(r'\draw[edge] (%s,%s) -- (%s,%s) -| (%s,%s);'%(px,py-.6,px,(py+y)/2,x,y+.6))
    for key,(x,y)in positions.items():
        lines.append(r'\node[box%s] at (%s,%s) {%s};'%(r',fill=forest!20,font=\bfseries'if key==roots[0]else'',x,y,text(byid[key]['label'])))
    lines.append(r'\end{tikzpicture}')
    return wrap_tikz('\n'.join(lines),spec.get('width_cm',16)),{'nodes':len(nodes),'leaves':leaf_count}

def positioning(spec):
    points=spec['points']
    if not 1<=len(points)<=12:raise ValueError('Positioning supports 1–12 labelled points')
    lines=[r'\begin{tikzpicture}[x=5cm,y=2.7cm,axis/.style={-{Latex[length=2.2mm]},draw=rule,line width=.7pt}]',r'\draw[axis] (-1.05,0)--(1.08,0);',r'\draw[axis] (0,-1.05)--(0,1.08);']
    for pos,label,anchor in [((-1.10,0),spec['x_low'],'east'),((1.13,0),spec['x_high'],'west'),((0,1.13),spec['y_high'],'south'),((0,-1.13),spec['y_low'],'north')]:
        lines.append(r'\node[anchor=%s,text width=2.4cm,align=center] at (%s,%s) {%s};'%(anchor,*pos,text(label)))
    for item in points:
        x=number(item['x']);y=number(item['y'])
        if abs(x)>1 or abs(y)>1:raise ValueError('Positioning x/y use normalized −1…1 coordinates')
        dx=number(item.get('label_dx',0));dy=number(item.get('label_dy',.12))
        lines.append(r'\fill[forest] (%s,%s) circle[radius=1.4pt];'%(x,y))
        lines.append(r'\node[align=center,text width=2.6cm,anchor=south] at (%s,%s) {%s};'%(x+dx,y+dy,text(item['label'])))
    lines.append(r'\end{tikzpicture}')
    return wrap_tikz('\n'.join(lines),spec.get('width_cm',16)),{'coordinates':'team assessment in normalized space; not a measured rank unless independently evidenced'}

def value_proposition(spec):
    def listing(values):
        if not isinstance(values,list)or not 1<=len(values)<=5:raise ValueError('Canvas lists need 1–5 concise items')
        if sum(len(str(v))for v in values)>330:raise ValueError('Canvas list too dense; shorten or split the exhibit')
        return r'\par\smallskip '.join(text(v)for v in values)
    left=spec['left'];right=spec['right'];offer=spec['offer']
    pt=number(spec.get('font_pt',10))
    cards=[(left['gains'],2.65),(left['pains'],2.65),(right['gains'],2.65),(right['pains'],2.65),(offer['gain_creators'],2.9),(offer['pain_relievers'],2.9)]
    cardheight=max(2.8,max((sum(math.ceil((len(str(v))+2)/max(10,int(w*28.35/(pt*.50))))for v in values)+2)*pt*1.2/28.35+.55 for values,w in cards))
    if cardheight>4.8:raise ValueError('Canvas too dense for this physical width; shorten lists or split the exhibit')
    yc=cardheight/2+.13;heady=cardheight+.85;jobheight=2*cardheight+.26
    lines=[r'\begin{tikzpicture}[x=1cm,y=1cm,box/.style={draw=rule,fill=white,rounded corners=1pt,align=left,inner sep=5pt},head/.style={align=center,font=\bfseries}]']
    for x,label in [(0,left['name']),(3.15,left.get('needs_heading','Kebutuhan')),(6.95,offer['name']),(10.75,right.get('needs_heading','Kebutuhan')),(13.9,right['name'])]:
        lines.append(r'\node[head,text width=2.7cm]at(%s,%s){%s};'%(x,heady,text(label)))
    for x,side in [(0,left),(13.9,right)]:
        lines.append(r'\node[box,text width=2.15cm,minimum height=%scm] at(%s,0){\textbf{%s}\par\smallskip %s};'%(jobheight,x,text(side.get('jobs_heading','Pekerjaan')),listing(side['jobs'])))
    for x,side,prefix in [(3.15,left,'left'),(10.75,right,'right')]:
        for y,key,title in [(yc,'gains',side.get('gains_heading','Manfaat')),(-yc,'pains',side.get('pains_heading','Hambatan'))]:
            lines.append(r'\node[box,text width=2.65cm,minimum height=%scm] (%s%s) at(%s,%s){\textbf{%s}\par\smallskip %s};'%(cardheight,prefix,key,x,y,text(title),listing(side[key])))
    for y,key,title in [(yc,'gain_creators',offer.get('gain_heading','Pencipta manfaat')),(-yc,'pain_relievers',offer.get('pain_heading','Pengurai hambatan'))]:
        lines.append(r'\node[box,fill=sage,text width=2.9cm,minimum height=%scm] (%s)at(6.95,%s){\textbf{%s}\par\smallskip %s};'%(cardheight,key,y,text(title),listing(offer[key])))
    for centre,key in [('gain_creators','gains'),('pain_relievers','pains')]:
        lines.append(r'\draw[-{Latex[length=1.8mm]},forest,line width=.6pt](%s.west)--(left%s.east);'%(centre,key))
        lines.append(r'\draw[-{Latex[length=1.8mm]},forest,line width=.6pt](%s.east)--(right%s.west);'%(centre,key))
    lines.append(r'\end{tikzpicture}')
    return wrap_tikz('\n'.join(lines),spec.get('width_cm',16)),{}

RENDERERS={k:globals()[k]for k in TYPES}

def self_test():
    """Regression checks for data/escaping/export failures that matter to a chart."""
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    def rejects(name,callback):
        try:callback()
        except (ValueError,RuntimeError):checks.append(name);return
        raise AssertionError(name)
    check('literal TeX-sensitive labels',text('A & B_1: 20%')==r'A \& B\_1: 20\%')
    rejects('nonfinite input rejected',lambda:number(float('nan')))
    rejects('fractional ordinal score rejected',lambda:risk_heatmap({'risks':[{'id':'R1','probability':2.5,'impact':4}]}))
    _,meta=distribution({'values':[0,10,20,30,40],'bins':4})
    check('histogram preserves all observations',sum(meta['bin_counts'])==5 and meta['bin_counts']==[1,1,1,2])
    check('linear quantiles agree with known sample',meta['quantiles_linear']=={'10':4.0,'50':20.0,'90':36.0})
    check('quantile overlays are lines rather than inherited histogram bars',r'\addplot[sharp plot,gray,dashed,forget plot]'in distribution({'values':[0,10,20,30,40],'bins':4})[0])
    check('identical quantiles share one label','P10/P50/P90'in distribution({'values':[5,5,5,5],'bins':4})[0])
    source,_=bar_comparison({'categories':['A','B'],'series':[{'label':'x','values':[30,115]}]})
    check('positive bars retain zero baseline','xmin=0,'in source and '(30,0)'in source)
    rejects('series-length mismatch rejected',lambda:cash_line({'periods':[1,2],'series':[{'label':'x','values':[3]}]}))
    rejects('reversed time axis rejected',lambda:cash_line({'periods':[2,1],'series':[{'label':'x','values':[3,4]}]}))
    rejects('Gantt out-of-range end rejected',lambda:gantt({'periods':['1','2'],'tasks':[{'label':'x','start':1,'end':3}]}))
    rejects('structure unknown parent rejected',lambda:structure_tree({'nodes':[{'id':'a','label':'a','parent':None},{'id':'b','label':'b','parent':'missing'}]}))
    def chunk(kind,payload):return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0\0\0\0'))+chunk(b'IEND',b'')
    valid_png(png);check('complete PNG accepted',True)
    rejects('truncated PNG rejected',lambda:valid_png(png[:-8]))
    return {'status':'passed','checks':checks,'scope':'Pure data/escaping/PNG regression checks; not a TeX render or editorial proof.'}

def render(spec_path,out_dir,font=None,tex_only=False,dpi=200,engine='auto'):
    spec_path=Path(spec_path);spec=json.loads(spec_path.read_text(encoding='utf-8'))
    if not isinstance(spec,dict):raise ValueError('Chart specification must be a JSON object')
    kind=spec.get('type')
    if kind not in RENDERERS:raise ValueError('type must be one of '+', '.join(TYPES))
    if font:spec['font']=font
    name=spec.get('id',spec_path.stem)
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}',name):raise ValueError('id must be a simple filename stem')
    intro=header(spec);figure,meta=RENDERERS[kind](spec)
    source=intro+figure+'\n\\end{document}\n'
    output=Path(out_dir);output.mkdir(parents=True,exist_ok=True)
    tex=output/(name+'.tex')
    result={'id':name,'type':kind,'tex':str(tex),'input_sha256':hashlib.sha256(spec_path.read_bytes()).hexdigest(),'font':spec.get('font','Latin Modern Roman'),'width_cm':spec.get('width_cm',16),'font_pt':spec.get('font_pt',10),'data_summary':meta,'example_status':spec.get('example_status'),'source_note':spec.get('source_note')}
    if tex_only:
        atomic_bytes(tex,source.encode('utf-8'))
        result['render_status']='source_only'
        result['existing_rendered_outputs_not_updated']=[str(output/(name+ext))for ext in ['.pdf','.png']if(output/(name+ext)).exists()]
    else:
        selected_engine=next((e for e in ['xelatex','lualatex']if shutil.which(e)),None)if engine=='auto'else engine
        if not selected_engine or not shutil.which(selected_engine):raise RuntimeError('XeLaTeX/LuaLaTeX unavailable. Install TeX Live with fontspec, standalone, TikZ and PGFPlots, or use --tex-only; no PDF/PNG was rendered.')
        with tempfile.TemporaryDirectory(prefix='chart-render-')as temporary:
            stage=Path(temporary);candidate=stage/(name+'.tex');candidate.write_text(source,encoding='utf-8')
            command=[selected_engine,'-no-shell-escape','-interaction=nonstopmode','-halt-on-error','-output-directory',str(stage),str(candidate)]
            proc=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
            atomic_bytes(output/(name+'.build.log'),proc.stdout.encode('utf-8'))
            error=None
            if proc.returncode:error=f'{selected_engine} failed; inspect {name}.build.log\n'+proc.stdout[-2200:]
            elif 'Missing character:' in proc.stdout:error=f'Missing font glyph; inspect {name}.build.log'
            overfull=[float(x)for x in re.findall(r'Overfull \\hbox \(([\d.]+)pt too wide\)',proc.stdout)]
            if overfull and max(overfull)>1:error=f'Text exceeds its box by {max(overfull):g}pt; shorten/widen labels or split {name}, then render again'
            if error:
                atomic_bytes(output/(name+'.failed.tex'),source.encode('utf-8'))
                raise RuntimeError(error+'; last successful rendered files were not replaced')
            result['pdf']=str(output/(name+'.pdf'));result['engine']=selected_engine
            result['tex_warnings']=[line for line in proc.stdout.splitlines()if 'Overfull'in line or 'Underfull'in line]
            try:
                import fitz
            except ImportError:fitz=None
            png_data=None
            pdf_path=stage/(name+'.pdf')
            if fitz is not None:
                with fitz.open(pdf_path)as pdf:
                    if len(pdf)!=1:raise RuntimeError('A chart must render as exactly one PDF page')
                    result['pdf_width_cm']=pdf[0].rect.width*2.54/72
                    result['pdf_height_cm']=pdf[0].rect.height*2.54/72
                    spans=[span for block in pdf[0].get_text('dict')['blocks']if 'lines'in block for line in block['lines']for span in line['spans']if span['text'].strip()]
                    if spans:
                        result['pdf_text_fonts']=sorted({span['font']for span in spans})
                        result['pdf_text_sizes_pt']=sorted({round(span['size'],3)for span in spans})
                        result['min_text_pt_at_nominal_width']=min(span['size']for span in spans)*number(spec.get('width_cm',16))/result['pdf_width_cm']
                    png_data=pdf[0].get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72)).tobytes('png')
                result['png_renderer']='PyMuPDF'
            elif shutil.which('pdftoppm'):
                png_data=subprocess.run(['pdftoppm','-png','-r',str(dpi),'-singlefile',str(pdf_path)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60).stdout
                result['png_renderer']='pdftoppm'
            if png_data is not None:valid_png(png_data)
            atomic_bytes(tex,source.encode('utf-8'));atomic_bytes(output/(name+'.pdf'),pdf_path.read_bytes())
            if png_data is not None:
                atomic_bytes(output/(name+'.png'),png_data);result['png']=str(output/(name+'.png'))
            else:result['png_status']='Neither PyMuPDF nor pdftoppm available; PDF rendered, PNG not produced'
            result['render_status']='rendered'
            (output/(name+'.failed.tex')).unlink(missing_ok=True)
    atomic_bytes(output/(name+'.meta.json'),json.dumps(result,ensure_ascii=False,indent=2).encode('utf-8'))
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec',nargs='?',help='JSON specification')
    parser.add_argument('--all',type=Path,help='Render every JSON specification in this directory')
    parser.add_argument('--out-dir',type=Path,default=Path('build/charts'))
    parser.add_argument('--font',help='Explicit installed font override; records it in metadata')
    parser.add_argument('--tex-only',action='store_true',help='Generate source only; do not claim rendered output')
    parser.add_argument('--dpi',type=int,default=200)
    parser.add_argument('--engine',choices=['auto','xelatex','lualatex'],default='auto',help='auto prefers XeLaTeX for fontspec/Unicode; no pdfLaTeX font substitution')
    parser.add_argument('--list',action='store_true')
    parser.add_argument('--self-test',action='store_true',help='Run data/escaping/PNG regression checks without LaTeX')
    args=parser.parse_args(argv)
    if args.list:print('\n'.join(TYPES));return 0
    if args.self_test:
        print(json.dumps(self_test(),ensure_ascii=False,indent=2));return 0
    if not 72<=args.dpi<=600:parser.error('--dpi must be 72–600')
    paths=sorted(args.all.glob('*.json'))if args.all else[Path(args.spec)]if args.spec else[]
    if not paths:parser.error('Supply a JSON specification or --all DIRECTORY')
    results=[]
    try:
        identities=[]
        for path in paths:
            incoming=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(incoming,dict):raise ValueError('Chart specification must be a JSON object')
            identities.append(incoming.get('id',path.stem))
        if len(set(identities))!=len(identities):raise ValueError('Duplicate chart IDs in batch would overwrite an output')
        for path in paths:results.append(render(path,args.out_dir,args.font,args.tex_only,args.dpi,args.engine))
    except (ValueError,TypeError,KeyError,OSError,RuntimeError,subprocess.SubprocessError)as e:
        print('Chart error: '+str(e),file=sys.stderr);return 2
    print(json.dumps(results,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
