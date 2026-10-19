"""Exploratory evaluation on derived held-out annotations; not a reviewed benchmark."""
import csv
import json
import time
from collections import Counter,defaultdict
from sklearn.metrics import accuracy_score,classification_report,confusion_matrix,precision_recall_fscore_support
from app.config import BACKEND_DIR,DATASET_DIR,REPORT_DIR
from app.services.dataset_loader import load_dataset
from app.services.nlp.pipeline import analyze
from app.services.nlp.preprocessing import text_template
from scripts.prepare_nlp_data import MANIFEST

SUPPORTED={'VEHICLE_CLASS','OBSERVED_SPEED','ROAD_TYPE','STATE','EVENT_DATE','INSURANCE_STATUS','CHALLAN_STATUS','LICENCE_STATUS','AGE'}

def run():
    with MANIFEST.open(encoding='utf-8',newline='') as f: assignments={x['utterance_id']:x['derived_split'] for x in csv.DictReader(f)}
    _,raw=load_dataset(DATASET_DIR/'annotated_utterances.csv')
    tests=[row for _,row in raw if isinstance(row,dict) and assignments.get(row.get('utterance_id'))=='test']
    y_true=[];y_pred=[];lang_true=[];lang_pred=[]
    entity_tp=entity_fp=entity_fn=0
    by_type=defaultdict(Counter)
    slot_tp=slot_fp=slot_fn=slot_exact=0
    latencies=[];errors=[]
    for row in tests:
        start=time.perf_counter()
        try:r=analyze(row['text'],'auto')
        except Exception as exc:
            errors.append({'id':row['utterance_id'],'error':type(exc).__name__})
            continue
        latencies.append((time.perf_counter()-start)*1000)
        y_true.append(row['primary_intent_id']);y_pred.append(r.intent.id)
        lang_true.append(row['language'].lower());lang_pred.append(r.language.detectedLanguage)
        expected=json.loads(row['entity_annotations_json'] or '[]')
        gold={(e['slot_name'],e['start'],e['end']) for e in expected if e.get('slot_name') in SUPPORTED and isinstance(e.get('start'),int) and isinstance(e.get('end'),int)}
        predicted={(e.type,e.start,e.end) for e in r.entities if e.type in SUPPORTED}
        entity_tp+=len(gold&predicted);entity_fp+=len(predicted-gold);entity_fn+=len(gold-predicted)
        for item in gold&predicted:by_type[item[0]]['tp']+=1
        for item in predicted-gold:by_type[item[0]]['fp']+=1
        for item in gold-predicted:by_type[item[0]]['fn']+=1
        expected_slots=set(filter(None,row['missing_slots'].split('|')))
        predicted_slots={x.slot for x in r.missingSlots}
        slot_tp+=len(expected_slots&predicted_slots);slot_fp+=len(predicted_slots-expected_slots);slot_fn+=len(expected_slots-predicted_slots)
        slot_exact+=expected_slots==predicted_slots
    def prf(tp,fp,fn):
        return {'precision':tp/(tp+fp) if tp+fp else 0.0,'recall':tp/(tp+fn) if tp+fn else 0.0,
                'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0,'tp':tp,'fp':fp,'fn':fn}
    labels=sorted(set(y_true)|set(y_pred))
    confusion=confusion_matrix(y_true,y_pred,labels=labels)
    mistakes=[{'true':a,'predicted':b,'count':n} for (a,b),n in Counter((a,b) for a,b in zip(y_true,y_pred) if a!=b).most_common(30)]
    _,gold_raw=load_dataset(DATASET_DIR/'gold_evaluation_cases.csv')
    gold=[row for _,row in gold_raw if isinstance(row,dict)]
    train_dev_templates={text_template(row['text']) for _,row in raw if isinstance(row,dict) and assignments.get(row.get('utterance_id')) in {'train','dev'}}
    gold_overlap=sum(text_template(row['natural_query']) in train_dev_templates for row in gold)
    model_meta=json.loads((BACKEND_DIR/'artifacts'/'intent_model_metadata.json').read_text())
    language_meta=json.loads((BACKEND_DIR/'artifacts'/'language_model_metadata.json').read_text())
    result={'evaluation_label':'exploratory; annotations pending human review',
      'model_version':model_meta['model_version'],'language_model_version':language_meta['model_version'],
      'manifest_sha256':model_meta['manifest_sha256'],'dataset':'annotated_utterances.csv','split':'derived test; original test rows only',
      'sample_count':len(tests),'processed_count':len(y_true),'errors':errors,
      'intent':{'accuracy':accuracy_score(y_true,y_pred),'per_intent':classification_report(y_true,y_pred,labels=labels,output_dict=True,zero_division=0),
                'labels':labels,'confusion_matrix':confusion.tolist(),'top_misclassifications':mistakes},
      'language':classification_report(lang_true,lang_pred,labels=['english','hindi','hinglish','mixed','uncertain'],output_dict=True,zero_division=0),
      'entity_exact_span':{**prf(entity_tp,entity_fp,entity_fn),'by_type':{k:prf(v['tp'],v['fp'],v['fn']) for k,v in by_type.items()}},
      'missing_slots':{**prf(slot_tp,slot_fp,slot_fn),'exact_set_accuracy':slot_exact/len(y_true) if y_true else 0.0,
                       'note':'Dataset missing-slot labels may include optional/conditional slots; Phase 2 detector only requires explicit required slots.'},
      'normalization':{'status':'not_measurable','reason':'No reviewed normalized IDs or canonical values are supplied as ground truth.'},
      'gold_cases':{'count':len(gold),'overlap_with_derived_train_or_dev_templates':gold_overlap,
                    'status':'not used for model selection or independent metrics; legal reviewer pending'},
      'latency_ms':{'sample_count':len(latencies),'mean':sum(latencies)/len(latencies) if latencies else None,
                    'max':max(latencies) if latencies else None,'environment':'local Python 3.12 process; warmed model cache'},
      'limitations':['Synthetic templating can inflate held-out results despite template exclusion.',
                     'Digit-masked template matching does not detect all paraphrases.',
                     'Every utterance has pending human review.']}
    REPORT_DIR.mkdir(parents=True,exist_ok=True)
    (REPORT_DIR/'nlp_evaluation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    lines=['# NLP exploratory evaluation','',f"- Model: {result['model_version']}",f"- Manifest SHA-256: {result['manifest_sha256']}",
           f"- Derived test rows: {len(tests)}; processed: {len(y_true)}",f"- Intent accuracy: {result['intent']['accuracy']:.4f}",
           f"- Intent macro F1: {result['intent']['per_intent']['macro avg']['f1-score']:.4f}",
           f"- Intent weighted F1: {result['intent']['per_intent']['weighted avg']['f1-score']:.4f}",
           f"- Language accuracy: {result['language']['accuracy']:.4f}",
           f"- Entity exact-span F1: {result['entity_exact_span']['f1']:.4f}",
           f"- Missing-slot F1: {result['missing_slots']['f1']:.4f}",
           f"- Gold cases: {len(gold)}; template overlap with derived train/dev: {gold_overlap}",
           f"- Mean inference latency: {result['latency_ms']['mean']:.2f} ms across {len(latencies)} cases",'','## Limits','']
    lines.extend(f'- {x}' for x in result['limitations'])
    lines+=['','Full per-intent metrics, confusion matrix, language breakdown, entity-type results, and sample counts are in `nlp_evaluation.json`.']
    (REPORT_DIR/'nlp_evaluation.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return result
if __name__=='__main__':
    r=run();print(json.dumps({'intent_accuracy':r['intent']['accuracy'],'entity_f1':r['entity_exact_span']['f1'],'slot_f1':r['missing_slots']['f1'],'processed':r['processed_count']},indent=2))
