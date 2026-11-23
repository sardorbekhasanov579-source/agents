import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from agentlar.api import Gemini
from agentlar.engine import Engine, BUILDER

def response(text, reason='STOP', **extra):
    return {'candidates':[{'finishReason':reason,'content':{'parts':[{'text':text}]},**extra}]}

class UpgradeTests(unittest.TestCase):
    def test_malformed_call_retry_is_bounded_and_json_only(self):
        bodies=[]
        def api(url,data,**kw):
            bodies.append(data)
            return response('', 'MALFORMED_FUNCTION_CALL') if len(bodies)==1 else response('{"action":"list"}')
        with patch('agentlar.api.request_json',api):
            self.assertEqual(Gemini('key','model').ask(BUILDER,'task'),{'action':'list'})
        self.assertEqual(len(bodies),2)
        self.assertEqual(bodies[0]['toolConfig']['functionCallingConfig']['mode'],'NONE')
        self.assertEqual(bodies[0]['generationConfig']['responseSchema']['required'],['action'])
        with patch('agentlar.api.request_json',return_value=response('','MALFORMED_FUNCTION_CALL')) as call:
            with self.assertRaises(RuntimeError): Gemini('key','model').ask(BUILDER,'task')
            self.assertEqual(call.call_count,2)

    def test_search_returns_provider_citations_not_invented_links(self):
        self.assertTrue(hasattr(Gemini,'search'),'search capability missing')
        body=response('Answer',groundingMetadata={'groundingChunks':[{'web':{'uri':'https://example.org/source','title':'Source'}}],'webSearchQueries':['question']})
        with patch('agentlar.api.request_json',return_value=body) as call:
            result=Gemini('key','model').search('question')
        self.assertTrue(result['grounded'])
        self.assertEqual(result['sources'][0]['url'],'https://example.org/source')
        self.assertEqual(call.call_args.args[1]['tools'],[{'google_search':{}}])
        self.assertNotIn('responseMimeType',call.call_args.args[1]['generationConfig'])

    def test_search_without_metadata_is_not_verified(self):
        self.assertTrue(hasattr(Gemini,'search'),'search capability missing')
        with patch('agentlar.api.request_json',return_value=response('unverified memory')):
            result=Gemini('key','model').search('question')
        self.assertFalse(result['grounded'])
        self.assertEqual(result['sources'],[])

    def test_progress_visible_before_model_returns(self):
        with tempfile.TemporaryDirectory() as d:
            events=[]
            e=Engine(Path(d),{'sources':{},'max_steps':1},None,events.append)
            j=e.create('progress')
            class AI:
                def ask(self,role,prompt):
                    saved=e.store.load(j['id'])
                    assert saved.get('phase')=='Reja tuzilmoqda', saved
                    assert any('Reja tuzilmoqda' in x for x in events)
                    return {'plan':'plan'}
            e.ai=AI()
            from agentlar.engine import PLANNER
            self.assertEqual(e.ask(j,PLANNER,'task'),{'plan':'plan'})

    def test_engine_search_is_saved_and_reported(self):
        with tempfile.TemporaryDirectory() as d:
            events=[]
            class AI:
                def __init__(self): self.actions=iter([{'plan':'search'},{'action':'search','query':'news'}])
                def ask(self,*args): return next(self.actions)
                def search(self,q): return {'text':'news','grounded':True,'sources':[{'url':'https://example.org/a','title':'A'}]}
            e=Engine(Path(d),{'sources':{},'max_steps':1},AI(),events.append)
            j=e.create('internet'); e.run(j['id'])
            saved=e.store.load(j['id'])
            self.assertTrue(saved['history'][-1]['result'].get('grounded'))
            self.assertTrue(any('https://example.org/a' in t for t in events))

if __name__=='__main__': unittest.main()
