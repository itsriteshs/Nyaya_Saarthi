import pytest
from test_slm_intake import Provider
from app.services.nlp import slm_extractor as intake


def test_failure_never_calls_legacy_extractor(monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    def forbidden(*args,**kwargs):
        pytest.fail('Production intake must not fall back to rules')
    monkeypatch.setattr('app.services.nlp.entity_extractor.extract',forbidden)
    with pytest.raises(intake.IntakeFailure) as caught:
        intake.interpret('150 speed',provider=Provider(error='INFERENCE_TIMEOUT'))
    assert not caught.value.metadata['fallbackUsed']


def test_busy_is_retryable_without_extraction(monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    class Busy:
        def acquire(self,**kwargs):return False
    monkeypatch.setattr(intake,'_gate',Busy())
    with pytest.raises(intake.IntakeFailure) as caught:
        intake.interpret('150 speed',provider=Provider())
    assert caught.value.reason=='INTAKE_BUSY'
    assert not caught.value.metadata['modelCalled']


def test_failed_initial_analysis_leaves_draft_unchanged(client,monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    monkeypatch.setattr(intake,'OllamaProvider',lambda url:Provider(error='INFERENCE_TIMEOUT'))
    m=client.post('/api/v1/matters',json={'originalText':'150 speed','language':'english'}).json()
    url='/api/v1/matters/'+m['id']
    response=client.post(url+'/analyze',json={'revision':m['revision']})
    assert response.status_code==503 and 'retry' in response.json()['detail']
    saved=client.get(url).json()
    assert saved['revision']==m['revision'] and saved['stage']=='DRAFT' and not saved['facts']
