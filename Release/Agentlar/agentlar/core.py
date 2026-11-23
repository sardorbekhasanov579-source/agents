import ast
import json
import os
import re
import threading
import uuid
import zipfile
from pathlib import Path

MAX_FILE = 256 * 1024
MAX_TOTAL = 5 * 1024 * 1024
SECRET = {'config.json', 'credentials.json', 'token.json', 'secrets.json', 'id_rsa', 'id_ed25519'}
RESERVED = {'con', 'prn', 'aux', 'nul', *('com' + str(i) for i in range(1, 10)), *('lpt' + str(i) for i in range(1, 10))}
GENERATED = {'node_modules', '__pycache__', 'dist', 'build', 'venv'}
BINARY_EXTENSIONS = {'.db','.sqlite','.sqlite3','.db-wal','.db-shm','.png','.jpg','.jpeg','.gif','.webp','.ico','.pdf','.zip','.docx','.xlsx','.pptx','.exe','.dll','.so','.woff','.woff2','.ttf','.mp3','.mp4','.bin'}
TEXT_EXTENSIONS = {'.py','.js','.ts','.tsx','.jsx','.json','.html','.css','.md','.txt','.csv','.yml','.yaml','.toml','.ini','.xml','.sql','.bat','.cmd','.ps1','.sh','.c','.cpp','.h','.java','.kt','.gradle'}

def is_binary(path,data=b''):
    return Path(path).suffix.lower() in BINARY_EXTENSIONS or b'\x00' in data or data.startswith((b'SQLite format 3',b'\x89PNG',b'PK\x03\x04',b'%PDF-'))

def authorized(message, owner):
    return (isinstance(owner, int) and owner > 0 and
            message.get('from', {}).get('id') == owner and
            message.get('chat', {}).get('id') == owner and
            message.get('chat', {}).get('type') == 'private')

def safe_path(root, name):
    if not isinstance(name, str) or not name or len(name) > 220:
        raise ValueError('Fayl yo‘li yaroqsiz')
    name = name.replace('\\', '/')
    parts = name.split('/')
    for part in parts:
        if (not part or part in ('.', '..') or part.startswith('.') or
                part.rstrip(' .') != part or any(c in part for c in ':<>"|?*') or
                any(ord(c) < 32 for c in part) or part.lower() in SECRET or
                part.lower().endswith(('.pem', '.key', '.p12')) or
                part.split('.')[0].lower() in RESERVED):
            raise ValueError('Bu fayl yo‘liga ruxsat yo‘q')
    root = Path(root).resolve()
    candidate = root.joinpath(*parts)
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink(): raise ValueError('Symlink ruxsat etilmagan')
    if not candidate.resolve().is_relative_to(root): raise ValueError('Papka tashqarisiga chiqish taqiqlangan')
    return candidate

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)

class Store:
    def __init__(self, root):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def path(self, ident):
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', ident): raise ValueError('ID yaroqsiz')
        return self.root / (ident + '.json')

    def save(self, ident, value):
        with self.lock: atomic_json(self.path(ident), value)

    def load(self, ident):
        with self.lock: return json.loads(self.path(ident).read_text(encoding='utf-8'))

    def jobs(self):
        rows = []
        for p in self.root.glob('*.json'):
            if p.stem.startswith('job_'):
                try: rows.append(self.load(p.stem))
                except (ValueError, OSError): pass
        return sorted(rows, key=lambda j: j['id'], reverse=True)

