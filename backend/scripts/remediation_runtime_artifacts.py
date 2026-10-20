"""Rebuild missing local classifier artifacts from grouped TRAIN only.

Fixed Phase 6 character-SVM architecture; dev sets uncertainty cutoffs only.
No gold or grouped test examples are trained on or evaluated here.
"""
import csv
import hashlib
import json
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from app.config import BACKEND_DIR, DATASET_DIR
from app.services.nlp.preprocessing import normalize_text
from app.services.nlp.ontology import ontology


def run():
    manifest=BACKEND_DIR/'experiments/manifests/phase6_grouped_split.csv'
    split={r['utterance_id']:r['split'] for r in csv.DictReader(manifest.open(encoding='utf-8'))}
    rows=[r for r in csv.DictReader((DATASET_DIR/'annotated_utterances.csv').open(encoding='utf-8-sig'))
          if split.get(r['utterance_id']) in {'train','dev'}]
    train=[r for r in rows if split[r['utterance_id']]=='train'];dev=[r for r in rows if split[r['utterance_id']]=='dev']
    for kind,target,grams,max_features in [('intent','primary_intent_id',(3,5),100000),('language','language',(2,5),80000)]:
        model=Pipeline([('tfidf',TfidfVectorizer(analyzer='char_wb',ngram_range=grams,min_df=2,max_features=max_features)),
                        ('classifier',LinearSVC(random_state=471))])
        texts=[normalize_text(r['text']) for r in train]
        labels=[r[target].lower() if kind=='language' else r[target] for r in train]
        # Catalog-wide intent descriptions help short queries whose domain phrase
        # is swamped by synthetic context in the utterance corpus. No test/gold
        # examples or per-query routing rules are used.
        if kind=='intent':
            for intent_id,row in ontology()['intents'].items():
                texts.extend([normalize_text(row['intent_name'].replace('_',' ')),
                              normalize_text(row['description']+' '+row['typical_user_goal'])])
                labels.extend([intent_id,intent_id])
        model.fit(texts,labels)
        ontology_examples=len(texts)-len(train)
        texts=[normalize_text(r['text']) for r in dev];scores=np.sort(model.decision_function(texts),axis=1)
        gaps=scores[:,-1]-scores[:,-2]
        predicted=model.predict(texts);truth=np.array([r[target].lower() if kind=='language' else r[target] for r in dev])
        correct=predicted==truth
        metadata={'model_version':f'tfidf-{kind}-grouped-v1','train_count':len(train),'dev_count':len(dev),
                  'test_evaluated':0,'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
                  'uncertainty_gap_threshold':float(np.quantile(gaps[correct],.10)),
                  'score_type':'SVM decision margin gap, not probability','random_seed':471,
                  'sklearn_version':__import__('sklearn').__version__,'review_status':'annotations unreviewed'}
        metadata['ontology_examples']=ontology_examples
        joblib.dump(model,BACKEND_DIR/f'artifacts/{kind}_model.joblib',compress=3)
        (BACKEND_DIR/f'artifacts/{kind}_model_metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        print(kind,metadata)


if __name__=='__main__':run()
