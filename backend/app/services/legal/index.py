"""Reproducible provision index and small-corpus BM25/semantic retrieval."""
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from math import log
from pathlib import Path
import json
import re
import numpy as np
from app.config import BACKEND_DIR
from app.services.legal.knowledge import load_knowledge, fingerprint
from app.services.legal.policy import provision_policy

INDEX_DIR = BACKEND_DIR / 'artifacts' / 'legal_index'
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
MODEL_LICENSE = 'Apache-2.0'

def tokens(text):
    return re.findall(r'[\w\u0900-\u097f]+', text.casefold(), re.UNICODE)

def documents(knowledge):
    tables=knowledge['tables'];out=[];excluded=[]
    for provision_id,row in tables['provisions'].items():
        policy=provision_policy(row,knowledge)
        if policy['status']!='eligible':
            excluded.append({'id':provision_id,'kind':'provision','reasons':policy['reasons']})
            continue
        source=tables['sources'][row['source_id']]
        related=[r['rule_name'] for r in tables['rules'].values() if r.get('provision_id')==provision_id
                 and r.get('review_status')=='VERIFIED']
        domains=sorted({r['domain'] for r in tables['rules'].values() if r.get('provision_id')==provision_id})
        text=' '.join(filter(None,[row['topic'],row['section_rule_number'],row['official_text'],
                                  row['normalized_text'],' '.join(related)]))
        out.append({'documentId':f'provision:{provision_id}','evidenceId':f'EVID:{provision_id}',
                    'recordId':provision_id,'kind':'provision','sourceId':source['source_id'],
                    'title':f"{source['source_title']} · {row['section_rule_number']}",
                    'text':text,'passage':row['normalized_text'] or row['official_text'],
                    'domains':domains,
                    'authority':source['issuing_authority'],'jurisdictionId':row['jurisdiction_id'],
                    'effectiveFrom':row['effective_from'],'effectiveTo':row['effective_to'],
                    'sourceUrl':source['official_url'],'reviewStatus':row['review_status'],
                    'sourceReviewStatus':source['review_status'],'file':row['_file'],'row':row['_row']})
    return out,excluded