class Workspace:
    def __init__(self, root, sources):
        self.root = Path(root).resolve(); self.root.mkdir(parents=True, exist_ok=True)
        self.sources = sources

    def list_files(self):
        rows = []
        for base, dirs, files in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d not in GENERATED and not (Path(base) / d).is_symlink())
            for f in sorted(files):
                if f in ('package-lock.json','npm-shrinkwrap.json') or f.endswith('.pyc'): continue
                rel = (Path(base) / f).relative_to(self.root).as_posix()
                try:
                    p = safe_path(self.root, rel)
                    if p.is_file(): rows.append({'path': rel, 'bytes': p.stat().st_size})
                except ValueError: pass
                if len(rows) >= 200: return rows
        return rows

    def read(self, path):
        return self._read(safe_path(self.root, path))

    @staticmethod
    def _read(p):
        if not p.is_file() or p.stat().st_size > MAX_FILE: raise ValueError('Fayl yo‘q yoki 256 KiB dan katta')
        data=p.read_bytes()
        if is_binary(p,data): raise ValueError(p.name+': ikkilik fayl; matn sifatida o‘qilmaydi')
        try: return data.decode('utf-8-sig')
        except UnicodeDecodeError:
            raise ValueError(p.name+': UTF-8 matn emas; kodlashni tekshiring, fayl o‘zgartirilmadi') from None

    def review_bundle(self):
        result={'files':{},'unreviewed_files':[],'unreadable_text':[],'truncated':False}
        count=0
        for item in self.list_files():
            name=item['path']; p=safe_path(self.root,name)
            if p.suffix.lower() in BINARY_EXTENSIONS:
                result['unreviewed_files'].append({**item,'reason':'binary_format_not_inspected'})
                continue
            if item['bytes']>MAX_FILE:
                result['unreadable_text'].append({**item,'reason':'text_read_size_limit'})
                continue
            data=p.read_bytes()
            if is_binary(p,data) and p.suffix.lower() not in TEXT_EXTENSIONS:
                result['unreviewed_files'].append({**item,'reason':'binary_content_not_inspected'})
                continue
            try:
                text=self._read(p)
            except ValueError as exc:
                result['unreadable_text'].append({**item,'reason':str(exc)})
                continue
            count+=len(text)
            if count>100000:
                result['truncated']=True; break
            result['files'][name]=text
        return result

    def write(self, path, text):
        p = safe_path(self.root, path)
        if not isinstance(text, str): raise ValueError('Matn kerak')
        data = text.encode('utf-8')
        if len(data) > MAX_FILE: raise ValueError('Fayl 256 KiB dan katta')
        files = self.list_files()
        if not p.exists() and len(files) >= 200: raise ValueError('200 fayl limiti')
        total = sum(x['bytes'] for x in files) - (p.stat().st_size if p.is_file() else 0) + len(data)
        if total > MAX_TOTAL: raise ValueError('5 MiB loyiha limiti')
        if p.is_file():
            backup = self.root / '.backups'; backup.mkdir(exist_ok=True)
            if backup.is_symlink(): raise ValueError('Backup symlink')
            (backup / (uuid.uuid4().hex + '.bak')).write_bytes(p.read_bytes())
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return {'written': path, 'bytes': len(data)}

    def read_source(self, alias, path):
        if alias not in self.sources: raise ValueError('Manba ruxsat etilmagan')
        return self._read(safe_path(self.sources[alias], path))

    def list_source(self, alias):
        if alias not in self.sources: raise ValueError('Manba ruxsat etilmagan')
        root = Path(self.sources[alias]).resolve()
        if not root.is_dir(): raise ValueError('Manba papkasi topilmadi')
        rows = []
        for base, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'venv', '__pycache__') and not (Path(base)/d).is_symlink())
            for f in files:
                rel = (Path(base)/f).relative_to(root).as_posix()
                try:
                    p = safe_path(root, rel)
                    if p.is_file(): rows.append(rel)
                except ValueError: pass
                if len(rows) >= 200: return rows
        return rows

    def check(self):
        errors = []; checked = 0
        for item in self.list_files():
            p = item['path']
            if Path(p).suffix not in ('.py', '.json'): continue
            checked += 1
            try:
                text = self.read(p)
                if p.endswith('.py'): ast.parse(text, filename=p)
                else: json.loads(text)
            except (ValueError, SyntaxError, UnicodeError) as e: errors.append({'path': p, 'error': str(e)[:300]})
        return {'kind': 'syntax_only_not_runtime_tests', 'checked': checked, 'errors': errors}

    def archive(self, target):
        target = Path(target); target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
            for item in self.list_files(): z.write(safe_path(self.root, item['path']), item['path'])
        return target
