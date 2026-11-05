"""JejakBalik impact planning, derived from the unchanged canonical finance model.
No empirical field impact is claimed. Run with CODEX_PRIMARY_RUNTIME_PYTHON.
"""
from pathlib import Path
import ast
import hashlib
import json
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
FINANCE_SCRIPT = ROOT / 'production/finance_model.py'
FINANCE_JSON = ROOT / 'production/finance.json'
PROTECTED = [FINANCE_SCRIPT, FINANCE_JSON, ROOT/'production/finance_tables.json', ROOT/'production/finance_mc_draws.csv']
BEFORE = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in PROTECTED}
canonical = json.loads(FINANCE_JSON.read_text())
source = ast.parse(FINANCE_SCRIPT.read_text())
# Execute only the original imports/constants/run definition, before any report
# generation. Importing the module itself would rewrite the canonical files.
prefix = []
for node in source.body:
    if isinstance(node, ast.FunctionDef) and node.name == 'clean':
        break
    prefix.append(node)
ns = {'__file__': str(FINANCE_SCRIPT)}
exec(compile(ast.Module(body=prefix, type_ignores=[]), str(FINANCE_SCRIPT), 'exec'), ns)

def canonical_run_keywords(name):
    for node in source.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'run':
                return {k.arg: ast.literal_eval(k.value) for k in node.value.keywords}
    raise KeyError(name)

# Category averages are planning batch-mix assumptions, not physical device
# bounds, measured weights, or recovery/recycling yields. Financial mix unchanged.
WEIGHTS = {
    'ordinary': {'label':'Biasa','low_kg':1.0,'base_kg':2.0,'high_kg':4.0,
                 'rationale':'Rerata campuran perangkat TI kecil, laptop dan periferal. Bukan berat minimum setiap benda.'},
    'bulky': {'label':'Besar','low_kg':15.0,'base_kg':25.0,'high_kg':35.0,
              'rationale':'Rerata campuran monitor, printer dan perangkat rumah tangga besar; kategori bukan satu produk tertentu.'},
    'specialist': {'label':'Khusus','low_kg':3.0,'base_kg':6.0,'high_kg':10.0,
                  'rationale':'Rerata campuran perangkat/kemasan yang memerlukan penanganan khusus, misalnya unit baterai atau UPS; tidak semua media penyimpan data seberat ini.'},
}
shares = {k: v['share'] for k,v in ns['CAT'].items()}
weighted_kg = {case: sum(shares[k] * v[f'{case}_kg'] for k,v in WEIGHTS.items()) for case in ['low','base','high']}
assert math.isclose(sum(shares.values()),1)
assert all(0 < v['low_kg'] <= v['base_kg'] <= v['high_kg'] for v in WEIGHTS.values())

SCENARIO_MAP = {'low':('down','downside'),'base':('base','base'),'high':('up','upside')}
scenarios = {}
for label, (source_name, summary_name) in SCENARIO_MAP.items():
    kwargs = canonical_run_keywords(source_name)
    s = ns['run'](**kwargs)
    reference = canonical[summary_name]
    assert abs(s['npv'] - reference['npv']) < .001
    assert abs(s['need'] - reference['required_funding']) < .001
    assert abs(float(s['devices'].sum()) - reference['total_devices']) < 1e-6
    transport = sum(c['share'] * c['transport'] for c in ns['CAT'].values())
    handling = sum(c['share'] * c['handling'] for c in ns['CAT'].values())
    # Cost-factor change is the existing financial scenario change, not an
    # additional monetized benefit. These allocations are costs already counted.
    direct_factor = kwargs.get('direct_factor',1)
    annual = []
    for y in range(3):
        sl = slice(y*12,(y+1)*12)
        q = float(s['devices'][sl].sum())
        h = float(s['hosts'][sl].sum())
        ops_hours = float((s['ops'][sl]/40000).sum())
        manager_hours = 150*12
        workload = float(s['workload'][sl].sum())
        item = {
            'year':2027+y,'equivalent_host_months':h,'closing_equivalent_hosts':float(s['hosts'][(y+1)*12-1]),
            'devices_received':q,'received_mass_kg':q*weighted_kg[label],
            'mass_if_low_category_averages_kg':q*weighted_kg['low'],
            'mass_if_base_category_averages_kg':q*weighted_kg['base'],
            'mass_if_high_category_averages_kg':q*weighted_kg['high'],
            'category_counts':{k:q*share for k,share in shares.items()},
            'paid_management_hours':manager_hours,'paid_operations_hours':ops_hours,
            'paid_total_hours':manager_hours+ops_hours,'estimated_required_work_hours':workload,
            'hours_capacity_headroom':manager_hours+ops_hours-workload,
            'paid_capacity_use_ratio':workload/(manager_hours+ops_hours),
            'transport_budget_idr':q*transport*direct_factor,
            'receiver_handling_budget_idr':q*handling*direct_factor,
            'direct_service_budget_idr':float(s['direct'][sl].sum()),
            'receiving_events_minimum':q,'pickup_and_receiving_events_minimum':2*q,
        }
        assert abs(item['paid_total_hours'] - float(s['funded_hours'][sl].sum())) < 1e-6
        assert abs(q - reference['annual'][y]['devices']) < 1e-6
        annual.append(item)
    additive = ['devices_received','received_mass_kg','paid_management_hours','paid_operations_hours',
                'paid_total_hours','estimated_required_work_hours','hours_capacity_headroom',
                'transport_budget_idr','receiver_handling_budget_idr','direct_service_budget_idr',
                'receiving_events_minimum','pickup_and_receiving_events_minimum']
    total = {k:sum(a[k] for a in annual) for k in additive}
    total['category_counts']={k:sum(a['category_counts'][k] for a in annual) for k in shares}
    scenarios[label] = {'canonical_finance_scenario':summary_name,'canonical_run_parameters':kwargs,
                        'mass_case':label,'annual':annual,'cumulative_2027_2029':total}

