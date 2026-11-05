"""JejakBalik planning model, constant 2027 IDR; estimates, not observations.
Run with bundled Python. Generates reproducible finance.json, tables and draws.
"""
from pathlib import Path
import json, csv, math
import numpy as np
OUT=Path(__file__).parent
BASE_HOSTS=np.array([0,0,1,1,2,2,3,3,3,4,4,4]+[5]*3+[6]*3+[7]*3+[8]*3+[9]*3+[10]*3+[11]*3+[12]*3,dtype=float)
SEED=20261104
N=10000
CAT={
 'ordinary':dict(label='Biasa',share=.80,fee=45000,transport=15000,handling=12000,review=2000,exceptions=2000),
 'bulky':dict(label='Besar',share=.15,fee=110000,transport=45000,handling=30000,review=3000,exceptions=4000),
 'specialist':dict(label='Khusus',share=.05,fee=190000,transport=60000,handling=70000,review=5000,exceptions=10000),
}
AVG_FEE=sum(c['share']*c['fee'] for c in CAT.values())
AVG_DIRECT=sum(c['share']*sum(c[k] for k in ('transport','handling','review','exceptions')) for c in CAT.values())
SETUP=28000000
DISCOUNT=.12
INITIAL_FUNDING=110000000

def run(host_factor=1., volume_factor=1., retainer_factor=1., fee_factor=1., direct_factor=1., overhead_factor=1., lag=1, retainer_prepaid=1.):
    # Fractional hosts are equivalent contracted host-months in scenarios, not headcounts.
    hosts=BASE_HOSTS*host_factor
    devices=hosts*40*volume_factor
    retainer=hosts*3000000*retainer_factor
    device_rev=devices*AVG_FEE*fee_factor
    revenue=retainer+device_rev
    direct=devices*AVG_DIRECT*direct_factor
    founders=np.full(36,6000000.)
    ops=2000000.*np.maximum(1,np.ceil(hosts/4))
    other=np.full(36,2100000.)
    marketing=np.repeat([1000000.,1200000.,1500000.],12)
    fixed=(founders+ops+other+marketing)*overhead_factor
    additions=np.maximum(0,np.diff(np.r_[0,hosts]))
    onboarding=additions*500000
    expense=direct+fixed+onboarding
    ebitda=revenue-expense
    lag=int(lag)
    received_device=np.r_[np.zeros(lag),device_rev[:36-lag]] if lag else device_rev.copy()
    late_retainer=retainer*(1-retainer_prepaid)
    received_retainer=retainer*retainer_prepaid+np.r_[0,late_retainer[:-1]]
    cashin=received_device+received_retainer
    netcash=cashin-expense
    cumulative=-SETUP+np.cumsum(netcash)
    receivable=np.cumsum(revenue-cashin)
    # Ring-fenced operating cash target: two months fixed + one week direct.
    reserve=2*fixed+direct/4
    funding_gap=np.maximum(0,reserve-cumulative)
    need=float(max(SETUP+reserve[0],funding_gap.max()))
    npv=float(-SETUP+sum(netcash/((1+DISCOUNT)**(np.arange(1,37)/12))))
    payback=next((int(i+1) for i,c in enumerate(cumulative) if c>=0 and np.all(cumulative[i:]>=0)),None)
    contribution=revenue-direct
    workload=80+hosts*8+devices*.2
    funded_hours=150+ops/40000
    assert np.all(workload<=funded_hours), 'Unfunded work capacity'
    return locals()

def clean(v):
    if isinstance(v,np.ndarray): return [clean(x) for x in v]
    if isinstance(v,(np.floating,float)): return round(float(v),6)
    if isinstance(v,(np.integer,int)): return int(v)
    if isinstance(v,dict): return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [clean(x) for x in v]
    return v

