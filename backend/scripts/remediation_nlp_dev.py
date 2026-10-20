"""Paired development diagnostics. Never evaluates grouped test or gold cases."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from app.config import BACKEND_DIR, DATASET_DIR
from app.services.nlp.entity_extractor import extract, build_status_vocabulary
from app.services.nlp.normalizer import normalize
from app.services.nlp.slot_detector import detect_slots
from app.services.nlp.ontology import ontology
from app.services.nlp.preprocessing import normalize_text
from scripts.phase6_nlp_experiment import prf
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC


def run(label, baseline=False, runtime=False):
    global extract, normalize, detect_slots, build_status_vocabulary
    if baseline:
        frozen=json.loads((BACKEND_DIR/'experiments/manifests/remediation_nlp_baseline_sources.json').read_text(encoding='utf-8'))
        modules={}
        for name, source in frozen.items():
            namespace={'__name__':f'remediation_baseline_{name}'}
            exec(compile(source,f'frozen_baseline/{name}.py','exec'),namespace)
            modules[name]=namespace
        extract=modules['entity_extractor']['extract']
        build_status_vocabulary=modules['entity_extractor']['build_status_vocabulary']
        normalize=modules['normalizer']['normalize']
        detect_slots=modules['slot_detector']['detect_slots']
    manifest = BACKEND_DIR / 'experiments/manifests/phase6_grouped_split.csv'
    assignment = {r['utterance_id']: r['split'] for r in csv.DictReader(manifest.open(encoding='utf-8'))}
    # Filter before decoding labels, annotations, or text; test rows are unused.
    rows = [r for r in csv.DictReader((DATASET_DIR/'annotated_utterances.csv').open(encoding='utf-8-sig'))
            if assignment.get(r['utterance_id']) in {'train', 'dev'}]
    train = [r for r in rows if assignment[r['utterance_id']] == 'train']
    dev = [r for r in rows if assignment[r['utterance_id']] == 'dev']
    model = Pipeline([('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=2, max_features=100000)),
                      ('classifier', LinearSVC(random_state=471))])
    model.fit([normalize_text(r['text']) for r in train], [r['primary_intent_id'] for r in train])
    if runtime:
        import joblib
        model=joblib.load(BACKEND_DIR/'artifacts/intent_model.joblib')
    predicted = model.predict([normalize_text(r['text']) for r in dev])
    vocab = build_status_vocabulary({r['utterance_id'] for r in train})
    totals = defaultdict(Counter); slots = defaultdict(Counter); intents = defaultdict(Counter)
    records = []; mismatches = Counter()
    for row, intent in zip(dev, predicted):
        entities = [normalize(e) for e in extract(row['text'], status_values=vocab)]
        gold = set(filter(None, row['missing_slots'].split('|')))
        annotations = json.loads(row['entity_annotations_json'] or '[]')
        oracle = [{'type': e['slot_name'], 'status': 'resolved', 'normalizedValue': e['value']} for e in annotations]
        predictions = {
            'endToEnd': {s['slot'] for s in detect_slots(str(intent), entities)['missingSlots']},
            'oracleIntent': {s['slot'] for s in detect_slots(row['primary_intent_id'], entities)['missingSlots']},
            'oracleEntitiesAndIntent': {s['slot'] for s in detect_slots(row['primary_intent_id'], oracle)['missingSlots']}}
        for kind, found in predictions.items():
            for metric, values in [('tp', found & gold), ('fp', found - gold), ('fn', gold - found)]:
                totals[kind][metric] += len(values)
                if kind == 'endToEnd':
                    for slot in values:
                        slots[slot][metric] += 1; intents[row['primary_intent_id']][metric] += 1
            totals[kind]['exact'] += found == gold
        schema = {r['slot_name']: r['required_level'] for r in ontology()['slots'].get(row['primary_intent_id'], [])}
        for slot in gold:
            if schema.get(slot) != 'required': mismatches['gold_missing_nonrequired_or_absent_schema'] += 1
        records.append({'id': row['utterance_id'], 'intent': row['primary_intent_id'], 'predictedIntent': str(intent),
                        'gold': sorted(gold), **{k: sorted(v) for k, v in predictions.items()}, 'entities': entities})
    result = {'partition': 'development only; synthetic unreviewed labels; no independent final evaluation',
              'classifier': 'production grouped model with catalog-wide descriptions' if runtime else 'fixed Phase 6 grouped character SVM',
              'counts': {'train': len(train), 'dev': len(dev), 'testEvaluated': 0},
              'manifestSHA256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
              'intentErrors': sum(r['intent'] != r['predictedIntent'] for r in records),
              'labelMismatches': dict(mismatches),
              'metrics': {k: {**prf(v['tp'], v['fp'], v['fn']), 'exactSetAccuracy': v['exact']/len(dev)} for k,v in totals.items()},
              'bySlot': {k: prf(v['tp'],v['fp'],v['fn']) for k,v in sorted(slots.items())},
              'byIntent': {k: prf(v['tp'],v['fp'],v['fn']) for k,v in sorted(intents.items())}}
    base = BACKEND_DIR/'experiments'
    output = base/'metrics'/f'remediation_nlp_{label}.json'
    if output.exists(): raise FileExistsError(output)
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    (base/'predictions'/f'remediation_nlp_{label}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--label', required=True); parser.add_argument('--baseline',action='store_true');parser.add_argument('--runtime',action='store_true')
    args=parser.parse_args();run(args.label,args.baseline,args.runtime)