def build(semantic=True):
    knowledge=load_knowledge();docs,excluded=documents(knowledge)
    INDEX_DIR.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(docs,ensure_ascii=False,sort_keys=True).encode()
    (INDEX_DIR/'documents.json').write_bytes(payload)
    capability='lexical-only'
    model_revision=None
    if semantic:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError('Install backend/requirements-semantic.txt, then rerun the index build') from exc
        model_path=INDEX_DIR/'embedding_model'
        model=SentenceTransformer(MODEL_NAME,cache_folder=str(INDEX_DIR/'model_cache'))
        model.save(str(model_path))
        vectors=model.encode([d['text'] for d in docs],normalize_embeddings=True,show_progress_bar=False)
        np.save(INDEX_DIR/'vectors.npy',np.asarray(vectors,dtype='float32'))
        capability='hybrid'
        model_revision=getattr(getattr(model,'_first_module',lambda:None)(),'auto_model',None)
        model_revision=getattr(getattr(model_revision,'config',None),'_commit_hash',None)
        if not model_revision:
            model_revision='local-sha256:'+sha256((model_path/'model.safetensors').read_bytes()).hexdigest()[:20]
    else:
        (INDEX_DIR/'vectors.npy').unlink(missing_ok=True)
    version=sha256((knowledge['fingerprint']+sha256(payload).hexdigest()+capability+str(model_revision)).encode()).hexdigest()[:16]
    manifest={'indexVersion':version,'sourceFingerprint':knowledge['fingerprint'],
              'documentCount':len(docs),'excludedProvisionCount':len(excluded),
              'excludedProvisions':excluded,'malformedRecords':knowledge['excluded'],
              'retrievalMode':capability,'embeddingModel':MODEL_NAME if semantic else None,
              'embeddingModelRevision':model_revision,'embeddingModelLicense':MODEL_LICENSE if semantic else None,
              'rankFusion':'RRF(k=60); lexical and semantic ranks equally weighted',
              'documentSha256':sha256(payload).hexdigest()}
    (INDEX_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    load_index.cache_clear()
    return manifest

@lru_cache(maxsize=1)
def load_index():
    manifest,docs=load_manifest()
    vectors=None;model=None
    if manifest['retrievalMode']=='hybrid':
        if not (INDEX_DIR/'vectors.npy').is_file():raise FileNotFoundError('Legal semantic index is missing; rebuild')
        vectors=np.load(INDEX_DIR/'vectors.npy')
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError('Install semantic requirements to use this hybrid index') from exc
        model=SentenceTransformer(str(INDEX_DIR/'embedding_model'),local_files_only=True)
    return manifest,docs,vectors,model

def load_manifest():
    manifest_path=INDEX_DIR/'manifest.json'
    if not manifest_path.is_file():raise FileNotFoundError('Build the legal index first')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['sourceFingerprint']!=fingerprint():raise ValueError('Legal index is stale; rebuild it from current datasets')
    raw=(INDEX_DIR/'documents.json').read_bytes()
    if sha256(raw).hexdigest()!=manifest['documentSha256']:raise ValueError('Legal index documents have changed; rebuild')
    docs=json.loads(raw)
    return manifest,docs

def bm25(query, docs):
    query_terms=tokens(query)
    tokenized=[tokens(d['text']) for d in docs]
    lengths=[len(t) for t in tokenized]
    avg=sum(lengths)/len(lengths) if lengths else 1
    df=Counter(term for row in tokenized for term in set(row))
    scores=[];n=len(docs)
    for row,length in zip(tokenized,lengths):
        freq=Counter(row);score=0.0
        for term in query_terms:
            if not freq[term]:continue
            idf=log(1+(n-df[term]+.5)/(df[term]+.5))
            score+=idf*(freq[term]*2.2)/(freq[term]+1.2*(.25+.75*length/avg))
        scores.append(score)
    return scores

def retrieve(query, event_date=None, jurisdiction_id=None, limit=5, domains=None):
    from app.services.legal.policy import provision_policy
    manifest,all_docs,vectors,model=load_index();knowledge=load_knowledge()
    if manifest['sourceFingerprint']!=fingerprint():
        raise ValueError('Legal index is stale; rebuild it from current datasets')
    candidates=[];excluded=[]
    for index,doc in enumerate(all_docs):
        if domains is not None and not set(doc.get('domains',[])).intersection(domains):
            excluded.append({'id':doc['recordId'],'status':'excluded','reasons':['DOMAIN_MISMATCH']})
            continue
        row=knowledge['tables']['provisions'][doc['recordId']]
        policy=provision_policy(row,knowledge,event_date,jurisdiction_id)
        if not event_date or not jurisdiction_id:
            reasons=policy['reasons']+(['DATE_APPLICABILITY_UNKNOWN'] if not event_date else [])+(['JURISDICTION_UNRESOLVED'] if not jurisdiction_id else [])
            policy={'status':'conditional','reasons':reasons}
        if policy['status']=='eligible':candidates.append((index,doc))
        else:excluded.append({'id':doc['recordId'],'status':policy['status'],'reasons':policy['reasons']})
    docs=[d for _,d in candidates]
    lexical=bm25(query,docs)
    lex_rank=sorted(range(len(docs)),key=lambda i:(-lexical[i],docs[i]['recordId']))
    semantic=[None]*len(docs);sem_rank=[]
    if model is not None and docs:
        query_vector=model.encode([query],normalize_embeddings=True,show_progress_bar=False)[0]
        semantic=(vectors[[i for i,_ in candidates]]@query_vector).tolist()
        sem_rank=sorted(range(len(docs)),key=lambda i:(-semantic[i],docs[i]['recordId']))
    rank_score=Counter()
    for order in (lex_rank,sem_rank):
        for rank,i in enumerate(order,1):rank_score[i]+=1/(60+rank)
    ranked=sorted(range(len(docs)),key=lambda i:(-rank_score[i],docs[i]['recordId']))[:limit]
    results=[]
    for rank,i in enumerate(ranked,1):
        if lexical[i]<=0 and (semantic[i] is None or semantic[i]<=0):continue
        results.append({**docs[i],'rank':rank,'lexicalScore':round(lexical[i],5),
                        'semanticScore':round(semantic[i],5) if semantic[i] is not None else None,
                        'combinedRankScore':round(rank_score[i],7),'admissibility':'eligible',
                        'relevanceReason':'Text similarity only; applicability requires separate rule evaluation.'})
    return {'indexVersion':manifest['indexVersion'],'sourceFingerprint':manifest['sourceFingerprint'],
            'retrievalMode':manifest['retrievalMode'],'results':results,'excluded':excluded}
