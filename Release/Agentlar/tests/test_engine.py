import importlib.util
import tempfile
import unittest
from pathlib import Path

class ScriptedAI:
    def __init__(self, actions): self.actions = iter(actions)
    def ask(self, role, prompt, json_mode=True): return next(self.actions)

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('agentlar.engine'), 'engine missing')
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.events = []

    def engine(self, actions, **extra):
        from agentlar.engine import Engine
        cfg = {'owner_id': 12, 'sources': {}, 'max_steps': 8, 'allow_commands': False, 'allow_local_build':True, **extra}
        return Engine(self.base, cfg, ScriptedAI(actions), self.events.append)

    def test_real_file_generation_and_review(self):
        e = self.engine([{'plan': 'HTML yaratamiz'}, {'action': 'write', 'path': 'index.html', 'text': '<h1>Salom</h1>'}, {'action': 'finish', 'summary': 'Tayyor'}, {'ok': True, 'issues': [], 'summary': 'HTML tekshirildi'}])
        job = e.create('Salom sayti')
        e.run(job['id'])
        state = e.store.load(job['id'])
        self.assertEqual(state['status'], 'done')
        self.assertEqual((self.base/'projects'/job['id']/'index.html').read_text(), '<h1>Salom</h1>')
        self.assertTrue(Path(state['archive']).is_file())
        self.assertEqual(state['review']['ok'], True)

    def test_cancel_after_ai_before_write(self):
        e = self.engine([])
        job = e.create('cancel test')
        class CancellingAI:
            def ask(inner, role, prompt, json_mode=True):
                if 'planner' in role: return {'plan': 'plan'}
                e.stop()
                return {'action':'write', 'path':'oops.txt', 'text':'bad'}
        e.ai = CancellingAI()
        e.run(job['id'])
        self.assertEqual(e.store.load(job['id'])['status'], 'stopped')
        self.assertFalse((self.base/'projects'/job['id']/'oops.txt').exists())

    def test_budget_bounds_unfinished_job(self):
        e = self.engine([{'plan': 'plan'}, {'action':'list'}, {'action':'list'}], max_steps=2)
        job = e.create('loop'); e.run(job['id'])
        self.assertEqual(e.store.load(job['id'])['status'], 'paused')

    def test_command_needs_explicit_approval(self):
        e = self.engine([{'plan':'plan'}, {'action':'command', 'argv':['python', '-V']}], allow_commands=True)
        job=e.create('command'); e.run(job['id'])
        saved=e.store.load(job['id'])
        self.assertEqual(saved['status'], 'awaiting_approval')
        self.assertEqual(saved['pending']['argv'], ['python','-V'])
        with self.assertRaises(ValueError): e.approve(job['id'], 'wrong')
        self.assertEqual(e.store.load(job['id'])['status'], 'awaiting_approval')

    def test_approved_command_produces_real_file_once(self):
        import sys
        e=self.engine([{'action':'finish','summary':'done'}, {'ok':True,'issues':[],'summary':'checked'}],allow_commands=True)
        j=e.create('write marker'); j['plan']='Write marker'
        j['status']='awaiting_approval'
        j['pending']={'argv':[sys.executable,'-c','from pathlib import Path; Path("marker.txt").write_text("executed")'],'token':'one-use'}
        e.store.save(j['id'],j)
        e.approve(j['id'],'one-use'); e.thread.join(10)
        self.assertFalse(e.thread.is_alive())
        self.assertEqual((self.base/'projects'/j['id']/'marker.txt').read_text(),'executed')
        self.assertEqual(e.store.load(j['id'])['status'],'done')
        with self.assertRaises(ValueError): e.approve(j['id'],'one-use')

    def test_bad_model_output_is_persisted_as_error(self):
        e=self.engine([{'plan':'plan'}, ['not an action']])
        job=e.create('bad'); e.run(job['id'])
        self.assertEqual(e.store.load(job['id'])['status'], 'error')

    def test_stop_during_approval_notification_cannot_restore_token(self):
        e=self.engine([{'plan':'plan'}, {'action':'command','argv':['python','-V']}],allow_commands=True)
        def notify(text):
            if 'BUYRUQ UCHUN' in text: e.stop()
        e.notify=notify
        j=e.create('race'); e.run(j['id'])
        saved=e.store.load(j['id'])
        self.assertEqual(saved['status'],'stopped')
        self.assertIsNone(saved['pending'])

    def test_shutdown_waits_for_command_worker(self):
        import threading, time
        e=self.engine([])
        ended=threading.Event()
        def worker():
            e.cancel.wait(2); time.sleep(.05); ended.set()
        e.thread=threading.Thread(target=worker); e.thread.start()
        self.assertTrue(hasattr(e,'shutdown'),'shutdown lifecycle missing')
        e.shutdown()
        self.assertTrue(ended.is_set())
        self.assertFalse(e.thread.is_alive())

    def test_restart_marks_running_interrupted(self):
        e=self.engine([]); j=e.create('restart'); j['status']='running'; e.store.save(j['id'],j)
        e2=self.engine([])
        self.assertEqual(e2.store.load(j['id'])['status'], 'interrupted')

    def test_untrusted_bot_messages_create_no_jobs(self):
        from agentlar.bot import Bot
        e=self.engine([])
        class TG:
            def send(inner, text): self.events.append(text)
        bot=Bot({'owner_id':12}, e, TG())
        bot.handle({'from':{'id':99},'chat':{'id':99,'type':'private'},'text':'make app'})
        bot.handle({'from':{'id':12},'chat':{'id':12,'type':'group'},'text':'make app'})
        self.assertEqual(e.store.jobs(), [])
        self.assertEqual(self.events, [])

if __name__=='__main__': unittest.main()
