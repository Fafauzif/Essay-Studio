#!/usr/bin/env python3
"""Optional exact weighted scores and conditional financial planning.

This general model contains no JejakBalik rates, demand or claimed observations.
"""
from pathlib import Path
import argparse, json, math
import numpy as np

FACTORS=('units_factor','price_factor','variable_cost_factor','fixed_cost_factor','retainer_factor')
FINANCE_KEYS={'months','units','unit_price','unit_variable_cost','fixed_cost','retainer','other_cost','setup_cost','annual_discount_rate','receipts_lag_months','retainer_prepaid','planned_financing','reserve_months_fixed','uncertainty','status','currency','price_year','price_basis','title','description','metadata','sources','assumptions'}

def series(value,n,name):
    a=np.asarray(value if isinstance(value,list)else[value]*n,dtype=float)
    if a.shape!=(n,)or not np.isfinite(a).all()or(a<0).any():raise ValueError(f'{name} must be nonnegative finite scalar or {n}-item array.')
    return a

def finance(config,factors=None,*,include_monthly=True):
    unknown=set(config)-FINANCE_KEYS
    if unknown:raise ValueError(f'Unknown financial input keys: {sorted(unknown)}. No silent ignored assumptions.')
    factors=factors or {};unknown=set(factors)-set(FACTORS)
    if unknown:raise ValueError(f'Unknown factors: {sorted(unknown)}')
    if any(not math.isfinite(float(x))or x<0 for x in factors.values()):raise ValueError('Factors must be finite and nonnegative.')
    n=config['months']
    if type(n)is not int or not 1<=n<=1200:raise ValueError('months must be an integer between 1 and 1200.')
    discount=float(config.get('annual_discount_rate',0));setup=float(config.get('setup_cost',0));fund=float(config.get('planned_financing',0));reserve_months=float(config.get('reserve_months_fixed',0));prepaid=float(config.get('retainer_prepaid',1))
    if not all(math.isfinite(x)for x in [discount,setup,fund,reserve_months,prepaid])or discount<0 or min(setup,fund,reserve_months)<0 or not 0<=prepaid<=1:raise ValueError('Invalid discount, setup, financing, reserve or prepaid fraction.')
    lag=config.get('receipts_lag_months',0)
    if type(lag)is not int or not 0<=lag<=n:raise ValueError('receipts_lag_months must be an integer from zero through horizon.')
    u=series(config['units'],n,'units')*factors.get('units_factor',1)
    price=series(config['unit_price'],n,'unit_price')*factors.get('price_factor',1)
    variable=u*series(config['unit_variable_cost'],n,'unit_variable_cost')*factors.get('variable_cost_factor',1)
    fixed=series(config['fixed_cost'],n,'fixed_cost')*factors.get('fixed_cost_factor',1)
    retainer=series(config.get('retainer',0),n,'retainer')*factors.get('retainer_factor',1)
    other=series(config.get('other_cost',0),n,'other_cost')
    unit_revenue=u*price;revenue=unit_revenue+retainer;cost=variable+fixed+other
    unit_receipts=np.r_[np.zeros(lag),unit_revenue[:n-lag]]if lag else unit_revenue.copy()
    retainer_receipts=retainer*prepaid+np.r_[0,(retainer*(1-prepaid))[:-1]]
    receipts=unit_receipts+retainer_receipts;cashflow=receipts-cost
    cumulative=-setup+np.cumsum(cashflow);reserve=fixed*reserve_months
    need=float(max(0,setup+reserve[0],np.max(reserve-cumulative)))
    npv=float(-setup+sum(cashflow/(1+discount)**(np.arange(1,n+1)/12)))
    payback=next((i+1 for i in range(n)if cumulative[i]>=0 and(cumulative[i:]>=0).all()),None)
    result={'npv':npv,'funding_need_including_reserve':need,'sustained_cash_payback_month':payback,'total_units':float(u.sum()),'total_accrued_revenue':float(revenue.sum()),'total_cash_receipts':float(receipts.sum()),'total_operating_cost':float(cost.sum()),'closing_receivables':float((revenue-receipts).sum()),'closing_project_cash_before_financing':float(cumulative[-1])}
    if include_monthly:result['monthly']=[{'month':i+1,'units':float(u[i]),'accrued_revenue':float(revenue[i]),'cash_receipts':float(receipts[i]),'cost':float(cost[i]),'net_cash_flow':float(cashflow[i]),'project_cash_before_financing':float(cumulative[i]),'cash_with_planned_financing':float(cumulative[i]+fund),'reserve_target':float(reserve[i])}for i in range(n)]
    return result

def inverse_cdf(q,spec):
    kind=spec['distribution'];lo=float(spec['min']);hi=float(spec['max'])
    if not all(math.isfinite(x)for x in [lo,hi])or lo<0 or hi<=lo:raise ValueError('Distribution needs finite 0 <= min < max.')
    if kind=='uniform':return lo+q*(hi-lo)
    if kind=='triangular':
        mode=float(spec['mode'])
        if not lo<=mode<=hi:raise ValueError('Triangular mode must lie within bounds.')
        split=(mode-lo)/(hi-lo)
        return np.where(q<split,lo+np.sqrt(q*(hi-lo)*(mode-lo)),hi-np.sqrt((1-q)*(hi-lo)*(hi-mode)))
    raise ValueError('Supported distributions: uniform, triangular.')