def summary(s):
    annual=[]
    for y in range(3):
        a=slice(y*12,(y+1)*12)
        annual.append(dict(year=2027+y,host_months=float(s['hosts'][a].sum()),closing_hosts=float(s['hosts'][(y+1)*12-1]),devices=float(s['devices'][a].sum()),revenue=float(s['revenue'][a].sum()),direct_cost=float(s['direct'][a].sum()),fixed_cost=float(s['fixed'][a].sum()),onboarding=float(s['onboarding'][a].sum()),ebitda=float(s['ebitda'][a].sum()),cashin=float(s['cashin'][a].sum()),net_cash=float(s['netcash'][a].sum()),closing_unfinanced_cash=float(s['cumulative'][(y+1)*12-1]),closing_cash_with_planned_financing=float(INITIAL_FUNDING+s['cumulative'][(y+1)*12-1]),receivables=float(s['receivable'][(y+1)*12-1]),coverage=float(s['revenue'][a].sum()/s['expense'][a].sum()),maximum_funding=float(s['funding_gap'][a].max())))
    return dict(annual=annual,npv=s['npv'],payback_month=s['payback'],required_funding=s['need'],min_financed_cash=float((INITIAL_FUNDING+s['cumulative']).min()),min_cash_reserve_headroom=float((INITIAL_FUNDING+s['cumulative']-s['reserve']).min()),total_revenue=float(s['revenue'].sum()),total_cost=float(s['expense'].sum()),total_devices=float(s['devices'].sum()))
base=run()
down=run(host_factor=.65,volume_factor=.75,retainer_factor=.8,direct_factor=1.2,lag=2,retainer_prepaid=.8)
up=run(host_factor=1.10,volume_factor=1.10,retainer_factor=1.05,direct_factor=.95,lag=1)
# Deterministic one-factor sensitivity, common model and currency boundary.
sens=[]
for name,kwargs in [
 ('Volume perangkat -20%',dict(volume_factor=.8)),('Volume perangkat +20%',dict(volume_factor=1.2)),
 ('Bulan kontrak -20%',dict(host_factor=.8)),('Bulan kontrak +20%',dict(host_factor=1.2)),
 ('Tarif tetap -15%',dict(retainer_factor=.85)),('Tarif tetap +15%',dict(retainer_factor=1.15)),
 ('Biaya langsung +20%',dict(direct_factor=1.2)),('Biaya langsung -20%',dict(direct_factor=.8)),
 ('Biaya bersama +15%',dict(overhead_factor=1.15)),('Biaya bersama -15%',dict(overhead_factor=.85)),
 ('Tagihan perangkat tertunda 2 bulan',dict(lag=2)),
]:
 s=run(**kwargs);sens.append(dict(label=name,npv=s['npv'],funding=s['need'],delta_npv=s['npv']-base['npv']))
# Shared participation factor links contracted host-months and delivered workload.
# No fitted probabilities or local field estimates are claimed.
rng=np.random.default_rng(SEED)
trials=[]
for i in range(N):
    participation=rng.triangular(.55,1,1.15)
    volume_specific=rng.triangular(.65,1,1.15)
    volume=.6*participation+.4*volume_specific
    pricing=rng.triangular(.8,1,1.10)
    # Greater accepted tariff may mildly reduce acquisition; no independent upside stack.
    hostfactor=np.clip(participation*(1-.25*(pricing-1)),.45,1.25)
    directfactor=rng.triangular(.9,1,1.3)
    overheadfactor=.5*directfactor+.5*rng.triangular(.9,1,1.2)
    feefactor=rng.triangular(.90,1,1.08)
    lag=int(rng.choice([0,1,2],p=[.1,.65,.25]))
    prepaid=rng.triangular(.7,1,1)
    s=run(host_factor=hostfactor,volume_factor=volume,retainer_factor=pricing,fee_factor=feefactor,direct_factor=directfactor,overhead_factor=overheadfactor,lag=lag,retainer_prepaid=prepaid)
    trials.append([i+1,participation,volume,hostfactor,pricing,directfactor,overheadfactor,feefactor,lag,prepaid,s['npv'],s['need'],float(s['revenue'][24:].sum()/s['expense'][24:].sum()),float(s['cumulative'][-1])])
