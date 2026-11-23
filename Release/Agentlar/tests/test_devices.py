import unittest,tempfile
from pathlib import Path
from agentlar.devices import PCFiles
from agentlar.phone import PhoneBridge
class DeviceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.docs=self.root/'docs';self.docs.mkdir();self.p=self.docs/'a.txt';self.p.write_text('salom',encoding='utf8');self.pc=PCFiles({'hujjat':str(self.docs)},self.root/'state')
 def test_scope(self):
  self.assertEqual(self.pc.path('hujjat/a.txt'),self.p)
  for name in ['hujjat/../bad','hujjat/.env','x/a.txt','hujjat/C:/a']:
   with self.assertRaises(ValueError):self.pc.path(name)
 def test_edit_backup_stale(self):
  token=self.pc.propose('hujjat/a.txt','salom','yangi')['token'];self.pc.apply(token)
  self.assertEqual(self.p.read_text(),'yangi');self.assertEqual(next((self.root/'state'/'file_backups').glob('*')).read_text(),'salom')
  token=self.pc.propose('hujjat/a.txt','yangi','keyingi')['token'];self.p.write_text('boshqa')
  with self.assertRaises(ValueError):self.pc.apply(token)
 def test_symlink(self):
  (self.docs/'link').symlink_to(self.root,target_is_directory=True)
  with self.assertRaises(ValueError):self.pc.path('hujjat/link/other')
 def test_pair_queue_revoke(self):
  b=PhoneBridge(self.root,lambda x:None,lambda x:None);code=b.new_pair();token=b.pair(code)
  with self.assertRaises(ValueError):b.pair(code)
  task=b.enqueue('search',query='a');poll=b.poll(token,{'battery':50});self.assertEqual(poll['command']['id'],task)
  self.assertEqual(b.poll(token,{})['command']['id'],task)
  b.result(token,task,{'text':'found'});self.assertIsNone(b.poll(token,{})['command'])
  b.revoke()
  with self.assertRaises(ValueError):b.poll(token,{})
 def test_unsolicited_result(self):
  b=PhoneBridge(self.root,lambda x:None,lambda x:None);t=b.pair(b.new_pair())
  with self.assertRaises(ValueError):b.result(t,'unknown',{'text':'bad'})
 def test_http_pair_and_authorization(self):
  import json,urllib.request,urllib.error
  b=PhoneBridge(self.root,lambda x:None,lambda x:None);b.start(0);self.addCleanup(b.close)
  endpoint='http://127.0.0.1:'+str(b.server.server_port)
  def call(route,obj,token=''):
   req=urllib.request.Request(endpoint+route,data=json.dumps(obj).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
   with urllib.request.urlopen(req,timeout=3) as r:return json.load(r)
  with self.assertRaises(urllib.error.HTTPError):call('/poll',{})
  t=call('/pair',{'code':b.new_pair()})['token'];self.assertIsNone(call('/poll',{},t)['command'])
  b.revoke()
  with self.assertRaises(urllib.error.HTTPError):call('/poll',{},t)
 def test_expired_pair_and_queue(self):
  import time
  b=PhoneBridge(self.root,lambda x:None,lambda x:None);code=b.new_pair();b.code_until=time.time()-1
  with self.assertRaises(ValueError):b.pair(code)
  t=b.pair(b.new_pair());b.enqueue('search',query='q');b.queue[0]['expires']=time.time()-1
  self.assertIsNone(b.poll(t,{})['command'])
 def test_invalid_result_retains_queue(self):
  b=PhoneBridge(self.root,lambda x:None,lambda x:None);t=b.pair(b.new_pair());job=b.enqueue('search',query='q')
  with self.assertRaises(ValueError):b.result(t,job,{'data':'aGVsbG8='})
  self.assertEqual(b.poll(t,{})['command']['id'],job)
 def test_get_result_and_duplicate(self):
  import base64
  b=PhoneBridge(self.root,lambda x:None,lambda x:None);t=b.pair(b.new_pair());job=b.enqueue('get',file_id='abc')
  value={'name':'../a.txt','data':base64.b64encode(b'hello').decode()}
  b.result(t,job,value);b.result(t,job,value)
  files=list((self.root/'phone_received').iterdir());self.assertEqual(len(files),1);self.assertEqual(files[0].read_bytes(),b'hello')
 def test_unauthorized_bot_cannot_access_devices(self):
  from agentlar.bot import Bot
  class E:base=self.root
  class TG:
   def send(self,text):raise AssertionError('Unauthorized message sent')
  bot=Bot({'owner_id':42},E(),TG())
  bot.devices.handle=lambda text:(_ for _ in ()).throw(AssertionError('Unauthorized command'))
  bot.handle({'text':'/pcfind a','from':{'id':9},'chat':{'id':42,'type':'private'}})
 def test_edit_preview_must_not_hide_content(self):
  with self.assertRaises(ValueError):self.pc.propose('hujjat/a.txt','salom','x'*1001)
 def test_slow_connection_does_not_block_pair(self):
  import socket,json,urllib.request
  b=PhoneBridge(self.root,lambda x:None,lambda x:None);b.start(0)
  slow=socket.create_connection(('127.0.0.1',b.server.server_port));slow.sendall(b'POST /pair HTTP/1.1\r\n')
  try:
   req=urllib.request.Request('http://127.0.0.1:'+str(b.server.server_port)+'/pair',data=json.dumps({'code':b.new_pair()}).encode())
   with urllib.request.urlopen(req,timeout=2) as response:self.assertIn('token',json.load(response))
  finally:slow.close();b.close()
 def test_search_counts_directories(self):
  for i in range(10002):(self.docs/str(i)).mkdir()
  rows=self.pc.find('no-match');self.assertTrue(any('limit' in row.lower() for row in rows))