# An index per 100 equivalent returns, holding the original synthetic reference
# composition/locations/windows/journey offers. It is NOT a routed 100-device plan.
fixture = {'devices':18,'shared_additional_km':28.8,'dedicated_grouped_km':112.8,
           'shared_service_cost_idr':438700,'dedicated_grouped_service_cost_idr':662400}
factor = 100/fixture['devices']
index100 = {
    'equivalent_returns':100,
    'shared_additional_km':fixture['shared_additional_km']*factor,
    'dedicated_grouped_km':fixture['dedicated_grouped_km']*factor,
    'difference_km':(fixture['dedicated_grouped_km']-fixture['shared_additional_km'])*factor,
    'shared_service_cost_idr':fixture['shared_service_cost_idr']*factor,
    'dedicated_grouped_service_cost_idr':fixture['dedicated_grouped_service_cost_idr']*factor,
    'difference_service_cost_idr':(fixture['dedicated_grouped_service_cost_idr']-fixture['shared_service_cost_idr'])*factor,
    'distance_difference_fraction':1-fixture['shared_additional_km']/fixture['dedicated_grouped_km'],
    'service_cost_difference_fraction':1-fixture['shared_service_cost_idr']/fixture['dedicated_grouped_service_cost_idr'],
    'interpretation':'Indeks normalisasi skenario 18 permintaan, bukan optimasi rute 100 perangkat atau penghematan operasi tahunan.',
    'exclusions':'Biaya skenario tidak merupakan biaya penuh perusahaan; tidak dikalikan ke volume tahunan atau dikonversi menjadi CO2.'
}
# Separate the two uncertainties rather than portraying the combined endpoints as
# an empirical confidence interval or mechanically correlated measurements.
mass_matrix = [{
    'volume_case':vcase,'devices_cumulative':scenarios[vcase]['cumulative_2027_2029']['devices_received'],
    **{f'{wcase}_weight_mass_tonnes':scenarios[vcase]['cumulative_2027_2029']['devices_received']*weighted_kg[wcase]/1000 for wcase in weighted_kg}
} for vcase in scenarios]