def ranks(a):
    order=np.argsort(a,kind='stable');result=np.empty(len(a),dtype=float);i=0
    while i<len(a):
        j=i+1
        while j<len(a)and a[order[j]]==a[order[i]]:j+=1
        result[order[i:j]]=(i+j-1)/2;i=j
    return result

def simulate(config):
    spec=config['uncertainty'];draws=spec.get('draws',10000);seed=spec.get('seed',1);params=spec['factors'];names=list(params)
    if type(draws)is not int or not 100<=draws<=100000:raise ValueError('draws must be 100–100000; choose effort deliberately.')
    if set(spec)-{'draws','seed','factors','latent_correlation'}:raise ValueError('Unknown uncertainty settings; use draws, seed, factors and latent_correlation.')
    if type(config['months'])is not int or draws*config['months']>5_000_000:raise ValueError('Simulation budget is at most 5,000,000 month-draws; reduce horizon or draws deliberately.')
    if not names or set(names)-set(FACTORS):raise ValueError('Define known factors in explicit stable JSON order.')
    corr=np.asarray(spec.get('latent_correlation',np.eye(len(names))),dtype=float)
    if corr.shape!=(len(names),len(names))or not np.isfinite(corr).all()or not np.allclose(corr,corr.T)or not np.allclose(np.diag(corr),1)or np.linalg.eigvalsh(corr).min()<-1e-9:raise ValueError('latent_correlation must be symmetric, PSD, finite, diagonal one, in factor order.')
    rng=np.random.default_rng(seed)
    # Gaussian copula dependence; this is latent-normal correlation, not a fitted
    # or promised marginal Spearman/Pearson correlation.
    latent=rng.multivariate_normal(np.zeros(len(names)),corr,size=draws,method='svd')
    uniform=np.vectorize(lambda x:.5*(1+math.erf(float(x)/math.sqrt(2))))(latent)
    samples=np.column_stack([inverse_cdf(uniform[:,j],params[name])for j,name in enumerate(names)])
    npvs=np.empty(draws);needs=np.empty(draws)
    for i,row in enumerate(samples):
        result=finance(config,dict(zip(names,row)),include_monthly=False)
        npvs[i]=result['npv'];needs[i]=result['funding_need_including_reserve']
    rho=[]
    for j,name in enumerate(names):
        a=ranks(samples[:,j]);b=ranks(npvs)
        rho.append({'factor':name,'spearman':float(np.corrcoef(a,b)[0,1])if np.std(a)>0 and np.std(b)>0 else None})
    return {'method':'One factor vector per run, shared across all months; Gaussian copula with uniform/triangular marginals.','draws':draws,'seed':seed,'generator':'NumPy default_rng/PCG64; multivariate_normal(method=svd)','numpy_version':np.__version__,'factor_order':names,'input_distributions':params,'latent_correlation':corr.tolist(),'quantiles':{name:dict(zip(['p10','p50','p90'],map(float,np.percentile(values,[10,50,90],method='linear'))))for name,values in [('npv',npvs),('funding_need_including_reserve',needs)]},'frequency_npv_nonnegative':float(np.mean(npvs>=0)),'frequency_planned_financing_sufficient':float(np.mean(needs<=float(config.get('planned_financing',0)))),'rank_associations':rho,'scope':'Conditional on team-specified distributions, dependence and this simplified cash model. Not probability of market success. Units may be equivalent expected units, not achieved counts. No terminal value, tax, debt or resale income added automatically.'}

def weighted(config):
    factors=config['factors'];bounds=config.get('rating_range',[1,5]);out=[]
    if not factors or len(bounds)!=2 or bounds[0]>bounds[1]:raise ValueError('Need factors and ordered rating range.')
    total=0.;weight=0.
    for row in factors:
        if not isinstance(row.get('factor'),str)or not row['factor'].strip():raise ValueError('Each factor needs a nonempty factor label for an inspectable score.')
        w=float(row['weight']);r=float(row['rating'])
        if not all(math.isfinite(x)for x in [w,r])or w<0 or not bounds[0]<=r<=bounds[1]:raise ValueError('Invalid factor weight or rating.')
        out.append({**row,'weighted_score':w*r});total+=w*r;weight+=w
    if not math.isclose(weight,1,abs_tol=1e-8):raise ValueError(f'Weights must sum to one; got {weight}. No silent normalization.')
    return {'status':config.get('status','team_assumption'),'rating_range':bounds,'factors':out,'weight_total':weight,'weighted_total':total,'scope':'Weights and ratings are explicit team judgments unless independently sourced; framework scales are not interchangeable.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['finance','score']);p.add_argument('input',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    try:
        config=json.loads(a.input.read_text(encoding="utf-8"));result=weighted(config)if a.mode=='score'else{'status':config.get('status','team_assumption'),'currency':config.get('currency'),'price_year':config.get('price_year'),'base':finance(config)}
        if a.mode=='finance'and config.get('uncertainty'):result['simulation']=simulate(config)
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n', encoding="utf-8");print(a.output)
    except (KeyError,ValueError,TypeError,OSError)as exc:p.exit(2,f'Input error: {exc}\n')
if __name__=='__main__':main()
