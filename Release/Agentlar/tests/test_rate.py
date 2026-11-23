import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from agentlar.api import Gemini, request_json

class RateTests(unittest.TestCase):
    def test_retry_after_is_respected_for_429(self):
        sleeps=[]
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,*args): return b'{"ok":true}'
        failure=HTTPError('https://example.org',429,'limit',{'Retry-After':'42'},io.BytesIO(b'{}'))
        with patch('agentlar.api.urlopen',side_effect=[failure,Response()]), patch('agentlar.api.time.sleep',sleeps.append):
            request_json('https://example.org',gemini_retry=True)
        self.assertGreaterEqual(sleeps[0],42)

    def test_daily_quota_does_not_retry(self):
        body={'error':{'details':[{'violations':[{'quotaId':'GenerateRequestsPerDayPerProjectPerModel-FreeTier'}]}]}}
        failure=HTTPError('https://example.org',429,'limit',{},io.BytesIO(json.dumps(body).encode()))
        with patch('agentlar.api.urlopen',side_effect=failure) as req, patch('agentlar.api.time.sleep'):
            with self.assertRaises(RuntimeError) as err: request_json('https://example.org',gemini_retry=True)
        self.assertEqual(req.call_count,1)
        self.assertIn('kunlik',str(err.exception).lower())

    def test_pacing_between_transport_attempts(self):
        self.assertTrue(hasattr(Gemini,'pace'),'rate pacing missing')
        g=Gemini('key','model'); g.min_interval=15
        with patch('agentlar.api.time.monotonic',side_effect=[100,102,115]), patch.object(g,'pause') as pause:
            g.pace(); g.pace()
        pause.assert_called_once_with(13)

    def test_telegram_retry_uses_telegram_retry_after(self):
        failure=HTTPError('https://example.org',429,'limit',{},io.BytesIO(b'{"parameters":{"retry_after":7}}'))
        sleeps=[]
        with patch('agentlar.api.urlopen',side_effect=failure), patch('agentlar.api.time.sleep',sleeps.append):
            with self.assertRaises(RuntimeError): request_json('https://example.org')
        self.assertEqual(sleeps[0],7)

if __name__=='__main__': unittest.main()