out = {
    'status':'Estimasi tim; proyeksi bersyarat, bukan hasil lapangan',
    'period':'2027–2029; tahun pertama 2027, tahun ketiga 2029',
    'count_unit':'Perangkat diterima tujuan dengan serah terima direkonsiliasi; bukan jumlah orang, rumah tangga, perangkat didaur ulang atau perangkat dialihkan secara neto dari TPA.',
    'scenario_method':'Volume berasal langsung dari downside/base/upside kanonis. LOW/HIGH bukan interval kepercayaan atau probabilitas; perangkat pecahan adalah ekspektasi ekuivalen bulan-kontrak, dibulatkan ke unit terdekat untuk penyajian.',
    'weight_status':'Estimasi tim atas rerata setiap kategori; rentang menggambarkan campuran layanan, bukan batas berat setiap jenis perangkat. Bauran 80% biasa, 15% besar, 5% khusus tetap sama dengan model finansial.',
    'category_weights':WEIGHTS,'category_shares':shares,'weighted_kg_per_device':weighted_kg,
    'formulas':{
        'devices':'q_t = canonical_base_hosts_t × host_factor × 40 × volume_factor',
        'mass_kg':'q_t × (0.80 × ordinary_average_kg + 0.15 × bulky_average_kg + 0.05 × specialist_average_kg)',
        'paid_management_hours':'150 hours per month',
        'paid_operations_hours':'50 × max(1, ceil(active_equivalent_hosts_t / 4)) hours per month',
        'required_work_hours':'80 + 8 × active_equivalent_hosts_t + 0.2 × devices_received_t',
        'transport_budget':'devices_received × Rp21,750 × existing_direct_cost_factor',
        'receiver_handling_budget':'devices_received × Rp17,600 × existing_direct_cost_factor'
    },
    'environmental_boundary':'Massa yang diterima ke jalur penanganan terdokumentasi dihitung sebagai arus layanan. Tidak diasumsikan sebagai pemulihan material, daur ulang selesai, pencegahan limbah neto, tambahan masa pakai, atau emisi yang dihindari.',
    'work_boundary':'Jam dibayar adalah kapasitas kerja pengelola/operasi yang telah dianggarkan, termasuk persiapan dan kesiapsiagaan. Bukan hitungan pekerjaan baru atau janji jam terpakai. Jam pengangkut/penerima tidak diketahui dan tidak dijumlahkan.',
    'benefit_budget_boundary':'Anggaran transportasi dan penanganan penerima adalah biaya jasa yang sudah masuk model, bukan keuntungan tambahan atau nilai ekonomi bersih. Tidak dijumlahkan lagi ke surplus perusahaan.',
    'scenarios':scenarios,'mass_sensitivity_matrix':mass_matrix,
    'logistics_index_per_100':index100,
    'no_annual_logistics_forecast':'Tanpa jadwal perjalanan nyata, penurunan kilometer/biaya skenario tidak diproyeksikan ke tahunan. Keuntungan layanan tahunan yang dihitung adalah kapasitas penerimaan, arus massa, dukungan kerja dan anggaran jasa.',
    'provenance':{'finance_script_sha256':BEFORE[str(FINANCE_SCRIPT)],'finance_json_sha256':BEFORE[str(FINANCE_JSON)],
                  'finance_files_unchanged':True,'source':'Model keuangan kanonis dan skenario perangkat rekaan yang telah dihitung; tidak ada fakta eksternal baru.'}
}

def clean(v):
    if isinstance(v,bool):return v
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x) for x in v]
    if isinstance(v,(np.integer,int)):return int(v)
    if isinstance(v,(np.floating,float)):return round(float(v),6)
    return v

def n(x):return f'{int(math.floor(x+.5)):,}'.replace(',','.')
def dec(x,d=1):return f'{x:,.{d}f}'.replace(',','X').replace('.',',').replace('X','.')
def mil(x):return dec(x/1e6,2)

