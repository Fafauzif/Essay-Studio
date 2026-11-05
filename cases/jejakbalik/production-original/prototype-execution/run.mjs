import {createScenario,planScenario,changeScenario} from './model.ts';
import fs from 'node:fs/promises';import {createHash} from 'node:crypto';import assert from 'node:assert/strict';
const sources={};for(const f of ['model.ts','seed.ts','types.ts']) sources[f]=createHash('sha256').update(await fs.readFile('/workspace/scratch/91cdcc6b9385/JejakBalik-Prototype/src/recovery/'+f)).digest('hex');
const definitions=[
 ['base','Semua penyedia tersedia',s=>{}],
 ['lintas_only','Hanya Lintas Paket',s=>s.journeys.forEach(j=>j.available=j.providerId==='lintas')],
 ['sela_only','Hanya Sela Kurir',s=>s.journeys.forEach(j=>j.available=j.providerId==='sela')],
 ['angkut_only','Hanya Angkut Aman',s=>s.journeys.forEach(j=>j.available=j.providerId==='angkut')],
 ['no_lintas','Lintas Paket tidak tersedia',s=>s.journeys.forEach(j=>{if(j.providerId==='lintas')j.available=false})],
 ['no_sela','Sela Kurir tidak tersedia',s=>s.journeys.forEach(j=>{if(j.providerId==='sela')j.available=false})],
 ['no_angkut','Angkut Aman tidak tersedia',s=>s.journeys.forEach(j=>{if(j.providerId==='angkut')j.available=false})],
 ['budget_300000','Anggaran Rp300.000',s=>s.budgetIdr=300000],
 ['receiver_capacity_zero','Semua kapasitas penerima nol',s=>s.receivers.forEach(r=>r.capacitySlots=0)],
 ['all_journeys_unavailable','Semua perjalanan tidak tersedia',s=>s.journeys.forEach(j=>j.available=false)],
];
const results=[];
for(const [id,label,mutate]of definitions){
 const initial=createScenario();const s=id==='base'?initial:changeScenario(initial,mutate);const p=planScenario(s);
 const accepted=s.requests.filter(r=>p.assignments.some(a=>a.requestId===r.id));
 const categoryCoverage=Object.fromEntries([...new Set(s.requests.map(r=>r.category))].map(c=>[c,{requested:s.requests.filter(r=>r.category===c).length,served:accepted.filter(r=>r.category===c).length}]));
 const handlingCoverage=Object.fromEntries(['ordinary','bulky','specialist'].map(c=>[c,{requested:s.requests.filter(r=>r.handling===c).length,served:accepted.filter(r=>r.handling===c).length}]));
 const providersUsed=[...new Set(p.assignments.map(a=>s.journeys.find(j=>j.id===a.journeyId).providerId))];
 const rejectionCodes={};for(const r of p.rejections)rejectionCodes[r.code]=(rejectionCodes[r.code]||0)+1;
 assert.equal(p.served,accepted.length);assert(p.totalCostIdr<=s.budgetIdr);assert.equal(p.totalCostIdr,p.routes.reduce((t,r)=>t+r.costIdr,0));assert.equal(p.served+p.rejections.length,s.requests.length);
 results.push({id,label,requests:s.requests.length,served:p.served,unserved:s.requests.length-p.served,budgetIdr:s.budgetIdr,addedKm:p.addedKm,totalCostIdr:p.totalCostIdr,additionalMinutes:p.addedMinutes,baselineFeasible:p.baselineFeasible,baselineServed:p.baselineServed,baselineKm:p.baselineKm,baselineCostIdr:p.baselineCostIdr,outstandingHandlingAllowanceIdr:p.outstandingCostIdr,providerPaymentIdr:p.routes.reduce((t,r)=>t+r.driverPaymentIdr,0),handlingAllowanceIdr:p.routes.reduce((t,r)=>t+r.handlingCostIdr,0),providersUsed,categoryCoverage,handlingCoverage,rejectionCodes,assignments:p.assignments});
}
const b=results[0];assert.equal(b.served,18);assert.equal(b.addedKm,28.8);assert.equal(b.totalCostIdr,438700);assert.equal(b.baselineKm,112.8);assert.equal(b.baselineCostIdr,662400);assert.equal(b.outstandingHandlingAllowanceIdr,262500);
const out={status:'Exploratory executed software scenarios using authored fictional inputs; not field evidence, partner performance or forecast',executionDate:'2026-11-04',sourceCommit:'82c86a9e9a7664bf74c4da9c1d84a51d2bbe47fb',executionMethod:'Node.js24 native TypeScript type stripping; byte-for-byte source copied into a scratch execution folder, with only relative module specifiers given .ts suffixes for ESM resolution; repository source unchanged',sourceFiles:sources,sourcePaths:['src/recovery/model.ts','src/recovery/seed.ts','src/recovery/types.ts'],boundary:'Each case begins from fresh pre-departure reference scenario. Existing origin, forward stops and destination remain. Only indicated availability, budget or receiver-capacity input changes. No approval or service event is executed.',comparisonBoundary:'Each case baseline serves only that case accepted workload. Restricted-provider cases usually serve fewer devices. Do not compare costs or kilometres across unequal-service cases as savings. This exploratory ablation shows coverage dependence on offered provider capabilities and journey options, not an isolated empirical cross-provider efficiency effect.',fieldSemantics:{served:'Requests assigned in the pre-departure plan, not completed recoveries',baselineFeasible:'Operational service coverage for the accepted workload only; does not mean within scenario budget. Zero accepted requests yields true vacuously.',baselineServed:'Dedicated grouped collection service for that case accepted workload',outstandingHandlingAllowanceIdr:'All accepted handling allowances remain outstanding before service events; distinct from total service cost'},domainTests:{command:'npm test -- tests/domain/recovery-v3.test.ts',passed:17,failed:0,observedDate:'2026-11-04'},checks:'10 case accounting/coverage/budget identities and canonical reference values passed',results:results};
await fs.writeFile('/workspace/scratch/91cdcc6b9385/production/prototype_scenarios.json',JSON.stringify(out,null,2));
console.log(results.map(r=>`${r.id}: ${r.served}/${r.requests}, ${r.addedKm}km, Rp${r.totalCostIdr}, baseline ${r.baselineServed}/${r.served}, outstanding Rp${r.outstandingHandlingAllowanceIdr}`).join('\n'));
