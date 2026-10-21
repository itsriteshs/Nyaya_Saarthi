"""Synthetic HTTP rechecks, separate from browser evidence and held-out NLP evaluation."""
import csv,json,time,argparse
from pathlib import Path
from uuid import uuid4
from urllib.request import Request,urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
ISSUES=['INT002','INT002','INT002','INT045','INT032','INT019','INT016','INT025','INT036','INT048','INT053','INT048','INT040','INT032','INT031','INT001','INT002','OUT_OF_SCOPE','INT002','INT002']

def run(base):
    results=[]
    cases=list(csv.DictReader((ROOT/'reports/FINAL_USER_SCENARIOS.csv').open(encoding='utf-8-sig')))[:20]
    for index,row in enumerate(cases,1):
        entry={'scenario':row['scenario_id'],'input':row['initial_query'],'transport':'HTTP','events':[],'answers':[]}
        def call(method,path,payload=None,expected=200):
            started=time.perf_counter();req=Request(base+'/api/v1'+path,data=json.dumps(payload).encode() if payload is not None else None,method=method,headers={'Content-Type':'application/json'})
            try:
                with urlopen(req,timeout=150) as response:status=response.status;data=json.load(response)
            except HTTPError as error:status=error.code;data=json.load(error)
            entry['events'].append({'method':method,'path':path,'status':status,'seconds':time.perf_counter()-started})
            if status!=expected:raise AssertionError((path,status,data))
            return data
        try:
            m=call('POST','/matters',{'originalText':row['initial_query'],'language':'auto'},201);path='/matters/'+m['id']
            m=call('POST',path+'/analyze',{'revision':m['revision'],'referenceDatetime':'2026-10-20T12:00:00+05:30'});entry['initial']=m
            issue=ISSUES[index-1]
            for turn in range(25):
                q=m.get('currentQuestion')
                if not q:break
                slot=q['slot']
                if slot.startswith('INTENT'):answer=issue
                elif index==16:answer=["I don't know",'Not sure','Mujhe nahi pata'][turn%3]
                else:
                    values={'VEHICLE_CLASS':'HGV' if index in {12,13} else 'MCWG' if index in {3,5} else 'car',
                        'OBSERVED_SPEED':'120 km/h' if index==1 else '90 km/h','ROAD_TYPE':'expressway' if index==1 else 'city road',
                        'STATE':'Tamil Nadu' if index in {1,2,3,20} else 'Kerala','DESTINATION_STATE':'Karnataka',
                        'EVENT_DATE':'2026-10-19','CHALLAN_DATE':'2026-10-19','LICENCE_EXPIRY_DATE':'2026-09-15',
                        'USER_ROLE':'witness' if index==12 else 'applicant' if index in {6,7} else 'buyer' if index==8 else 'driver',
                        'LOCATION':'Kochi public parking','CITY':'Kochi','ROAD_NAME':'A city road',
                        'LICENCE_STATUS':'expired','RC_STATUS':'transfer pending','INSURANCE_STATUS':'expired',
                        'INJURY_PRESENT':'yes' if index==11 else 'no','DEATH_PRESENT':'no','EVIDENCE_AVAILABLE':'yes',
                        'POLICE_REPORTED':'no','OTHER_VEHICLE_IDENTIFIED':'yes','ACCIDENT_TYPE':'road accident',
                        'CHALLAN_STATUS':'disputed','PUC_STATUS':'expired','LICENCE_CLASS':'LMV'}
                    answer=values.get(slot,'I do not know')
                    if index==4 and slot=='CHALLAN_DATE':answer='2026-10-19; a car in Kerala; the photo shows a different number plate'
                if index==15 and slot=='EVENT_DATE':answer='2026-10-19; insurance expired'
                if index==17 and slot=='VEHICLE_CLASS':answer='Sorry, I meant a car, not a bike.'
                entry['answers'].append({'question':q,'answer':answer})
                m=call('POST',path+'/answers',{'revision':m['revision'],'questionId':q['id'],'messageId':str(uuid4()),'answer':answer})
            if issue=='OUT_OF_SCOPE':
                call('POST',path+'/verify',{'revision':m['revision'],'acknowledgeUnknowns':True},409)
                assert m['conversation']['intentUnsupported'] and not m.get('guidance')
                entry['result']='SAFE_OUTSIDE_SCOPE'
            else:
                if m.get('currentQuestion'):raise AssertionError('Question unresolved after bounded replies: '+str(m['currentQuestion']))
                # Exercise explicit corrections and preserve their provenance.
                if index==17:
                    f=next(f for f in m['facts'] if f['key']=='VEHICLE_CLASS')
                    m=call('PATCH',path+'/facts/'+f['id'],{'revision':m['revision'],'value':'car'})
                    assert next(item for item in m['facts'] if item['id']==f['id'])['normalizedId']=='VC_MOTORCAR'
                if index==15:
                    assert any(h['action']=='resolve_contradiction' for h in m['conversation']['factHistory']), 'Correction was not explicitly resolved'
                for fact in list(m['facts']):
                    if fact.get('resolutionStatus')=='resolved':m=call('POST',path+'/facts/'+fact['id']+'/confirm',{'revision':m['revision']})
                m=call('POST',path+'/verify',{'revision':m['revision'],'acknowledgeUnknowns':True})
                m=call('POST',path+'/guidance',{'revision':m['revision']})
                guidance=m['guidance'];assert guidance['metadata']['generationMethod']!='LOCAL_LLM'
                m=call('POST',path+'/complete',{'revision':m['revision']})
                restored=call('GET',path);assert restored['facts']==m['facts'],'Persisted facts differ';assert restored['guidance']==m['guidance'],'Persisted guidance differs'
                entry['result']='DETERMINISTIC_JOURNEY_COMPLETED'
            entry['final']=m
        except Exception as error:entry['result']='FAIL';entry['error']=type(error).__name__+': '+str(error)
        results.append(entry)
        print(entry['scenario'],entry['result'],entry.get('error',''),flush=True)
    (ROOT/'reports/uat_recheck_after_http.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='http://127.0.0.1:8012');args=parser.parse_args();run(args.base)