tables={
 'I1':{'title':'Jangkauan dan kapasitas kerja 2027–2029','columns':['Ukuran','LOW','BASE','HIGH'],'rows':[
   [title]+[n(scenarios[k]['annual'][year][key]) for k in scenarios]
   for title,year,key in [('Perangkat diterima tahun 1',0,'devices_received'),('Perangkat diterima tahun 3',2,'devices_received'),('Jam kerja dibayar tahun 1',0,'paid_total_hours'),('Jam kerja dibayar tahun 3',2,'paid_total_hours')]
  ]+[[title]+[n(scenarios[k]['cumulative_2027_2029'][key]) for k in scenarios]
       for title,key in [('Perangkat diterima tiga tahun','devices_received'),('Jam kerja dibayar tiga tahun','paid_total_hours'),('Kebutuhan jam kerja tiga tahun','estimated_required_work_hours')]],
  'note':'Estimasi tim; volume memakai skenario finansial yang sama. Jam kerja dibayar merupakan kapasitas pengelola dan operasi, bukan jumlah pekerjaan atau jam angkut.'},
 'I2':{'title':'Asumsi massa rata-rata per kategori','columns':['Kategori','Bauran','LOW kg','BASE kg','HIGH kg'],'rows':[
  [v['label'],f'{shares[k]:.0%}',dec(v['low_kg']),dec(v['base_kg']),dec(v['high_kg'])]for k,v in WEIGHTS.items()
 ]+[['Rata-rata berbobot','100%',dec(weighted_kg['low'],2),dec(weighted_kg['base'],2),dec(weighted_kg['high'],2)]],
 'note':'Estimasi tim atas rerata campuran kategori, bukan berat minimum/maksimum setiap benda; bukan konversi massa menjadi hasil daur ulang.'},
 'I3':{'title':'Massa perangkat yang masuk jalur penerimaan','columns':['Periode','LOW ton','BASE ton','HIGH ton'],'rows':[
  ['2027']+[dec(scenarios[k]['annual'][0]['received_mass_kg']/1000,2)for k in scenarios],
  ['2029']+[dec(scenarios[k]['annual'][2]['received_mass_kg']/1000,2)for k in scenarios],
  ['2027–2029']+[dec(scenarios[k]['cumulative_2027_2029']['received_mass_kg']/1000,2)for k in scenarios]],
 'note':'Estimasi tim: setiap kolom memasangkan skenario volume dan rerata berat kategori yang sesuai. Ini arus perangkat diterima, bukan massa material berhasil dipulihkan atau dampak kausal.'},
 'I4':{'title':'Pengaruh campuran berat pada volume tiga tahun','columns':['Volume','Perangkat','Berat LOW ton','Berat BASE ton','Berat HIGH ton'],'rows':[
   [x['volume_case'].upper(),n(x['devices_cumulative']),dec(x['low_weight_mass_tonnes'],2),dec(x['base_weight_mass_tonnes'],2),dec(x['high_weight_mass_tonnes'],2)] for x in mass_matrix],
 'note':'Pisahkan ketidakpastian volume dan berat. Pada volume dasar 9.240 perangkat, rentang massa 29,57–82,70 ton; nilai tengah 52,21 ton.'},
 'I5':{'title':'Anggaran jasa dan kapasitas kerja pada skenario dasar','columns':['Ukuran','2027','2029','Total tiga tahun'],'rows':[
   ['Angkutan, juta Rp']+[mil(x)for x in [scenarios['base']['annual'][0]['transport_budget_idr'],scenarios['base']['annual'][2]['transport_budget_idr'],scenarios['base']['cumulative_2027_2029']['transport_budget_idr']]],
   ['Penanganan penerima, juta Rp']+[mil(x)for x in [scenarios['base']['annual'][0]['receiver_handling_budget_idr'],scenarios['base']['annual'][2]['receiver_handling_budget_idr'],scenarios['base']['cumulative_2027_2029']['receiver_handling_budget_idr']]],
   ['Jam dibayar pengelola/operasi']+[n(x)for x in [scenarios['base']['annual'][0]['paid_total_hours'],scenarios['base']['annual'][2]['paid_total_hours'],scenarios['base']['cumulative_2027_2029']['paid_total_hours']]],
   ['Kebutuhan jam pengelola/operasi']+[n(x)for x in [scenarios['base']['annual'][0]['estimated_required_work_hours'],scenarios['base']['annual'][2]['estimated_required_work_hours'],scenarios['base']['cumulative_2027_2029']['estimated_required_work_hours']]]],
 'note':'Estimasi tim, rupiah konstan 2027. Anggaran jasa telah masuk biaya langsung; jam dibayar telah masuk biaya bersama. Keduanya tidak dihitung kembali sebagai keuntungan tambahan.'},
 'I6':{'title':'Indeks kesempatan efisiensi per 100 pengembalian setara','columns':['Ukuran','Perjalanan tersedia','Khusus berkelompok','Selisih'],'rows':[
  ['Tambahan jarak, km',dec(index100['shared_additional_km']),dec(index100['dedicated_grouped_km']),dec(index100['difference_km'])],
  ['Biaya jasa skenario, juta Rp',mil(index100['shared_service_cost_idr']),mil(index100['dedicated_grouped_service_cost_idr']),mil(index100['difference_service_cost_idr'])]],
 'note':'Normalisasi skenario 18 permintaan dengan komposisi, lokasi, waktu dan penawaran perjalanan yang sama; bukan rute 100 perangkat, biaya penuh perusahaan, atau penghematan tahunan. Tidak digunakan untuk menghitung emisi.'},
}
(OUT/'impact.json').write_text(json.dumps(clean(out),ensure_ascii=False,indent=2))
(OUT/'impact_tables.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2))
AFTER={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in PROTECTED}
assert BEFORE==AFTER, 'Canonical finance files changed unexpectedly'
print(json.dumps({'devices_3yr':{k:v['cumulative_2027_2029']['devices_received'] for k,v in scenarios.items()},
                  'mass_3yr_tonnes':{k:v['cumulative_2027_2029']['received_mass_kg']/1000 for k,v in scenarios.items()},
                  'paid_hours_3yr':{k:v['cumulative_2027_2029']['paid_total_hours'] for k,v in scenarios.items()},
                  'finance_files_unchanged':BEFORE==AFTER},ensure_ascii=False,indent=2))
