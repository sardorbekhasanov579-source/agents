import importlib.util
import tempfile
import threading
import unittest
from pathlib import Path
from agentlar.core import Workspace

class BuildTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('agentlar.build'),'build runner missing')
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name); self.w=Workspace(self.base/'project',{})

    def runner(self):
        from agentlar.build import LocalBuilder
        return LocalBuilder(self.w,self.base/'exports',threading.Event(),lambda s:None)

    def test_generated_dependencies_not_in_model_source_view(self):
        self.w.write('main.py','print(1)')
        (self.w.root/'node_modules').mkdir(); (self.w.root/'node_modules'/'huge.py').write_text('bad syntax!')
        self.assertEqual([x['path'] for x in self.w.list_files()],['main.py'])
        self.assertEqual(self.w.check()['errors'],[])

    def test_static_requires_index_and_archives_real_output(self):
        import zipfile
        b=self.runner()
        self.assertFalse(b.build('static')['ok'])
        self.w.write('index.html','<!doctype html><html><h1>Hello</h1></html>')
        result=b.build('static')
        self.assertTrue(result['ok'])
        self.assertEqual(result['tests'],'not_run_browser')
        with zipfile.ZipFile(result['archive']) as z:
            self.assertIn('source/index.html',z.namelist())

    def test_source_change_invalidates_build_digest(self):
        from agentlar.build import source_digest
        self.w.write('index.html','hello')
        first=source_digest(self.w)
        self.w.write('index.html','changed')
        self.assertNotEqual(source_digest(self.w),first)

    def test_lockfile_in_digest_and_archive(self):
        import zipfile
        from agentlar.build import source_digest
        self.w.write('index.html','hello')
        first=source_digest(self.w)
        (self.w.root/'package-lock.json').write_text('{"lockfileVersion":3}')
        self.assertNotEqual(source_digest(self.w),first)
        archive=self.runner().archive('static')
        with zipfile.ZipFile(archive) as z: self.assertIn('source/package-lock.json',z.namelist())

    def test_real_web_build_cannot_reuse_old_dist(self):
        import shutil
        if not shutil.which('node') or not shutil.which('npm'): self.skipTest('Node missing')
        self.w.write('package.json','{"name":"local-build-test","version":"1.0.0","scripts":{"test":"node --test tests/basic.test.js","build":"node build.js"}}')
        self.w.write('tests/basic.test.js','const test=require("node:test");const assert=require("node:assert");test("sum",()=>assert.equal(2+3,5));')
        self.w.write('build.js','const fs=require("node:fs");fs.mkdirSync("dist",{recursive:true});fs.writeFileSync("dist/index.html","hello");')
        result=self.runner().build('web'); self.assertTrue(result['ok'],result)
        self.w.write('build.js','console.log("no artifact")')
        result=self.runner().build('web'); self.assertFalse(result['ok'],result)

    def test_python_environment_is_clean_on_rebuild(self):
        self.w.write('app.py','x=1')
        self.w.write('tests/test_app.py','import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
        self.assertTrue(self.runner().build('python')['ok'])
        marker=self.w.root/'.venv'/'old-dependency-marker'; marker.write_text('stale')
        self.assertTrue(self.runner().build('python')['ok'])
        self.assertFalse(marker.exists())

    def test_artifact_tampering_invalidates_evidence(self):
        import agentlar.build as build
        self.assertTrue(hasattr(build,'valid_evidence'),'artifact verifier missing')
        self.w.write('index.html','hello'); result=self.runner().build('static')
        self.assertTrue(build.valid_evidence(self.w,result))
        Path(result['archive']).write_bytes(b'not the tested artifact')
        self.assertFalse(build.valid_evidence(self.w,result))

    def test_review_time_source_change_cannot_finish(self):
        from agentlar.engine import Engine
        class AI:
            def __init__(inner): inner.count=0
            def ask(inner,role,prompt):
                inner.count+=1
                if inner.count==1: return {'plan':'site'}
                if inner.count==2: return {'action':'write','path':'index.html','text':'hello'}
                if inner.count==3: return {'action':'finish','summary':'done'}
                e.workspace(j['id']).write('index.html','changed during review')
                return {'ok':True,'summary':'fine','issues':[]}
        e=Engine(self.base/'app',{'max_steps':2,'sources':{},'allow_local_build':True},AI(),lambda s:None)
        j=e.create('site'); e.run(j['id'])
        self.assertNotEqual(e.store.load(j['id'])['status'],'done')

    def test_python_runs_actual_tests_and_rejects_failure(self):
        self.w.write('app.py','def add(a,b): return a+b\n')
        self.w.write('tests/test_app.py','import unittest\nfrom app import add\nclass TestApp(unittest.TestCase):\n def test_add(self): self.assertEqual(add(2,3),5)\n')
        result=self.runner().build('python')
        self.assertTrue(result['ok'],result)
        self.assertEqual(result['tests'],'passed')
        self.w.write('app.py','def add(a,b): return 0\n')
        result=self.runner().build('python')
        self.assertFalse(result['ok'],result)

    def test_empty_test_suite_is_not_a_pass(self):
        self.w.write('main.py','print(1)')
        result=self.runner().build('python')
        self.assertFalse(result['ok'])
        self.assertIn('test',str(result).lower())

    def test_cancelled_runner_never_launches(self):
        b=self.runner(); b.cancel.set()
        with self.assertRaises(InterruptedError): b.build('static')

    def test_web_requires_build_and_test_scripts(self):
        self.w.write('package.json','{"scripts":{}}')
        result=self.runner().build('web')
        self.assertFalse(result['ok'])

    def test_engine_does_not_finish_unbuilt_software(self):
        from agentlar.engine import Engine
        class AI:
            def __init__(self): self.steps=iter([{'plan':'site'},{'action':'write','path':'index.html','text':'<h1>x</h1>'},{'action':'finish','summary':'done'},{'ok':True,'summary':'fine','issues':[]}])
            def ask(self,*args): return next(self.steps)
        e=Engine(self.base/'app',{'sources':{},'max_steps':5},AI(),lambda s:None)
        j=e.create('website'); e.run(j['id'])
        self.assertEqual(e.store.load(j['id'])['status'],'needs_setup')

    def test_engine_builds_before_done_and_delivers_artifact(self):
        from agentlar.engine import Engine
        import inspect
        self.assertIn('deliver',inspect.signature(Engine).parameters)
        sent=[]
        class AI:
            def __init__(self): self.steps=iter([{'plan':'site'},{'action':'write','path':'index.html','text':'<h1>x</h1>'},{'action':'finish','summary':'done'},{'ok':True,'summary':'fine','issues':[]}])
            def ask(self,*args): return next(self.steps)
        e=Engine(self.base/'app',{'sources':{},'max_steps':5,'allow_local_build':True},AI(),lambda s:None,deliver=lambda p:sent.append(Path(p)))
        j=e.create('website'); e.run(j['id']); saved=e.store.load(j['id'])
        self.assertEqual(saved['status'],'done')
        self.assertTrue(saved['build']['ok'])
        self.assertTrue(sent[0].is_file())

if __name__=='__main__': unittest.main()