arr=np.array(trials)
metrics={'npv':10,'required_funding':11,'year3_cost_coverage':12,'closing_unfinanced_cash':13}
mc={k:dict(zip(['p10','p50','p90'],np.percentile(arr[:,j],[10,50,90]).tolist())) for k,j in metrics.items()}
mc.update(seed=SEED,draws=N,positive_npv_share=float((arr[:,10]>=0).mean()),year3_coverage_share=float((arr[:,12]>=1).mean()),funding_110m_suffices_share=float((arr[:,11]<=INITIAL_FUNDING).mean()),scope='Frekuensi skenario asumsi tim; bukan probabilitas keberhasilan pasar.')
# Convergence is numerical, not evidence about whether assumptions are true.
stability=[]
for k,j in metrics.items():
 full=np.percentile(arr[:,j],[10,50,90]);half=np.percentile(arr[:N//2,j],[10,50,90]);width=full[2]-full[0]
 stability.append(dict(metric=k,max_quantile_shift_over_p90p10=float(np.max(np.abs(full-half))/width)))
mc['stability']=stability
# Rank association without external stats dependency; values are continuous except lag.
def rank(a):
 order=np.argsort(a,kind='stable');r=np.empty(len(a),dtype=float);r[order]=np.arange(len(a),dtype=float)
 vals,starts,counts=np.unique(a,return_index=True,return_counts=True)
 # Tie handling via sorted-index grouping.
 sorted_a=a[order];bounds=np.r_[0,np.where(np.diff(sorted_a)!=0)[0]+1,len(a)]
 for lo,hi in zip(bounds[:-1],bounds[1:]): r[order[lo:hi]]=(lo+hi-1)/2
 return r
ranky=rank(arr[:,10]);drivers=[]
for key,j in [('Partisipasi/kontrak',1),('Volume per kontrak',2),('Tarif tetap',4),('Biaya langsung',5),('Biaya bersama',6),('Tarif perangkat',7),('Jeda tagihan',8),('Prapembayaran',9)]:
 drivers.append(dict(label=key,spearman=float(np.corrcoef(rank(arr[:,j]),ranky)[0,1])))
mc['rank_associations']=drivers
# Arithmetic/flow integrity checks; arrays are exact numeric source for manuscript.
assert AVG_FEE==62000 and AVG_DIRECT==44350
assert len(BASE_HOSTS)==36 and np.all(base['workload']<=base['funded_hours'])
assert np.allclose(base['revenue']-base['expense'],base['ebitda'])
assert np.allclose(np.cumsum(base['revenue']-base['cashin']),base['receivable'])
assert np.all(base['receivable']>=-.01)
assert np.allclose(-SETUP+np.cumsum(base['netcash']),base['cumulative'])
assert all(sum(c[k] for k in ('transport','handling','review','exceptions'))<c['fee'] for c in CAT.values())
# All host counts in deterministic base are whole; money and shipments kept separate.
assert np.all(BASE_HOSTS==BASE_HOSTS.astype(int))

monthly=[]
for i in range(36):
 monthly.append(dict(month=i+1,year=2027+i//12,hosts=float(base['hosts'][i]),devices=float(base['devices'][i]),retainer=float(base['retainer'][i]),device_revenue=float(base['device_rev'][i]),revenue=float(base['revenue'][i]),direct_cost=float(base['direct'][i]),fixed_cost=float(base['fixed'][i]),onboarding=float(base['onboarding'][i]),ebitda=float(base['ebitda'][i]),cashin=float(base['cashin'][i]),net_cash=float(base['netcash'][i]),closing_unfinanced_cash=float(base['cumulative'][i]),closing_financed_cash=float(INITIAL_FUNDING+base['cumulative'][i]),receivables=float(base['receivable'][i]),cash_floor=float(base['reserve'][i]),work_hours=float(base['workload'][i]),funded_hours=float(base['funded_hours'][i])))
quarterly=[]
for i in range(12):
 a=slice(i*3,(i+1)*3)
 quarterly.append(dict(year=2027+i//4,quarter=i%4+1,host_months=float(base['hosts'][a].sum()),devices=float(base['devices'][a].sum()),revenue=float(base['revenue'][a].sum()),expense=float(base['expense'][a].sum()),ebitda=float(base['ebitda'][a].sum()),net_cash=float(base['netcash'][a].sum()),closing_financed_cash=float(INITIAL_FUNDING+base['cumulative'][(i+1)*3-1])))
# Market envelope uses published HEI count but service fee/eligibility are team assumptions.
annual_package=12*(3000000+40*AVG_FEE)
market=dict(tam_institutions=4303,tam_value=4303*annual_package,sam_programs=100,sam_value=100*annual_package,som_year3_hostmonths=126,som_year3_revenue=summary(base)['annual'][2]['revenue'],som_year3_devices=5040,closing_hosts_year3=12,package_annual=annual_package,scope='Segmen perguruan tinggi; satu program standar per institusi untuk TAM. SAM100 adalah cakupan penawaran tim, bukan hitungan institusi terverifikasi. SOM mengikuti126bulan-kontrak.',source='Kemdiktisaintek (2026), Statistik Pendidikan Tinggi 2025, Grafik1.1–1.2, pp3–4; harga/frekuensi dan SAM: Estimasi tim.')
contrib_host=3000000+40*(AVG_FEE-AVG_DIRECT)
# First commercial steady state with three hosts; shared cost/hosts retained.
breakeven=dict(contribution_per_host=contrib_host,hosts_for_initial_shared_cost=11100000/contrib_host,integer_hosts=math.ceil(11100000/contrib_host),retainer_at_3hosts=11100000/3-40*(AVG_FEE-AVG_DIRECT),retainer_at_4hosts=11100000/4-40*(AVG_FEE-AVG_DIRECT),devices_needed_at_3hosts=(11100000-3*3000000)/(AVG_FEE-AVG_DIRECT),devices_needed_at_4hosts=max(0,(11100000-4*3000000)/(AVG_FEE-AVG_DIRECT)),scope='Steady state sebelum onboarding, pajak, bunga dan belanja awal; biaya bersama awal11.1juta/bulan.')
data=dict(status='Estimasi tim; bukan kontrak, hasil lapangan atau penawaran harga',currency='Rupiah konstan2027',period='Januari2027–Desember2029; bulan1–2 persiapan, layananmulai bulan3',assumptions=dict(category=CAT,avg_fee=AVG_FEE,avg_direct_cost=AVG_DIRECT,devices_per_host_month=40,retainer=3000000,setup_software_training=16000000,setup_equipment=12000000,setup_total=SETUP,planned_financing=INITIAL_FUNDING,committed_financing=0,discount_rate=DISCOUNT,tax='Hasil sebelum pajak, bunga dan distribusi pemilik; tidak mengestimasi kewajiban pajak badan.',recovery_revenue=0,payment='Tarif tetap prabayar; tarif perangkat diterima satu bulan setelah pengakuan layanan.',success_unit='Satu perangkat diterima tujuan dan serah terima direkonsiliasi. Bukan bukti guna ulang atau daur ulang selesai.',fixed_other=dict(hosting=350000,workspace=500000,communications=250000,professional=500000,protection=250000,travel=250000),labor='Pengelola150jam/bulan ×40ribu; operasi50jam ×40ribu perblok untuk setiapempat host (dibulatkankeatas), minimum1blok.',capacity='80jam bersama/bulan +8jam/host +0.2jam/perangkat. Tawaran perjalanan dan penerima tetap membatasi layanan.',reserve='Dua bulan biaya bersama + satu minggu biaya pemenuhan.',exclusions='Tidak memasukkan nilai terminal, penjualan perangkat, kredit karbon, pinjaman atau hibah otomatis.'),base=summary(base),downside=summary(down),upside=summary(up),monthly=monthly,quarterly=quarterly,sensitivity=sens,monte_carlo=mc,market=market,breakeven=breakeven)
(OUT/'finance.json').write_text(json.dumps(clean(data),ensure_ascii=False,indent=2))
with (OUT/'finance_mc_draws.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['trial','participation','volume_factor','host_factor','retainer_factor','direct_factor','overhead_factor','fee_factor','lag_months','prepaid_share','npv_idr','funding_need_idr','year3_coverage','closing_unfinanced_cash']);w.writerows(trials)
# Compact native table specifications for document author.
fmt=lambda x:f"{x:,.0f}".replace(',','.')
mil=lambda x:f"{x/1000000:,.2f}".replace(',','X').replace('.',',').replace('X','.')
tables={
 'H1':{'title':'Tarif dan anggaran pemenuhan per perangkat','columns':['Kategori','Bauran','Tarif Rp','Angkut Rp','Terima/tangani Rp','Tinjau Rp','Pengecualian Rp','Total biaya Rp'],'rows':[[c['label'],f"{c['share']:.0%}",fmt(c['fee']),fmt(c['transport']),fmt(c['handling']),fmt(c['review']),fmt(c['exceptions']),fmt(sum(c[k] for k in ('transport','handling','review','exceptions')))] for c in CAT.values()],'note':'Estimasi tim, rupiah konstan2027. Kategori khusus hanya dilayani operator yang memenuhi persyaratan. Anggaran pengecualian diasumsikan digunakan.'},
 'H2':{'title':'Biaya bersama dan modal awal','columns':['Komponen','Nilai','Dasar'],'rows':[['Imbalan pengelola','Rp6.000.000/bulan','150jam total ×Rp40.000'],['Tenaga operasi','Rp2juta per50jam/bulan','Satu blok untuk setiapempat host; minimum1blok'],['Hosting','Rp350.000/bulan','Estimasi tim'],['Ruang kerja','Rp500.000/bulan','Estimasi tim'],['Komunikasi','Rp250.000/bulan','Estimasi tim'],['Profesional/review','Rp500.000/bulan','Estimasi tim'],['Perlindungan/administrasi insiden','Rp250.000/bulan','Estimasi tim; bukanjaminan pertanggungan'],['Perjalanan koordinasi','Rp250.000/bulan','Estimasi tim'],['Akuisisi/pemasaran','Rp1/1,2/1,5juta perbulan','Tahun1/2/3'],['Onboarding','Rp500.000/hostbaru','Tambahan layanan/latihan dan bahan'],['Peralatanawal','Rp12.000.000','Belanja awal; tidak ada nilai terminal'],['Konfigurasi perangkatlunak/pelatihan','Rp16.000.000','Biaya persiapan sebelum operasi']],'note':'Semua nilai estimasi tim. Imbalan pengelola merupakan biaya kerja, terpisah dari distribusi keuntungan.'},
 'H3':{'title':'Rekap tahunan model dasar','columns':['Ukuran','2027','2028','2029'],'rows':[[label]+[mil(a[key]) if unit=='m' else fmt(a[key]) for a in summary(base)['annual']] for label,key,unit in [('Bulan-kontrak','host_months','n'),('Host akhir tahun','closing_hosts','n'),('Perangkat diterima','devices','n'),('Penerimaan layanan, juta Rp','revenue','m'),('Biaya pemenuhan, juta Rp','direct_cost','m'),('Biaya bersama, juta Rp','fixed_cost','m'),('Onboarding, juta Rp','onboarding','m'),('Surplus operasi, juta Rp','ebitda','m'),('Kasbersih periode, juta Rp','net_cash','m'),('Kasakhir dengan rencana modal, juta Rp','closing_cash_with_planned_financing','m'),('Piutangakhir, juta Rp','receivables','m')]],'note':'Surplus operasi sebelum pajak/bunga. Modal rencana110juta masuk sekali sebelum bulan1; komitmen dana masih0.'},
 'H4':{'title':'Skenario operasi tiga tahun','columns':['Ukuran','Downside','Dasar','Upside'],'rows':[[label]+[mil(summary(s)[key]) if unit=='m' else str(summary(s)[key]) for s in [down,base,up]] for label,key,unit in [('NPV sebelum pajak, jutaRp','npv','m'),('Kebutuhan pendanaan, jutaRp','required_funding','m'),('Pengembalian kas, bulan','payback_month','n'),('Penerimaan tiga tahun, jutaRp','total_revenue','m')]],'note':'Tidak ada nilai terminal. Downside:bulan-kontrak65%, volume75%, tarif tetap80%, biaya langsung120%, jedaperangkat2bulan dan80%tariftetap prabayar. Upside:bulan-kontrak110%, volume110%, tarif tetap105%, biaya langsung95%.'},
 'H5':{'title':'Arus kas bulanan tahun pertama','columns':['Bln','Host','Unit','Penerimaan','Biaya','Surplus','Kasmasuk','Kasakhir'],'rows':[[str(i+1),fmt(base['hosts'][i]),fmt(base['devices'][i]),mil(base['revenue'][i]),mil(base['expense'][i]),mil(base['ebitda'][i]),mil(base['cashin'][i]),mil(INITIAL_FUNDING+base['cumulative'][i])] for i in range(12)],'note':'JutaRp, kecuali host danunit. Kasakhir mencakup rencana modal110juta dan pengeluaranawal28juta.'},
 'H6':{'title':'Rekap kuartalan tiga tahun','columns':['Tahun/Q','Bln-kontrak','Unit','Penerimaan','Biaya','Surplus','Kasbersih','Kasakhir'],'rows':[[f"{q['year']}/Q{q['quarter']}",fmt(q['host_months']),fmt(q['devices']),mil(q['revenue']),mil(q['expense']),mil(q['ebitda']),mil(q['net_cash']),mil(q['closing_financed_cash'])] for q in quarterly],'note':'JutaRp, kecuali bulan-kontrak danunit.'},
 'L1':{'title':'Hasil10.000 skenario asumsi','columns':['Ukuran','P10','P50','P90'],'rows':[[label]+[mil(mc[key][p]) if unit=='m' else f"{mc[key][p]*100:.1f}%" for p in ['p10','p50','p90']] for label,key,unit in [('NPV, jutaRp','npv','m'),('Kebutuhan pendanaan, jutaRp','required_funding','m'),('Cakupan biaya tahun3','year3_cost_coverage','pct'),('Kasakhir sebelum pendanaan, jutaRp','closing_unfinanced_cash','m')]],'note':f"Seed{SEED}; frekuensi NPV≥0:{mc['positive_npv_share']:.1%}; cakupan biaya tahun3≥1:{mc['year3_coverage_share']:.1%}. Frekuensi bersyarat pada asumsi, bukan peluang keberhasilan pasar."},
}
(OUT/'finance_tables.json').write_text(json.dumps(clean(tables),ensure_ascii=False,indent=2))
print(json.dumps(clean({k:data[k] for k in ['base','downside','upside','breakeven','market','monte_carlo']}),ensure_ascii=False,indent=2))
# Extend the published specifications with method and decision tables.
inputs=[
 ['Partisipasi kontrak','Triangular 0,55;1,00;1,15','Faktor bersama bulan-kontrak dan volume'],
 ['Volume spesifik','Triangular 0,65;1,00;1,15','Volume=0,6×partisipasi+0,4×volume spesifik'],
 ['Tarif tetap','Triangular 0,80;1,00;1,10','Bulan-kontrak dikalikan1−0,25×(faktor tarif−1)'],
 ['Tarif perangkat','Triangular 0,90;1,00;1,08','Diterapkan pada tarif setiap kategori'],
 ['Biaya pemenuhan','Triangular 0,90;1,00;1,30','Faktor bersama biaya langsung'],
 ['Biaya bersama spesifik','Triangular 0,90;1,00;1,20','Faktor biaya bersama=0,5×biaya langsung+0,5×faktor spesifik'],
 ['Jeda tagihan perangkat','0/1/2bulan; bobot10%/65%/25%','Perubahan waktu penerimaan, bukan pendapatan baru'],
 ['Prapembayaran tarif tetap','Triangular 0,70;1,00;1,00','Sisa dibayar bulan berikutnya'],
]
data['monte_carlo']['inputs']=inputs
data['monte_carlo']['funding_160m_suffices_share']=float((arr[:,11]<=160000000).mean())
data['funding_policy']=dict(base_plan=110000000,contingent_envelope=50000000,total_proposed_envelope=160000000,committed=0,condition='Sediakan otorisasi dan sumber dana yang nyata sebelum komitmen layanan baru; angka160juta adalah amplop rencana, bukan jaminan atau komitmen.')
data['breakeven']['confirmed_operating_month']=next((i+1 for i in range(2,36) if np.all(base['ebitda'][i-2:i+1]>0)),None)
tables['H7']={'title':'Ambang operasi dan kebutuhan pendanaan','columns':['Ukuran','Hasil','Interpretasi'],'rows':[
 ['Kontribusi per host/bulan',f'Rp{fmt(contrib_host)}','Tarif tetap+marjin40perangkat; sebelum biaya bersama'],
 ['Host minimum',str(breakeven['integer_hosts']),'Pada40perangkat/host dan biaya bersama awal11,1juta'],
 ['Tarif tetap impas pada3host',f'Rp{fmt(breakeven["retainer_at_3hosts"])}','Hampir sama dengan tarif3juta;4host memberi ruang lebih besar'],
 ['Surplus operasi3bulan berturut-turut',f'Bulan{data["breakeven"]["confirmed_operating_month"]}','Onboarding dan biaya bersama tetap disertakan'],
 ['Pengembalian kas proyek',f'Bulan{base["payback"]}','Sebelum pajak, pendanaan dan nilai terminal'],
 ['Kebutuhan dana dasar',f'Rp{fmt(base["need"])}','Termasuk modal awal dan batas cadangan berjalan'],
 ['Modal rencana dasar','Rp110.000.000','Komitmen dana0; bukan pendapatan'],
 ['Kebutuhan dana P90',f'Rp{fmt(mc["required_funding"]["p90"])}','Hasil skenario asumsi, bukan batas maksimum pasti'],
 ['Amplop rencana bertahap','Rp160.000.000','110juta dasar+50juta bersyarat; pelepasan sesuai kebutuhan'],
 ],'note':'Ambang impas adalah keadaan stabil, tanpa onboarding baru. Piutang dan cadangan menjelaskan mengapa surplus operasi dan kebutuhan kas berbeda.'}
tables['H8']={'title':'Pasar ekuivalen layanan dan jangkauan yang direncanakan','columns':['Lapisan','Dasar','Nilai tahunan'],'rows':[
 ['TAM','4.303perguruan tinggi×1paket referensi×Rp65,76juta','Rp282,97miliar'],
 ['SAM','100program dalam cakupan penawaran Jabodetabek; estimasi tim','Rp6,576miliar'],
 ['SOM2029','126bulan-kontrak×Rp5,48juta;12host pada akhir tahun','Rp690,48juta'],
 ],'note':'Jumlah nasional bersumber Kemdiktisaintek(2026). Satu paket referensi, cakupan100program, harga dan penggunaan40perangkat/bulan adalah estimasi tim. SAM bukan hitungan institusi Jabodetabek yang sudah diverifikasi. TAM adalah amplop ekuivalen layanan, bukan permintaan teramati.'}
tables['L2']={'title':'Distribusi dan hubungan antarinput','columns':['Input','Rentang/model','Hubungan'],'rows':inputs,'note':'Estimasi tim. Tidak ada distribusi yang dikalibrasi dari data lapangan JejakBalik. Dependensi dinyatakan agar kelemahan partisipasi tidak diperlakukan terpisah dari volume.'}
tables['L3']={'title':'Sensitivitas satu faktor','columns':['Perubahan','NPVjutaRp','PerubahanNPV','DanajutaRp'],'rows':[[x['label'],mil(x['npv']),mil(x['delta_npv']),mil(x['funding'])] for x in sens],'note':'Input lain tetap. Perubahan bulan-kontrak dapat mengubah blok tenaga operasi sehingga efeknya tidak linear.'}
tables['L4']={'title':'Pemeriksaan kestabilan numerik','columns':['Ukuran','Pergeseran kuantil maksimum/P90−P10'],'rows':[[x['metric'],f"{x['max_quantile_shift_over_p90p10']*100:.2f}%"] for x in stability],'note':'Membandingkan5.000draw pertama dengan10.000draw; kuantilP10/P50/P90. Ketelitian numerik tidak membuktikan kebenaran asumsi.'}
(OUT/'finance.json').write_text(json.dumps(clean(data),ensure_ascii=False,indent=2))
(OUT/'finance_tables.json').write_text(json.dumps(clean(tables),ensure_ascii=False,indent=2))
