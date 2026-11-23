import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('agentlar.core'), 'core implementation missing')
        from agentlar.core import Workspace
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.w = Workspace(self.base / 'job', {})

    def test_write_read_and_archive(self):
        import zipfile
        self.w.write('src/main.py', 'print(42)')
        self.assertEqual(self.w.read('src/main.py'), 'print(42)')
        with zipfile.ZipFile(self.w.archive(self.base / 'out.zip')) as z:
            self.assertEqual(z.read('src/main.py'), b'print(42)')

    def test_escape_and_secret_paths(self):
        for p in ('../escape', '/tmp/escape', 'C:/escape', r'..\escape', 'foo:bar', '.env', 'a/.git/config', 'config.json', 'CON.txt'):
            with self.subTest(p=p), self.assertRaises(ValueError): self.w.write(p, 'secret')

    def test_symlink_escape(self):
        outside = self.base / 'outside'; outside.mkdir()
        (self.w.root / 'link').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError): self.w.write('link/x.txt', 'bad')
        self.assertFalse((outside / 'x.txt').exists())

    def test_limit_and_backup(self):
        self.w.write('a.txt', 'old')
        self.w.write('a.txt', 'new')
        self.assertEqual(self.w.read('a.txt'), 'new')
        self.assertTrue(any(p.read_text() == 'old' for p in (self.w.root / '.backups').rglob('*.bak')))
        with self.assertRaises(ValueError): self.w.write('big.txt', 'a' * 262145)

    def test_source_read_only_and_secret_block(self):
        from agentlar.core import Workspace
        source = self.base / 'source'; source.mkdir()
        (source / 'notes.txt').write_text('hello')
        (source / '.env').write_text('key')
        w = Workspace(self.w.root, {'notes': str(source)})
        self.assertEqual(w.read_source('notes', 'notes.txt'), 'hello')
        with self.assertRaises(ValueError): w.read_source('notes', '.env')
        with self.assertRaises(ValueError): w.read_source('notes', '../job/a.txt')

    def test_checks_are_syntax_only(self):
        self.w.write('bad.py', 'if')
        self.w.write('good.py', 'raise RuntimeError("must not execute")')
        self.w.write('bad.json', '{')
        result = self.w.check()
        self.assertEqual(len(result['errors']), 2)
        self.assertEqual(result['checked'], 3)

    def test_owner_private_chat(self):
        from agentlar.core import authorized
        msg = {'from': {'id': 12}, 'chat': {'id': 12, 'type': 'private'}}
        self.assertTrue(authorized(msg, 12))
        self.assertFalse(authorized(msg, 13))
        msg['chat']['type'] = 'group'
        self.assertFalse(authorized(msg, 12))

    def test_store_durable(self):
        from agentlar.core import Store
        s = Store(self.base / 'state')
        s.save('task1', {'status': 'running', 'text': 'o‘zbek'})
        self.assertEqual(Store(self.base / 'state').load('task1')['text'], 'o‘zbek')
        with self.assertRaises(ValueError): s.load('../secrets')

if __name__ == '__main__': unittest.main()
