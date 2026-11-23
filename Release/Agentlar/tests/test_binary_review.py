import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from agentlar.core import Workspace
from agentlar.engine import Engine

class BinaryReviewTests(unittest.TestCase):
    def test_real_sqlite_does_not_crash_finish_or_change_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            payloads=[]
            class AI:
                def __init__(self): self.items=iter([{'plan':'document'},{'action':'finish','summary':'done'},{'ok':True,'issues':[],'summary':'text reviewed; database not inspected'}])
                def ask(self,role,prompt):
                    if 'independent reviewer' in role: payloads.append(json.loads(prompt))
                    return next(self.items)
            e=Engine(Path(d),{'sources':{},'max_steps':2},AI(),lambda s:None)
            j=e.create('Review project'); w=e.workspace(j['id']); w.write('README.md','Database example')
            db=w.root/'expenses.db'
            with sqlite3.connect(db) as con:
                con.execute('create table expenses (name text, amount real)')
                con.execute('insert into expenses values (?,?)',('test',150.5))
            before=db.read_bytes(); e.run(j['id']); state=e.store.load(j['id'])
            self.assertEqual(state['status'],'done',state.get('error'))
            self.assertIn('expenses.db',[x['path'] for x in payloads[0]['unreviewed_files']])
            self.assertNotIn('expenses.db',payloads[0]['files'])
            with zipfile.ZipFile(state['archive']) as archive: self.assertEqual(archive.read('expenses.db'),before)
            self.assertEqual(db.read_bytes(),before)

    def test_binary_read_error_is_clear_not_decode_exception(self):
        with tempfile.TemporaryDirectory() as d:
            w=Workspace(Path(d),{}); (w.root/'image.png').write_bytes(b'\x89PNG\x00\x96')
            with self.assertRaises(ValueError) as err: w.read('image.png')
            self.assertNotIsInstance(err.exception,UnicodeDecodeError)
            self.assertIn('image.png',str(err.exception))

    def test_non_utf8_source_cannot_be_silently_approved(self):
        with tempfile.TemporaryDirectory() as d:
            w=Workspace(Path(d),{})
            (w.root/'main.js').write_bytes(b'const x="\x96";')
            self.assertTrue(hasattr(w,'review_bundle'),'review classifier missing')
            result=w.review_bundle()
            self.assertEqual(result['unreadable_text'][0]['path'],'main.js')
            self.assertNotIn('main.js',result['files'])

    def test_utf8_bom_and_uzbek_remain_readable(self):
        with tempfile.TemporaryDirectory() as d:
            w=Workspace(Path(d),{})
            (w.root/'notes.txt').write_bytes(b'\xef\xbb\xbf'+ 'O‘zbekcha matn'.encode())
            self.assertEqual(w.read('notes.txt'),'O‘zbekcha matn')

if __name__=='__main__': unittest.main()
