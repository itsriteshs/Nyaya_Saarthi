"""Compare general intent features on grouped dev only; never reads grouped-test text or UAT cases."""
import csv,json,hashlib,time
from pathlib import Path
import joblib,numpy as np
from sklearn.pipeline import Pipeline,FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import f1_score,accuracy_score
from app.config import BACKEND_DIR,DATASET_DIR
from app.services.nlp.preprocessing import normalize_text
from app.services.nlp.ontology import ontology

manifest=BACKEND_DIR/'experiments/manifests/phase6_grouped_split.csv'
split={r['utterance_id']:r['split'] for r in csv.DictReader(manifest.open(encoding='utf-8'))}
rows=[r for r in csv.DictReader((DATASET_DIR/'annotated_utterances.csv').open(encoding='utf-8-sig')) if split.get(r['utterance_id']) in {'train','dev'}]
train=[r for r in rows if split[r['utterance_id']]=='train'];dev=[r for r in rows if split[r['utterance_id']]=='dev']
x=[normalize_text(r['text']) for r in train];y=[r['primary_intent_id'] for r in train]
for key,r in ontology()['intents'].items():
 x.extend([normalize_text(r['intent_name'].replace('_',' ')),normalize_text(r['description']+' '+r['typical_user_goal'])]);y.extend([key,key])
xd=[normalize_text(r['text']) for r in dev];yd=[r['primary_intent_id'] for r in dev]
def word():return TfidfVectorizer(ngram_range=(1,2),min_df=1,max_features=100000,token_pattern=r'(?u)[^\s,.!?।:;]+')
def char():return TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,max_features=100000)
candidates={'existing':joblib.load(BACKEND_DIR/'artifacts/intent_model.joblib'),
 'word':Pipeline([('features',word()),('classifier',LinearSVC(random_state=471))]),
 'word_char':Pipeline([('features',FeatureUnion([('word',word()),('char',char())])),('classifier',LinearSVC(random_state=471))])}
report={'train':len(train),'dev':len(dev),'ontologyExamples':len(x)-len(train),'testEvaluated':0,'uatUsedForSelection':False,'manifestSHA256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'results':{}}
for name,model in candidates.items():
 t=time.perf_counter()
 if name!='existing':model.fit(x,y)
 p=model.predict(xd)
 report['results'][name]={'accuracy':float(accuracy_score(yd,p)),'macroF1':float(f1_score(yd,p,average='macro',zero_division=0)),'seconds':time.perf_counter()-t}
 print(name,report['results'][name],flush=True)
report['note']='Development-only comparison on reused synthetic/unreviewed dev labels. No automatic model promotion and no new held-out claim.'
(BACKEND_DIR/'reports/uat_intent_dev_candidates.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
