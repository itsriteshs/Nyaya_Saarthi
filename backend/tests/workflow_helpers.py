"""Explicit user setup for tests focused on downstream slot/legal behavior."""
from uuid import uuid4

def establish_issue(client,url,matter,issue_id=None):
    question=matter.get('currentQuestion')
    if question and question['slot']=='INTENT':
        response=client.post(url+'/answers',json={'revision':matter['revision'],'questionId':question['id'],
            'messageId':str(uuid4()),'answer':issue_id or matter['nlpAnalysis']['intent']['id']})
        assert response.status_code==200,response.text
        return response.json()
    return matter
