import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

class SetupApiTests(unittest.TestCase):
    def test_config_rejects_bad_owner_and_external_job_root(self):
        self.assertIsNotNone(importlib.util.find_spec('agentlar.config'), 'config missing')
        from agentlar.config import validate_config
        with tempfile.TemporaryDirectory() as t:
            good={'telegram_token':'123:abc','gemini_api_key':'key','model':'model-x','owner_id':12,'sources':{},'max_steps':24,'allow_commands':False}
            self.assertEqual(validate_config(good,Path(t))['owner_id'],12)
            for bad in (0,'12',True,-1):
                with self.assertRaises(ValueError): validate_config({**good,'owner_id':bad},Path(t))
            with self.assertRaises(ValueError): validate_config({**good,'sources':{'all':str(Path(t).anchor)}},Path(t))

    def test_gemini_json_payload_and_incomplete_response(self):
        from agentlar.api import Gemini
        seen=[]
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,*args): return json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"plan":"test"}'}]}}]}).encode()
        def fake(req,timeout): seen.append(req); return Response()
        with patch('agentlar.api.urlopen',fake): self.assertEqual(Gemini('secret','model-x').ask('planner','hello'),{'plan':'test'})
        body=json.loads(seen[0].data)
        self.assertEqual(body['contents'][0]['parts'][0]['text'],'hello')
        self.assertEqual(body['generationConfig']['responseMimeType'],'application/json')
        self.assertNotIn('secret',seen[0].full_url)
        with patch('agentlar.api.request_json',return_value={'candidates':[{'finishReason':'MAX_TOKENS','content':{'parts':[{'text':'{}'}]}}]}):
            with self.assertRaises(RuntimeError): Gemini('secret','model-x').ask('planner','hello')

    def test_http_error_never_discloses_key(self):
        from agentlar.api import request_json
        from urllib.error import HTTPError
        with patch('agentlar.api.urlopen',side_effect=HTTPError('https://api.telegram.org/botSECRET/getMe',401,'bad',{},None)):
            with self.assertRaises(RuntimeError) as err: request_json('https://api.telegram.org/botSECRET/getMe')
        self.assertNotIn('SECRET',str(err.exception))

    def test_stop_revokes_pending_approval(self):
        from agentlar.engine import Engine
        with tempfile.TemporaryDirectory() as t:
            e=Engine(Path(t),{'allow_commands':True},None,lambda x:None)
            j=e.create('test'); j['status']='awaiting_approval'; j['pending']={'argv':['python','-V'],'token':'old'}; e.store.save(j['id'],j)
            e.stop()
            self.assertEqual(e.store.load(j['id'])['status'],'stopped')
            with self.assertRaises(ValueError): e.approve(j['id'],'old')

if __name__=='__main__': unittest.main()
