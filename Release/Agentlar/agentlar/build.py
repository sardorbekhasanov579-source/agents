"""Explicitly enabled HOST builds. Project isolation is organizational, not a sandbox."""
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from .core import safe_path

def source_entries(workspace):
    entries=[(safe_path(workspace.root,f['path']),f['path']) for f in workspace.list_files()]
    for name in ('package-lock.json','npm-shrinkwrap.json'):
        p=safe_path(workspace.root,name)
        if p.is_file():
            if p.stat().st_size>10*1024*1024: raise ValueError('Lockfile 10 MiB dan katta')
            entries.append((p,name))
    return sorted(entries,key=lambda x:x[1])

def source_digest(workspace):
    digest=hashlib.sha256()
    for p,name in source_entries(workspace):
        digest.update(name.encode()); digest.update(b'\0')
        digest.update(p.read_bytes()); digest.update(b'\0')
    return digest.hexdigest()

def valid_evidence(workspace,evidence):
    try:
        archive=Path(evidence['archive'])
        return bool(evidence.get('ok') and evidence.get('source_digest')==source_digest(workspace)
                    and archive.is_file() and not archive.is_symlink() and archive.stat().st_size<=15*1024*1024
                    and hashlib.sha256(archive.read_bytes()).hexdigest()==evidence.get('archive_digest'))
    except (KeyError,ValueError,OSError): return False

class LocalBuilder:
    def __init__(self,workspace,exports,cancel,notify):
        self.w=workspace; self.exports=Path(exports); self.cancel=cancel; self.notify=notify
        self.logs=[]; self.started=time.monotonic()

    def command(self,argv,label,timeout=300):
        if self.cancel.is_set(): raise InterruptedError()
        remaining=1200-(time.monotonic()-self.started)
        if remaining<=0: raise RuntimeError('Umumiy build vaqti 20 daqiqadan oshdi')
        timeout=min(timeout,remaining)
        self.notify('🔧 '+label)
        env={k:v for k,v in os.environ.items() if k.upper() in (
            'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','COMSPEC','PATHEXT','LANG','JAVA_HOME','ANDROID_HOME','ANDROID_SDK_ROOT','HOME','USERPROFILE','APPDATA','LOCALAPPDATA')}
        env.update({'CI':'true','PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1',
                    'PIP_DISABLE_PIP_VERSION_CHECK':'1','npm_config_audit':'false','npm_config_fund':'false'})
        launch=[sys.executable,str(Path(__file__).with_name('process_runner.py')),json.dumps(argv)] if os.name=='nt' else argv
        kw={'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
        process=None; reason=None; last=time.monotonic()
        with tempfile.TemporaryFile() as out:
            try:
                process=subprocess.Popen(launch,cwd=self.w.root,env=env,stdin=subprocess.DEVNULL,
                    stdout=out,stderr=subprocess.STDOUT,shell=False,**kw)
                deadline=time.monotonic()+timeout
                while process.poll() is None:
                    if self.cancel.is_set(): reason='cancelled'; break
                    if time.monotonic()>deadline: reason='timeout'; break
                    if os.fstat(out.fileno()).st_size>8*1024*1024: reason='output_limit'; break
                    if time.monotonic()-last>=30:
                        self.notify('⏳ '+label+' davom etmoqda...'); last=time.monotonic()
                    time.sleep(.1)
            finally:
                if process:
                    if os.name=='nt':
                        if process.poll() is None: process.kill()
                    else:
                        try: os.killpg(process.pid,signal.SIGKILL)
                        except ProcessLookupError: pass
                    process.wait()
            size=os.fstat(out.fileno()).st_size
            out.seek(max(0,size-20000)); output=out.read().decode('utf-8',errors='replace')
        item={'step':label,'argv':argv,'returncode':process.returncode,'output':output,'limit':reason}
        self.logs.append(item)
        if self.cancel.is_set(): raise InterruptedError()
        if process.returncode!=0 or reason:
            raise RuntimeError(label+' muvaffaqiyatsiz: '+str(reason or process.returncode)+'\n'+output[-8000:])
        self.notify('✅ '+label)
        return output

    def build(self,profile):
        if self.cancel.is_set(): raise InterruptedError()
        try:
            if profile not in ('static','python','web','android'): raise ValueError('Profil: static, python, web yoki android')
            if profile=='static':
                path=safe_path(self.w.root,'index.html')
                if not path.is_file() or not path.read_text(encoding='utf-8').strip(): raise ValueError('index.html kerak')
                if (self.w.root/'package.json').exists() or any(f['path'].endswith('.py') for f in self.w.list_files()):
                    raise ValueError('Static profil Python yoki package.json loyihasini tekshirmaydi; mos build profilini tanlang')
                tests='not_run_browser'
            elif profile=='python':
                checks=self.w.check()
                if checks['errors']: raise ValueError('Sintaksis xatolari: '+json.dumps(checks['errors']))
                if not list((self.w.root/'tests').glob('test*.py')): raise ValueError('Python uchun tests/test_*.py funksional testlari kerak')
                venv=self.w.root/'.venv'
                if venv.is_symlink() or not venv.resolve().is_relative_to(self.w.root): raise ValueError('venv symlink/junction taqiqlangan')
                if venv.exists(): shutil.rmtree(venv)
                python=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
                if not python.exists(): self.command([sys.executable,'-m','venv',str(venv)],'Python muhiti yaratish',180)
                requirements=self.w.root/'requirements.txt'
                if requirements.exists() and requirements.read_text(encoding='utf-8').strip():
                    self.command([str(python),'-m','pip','install','-r','requirements.txt'],'Python kutubxonalarini o‘rnatish',600)
                output=self.command([str(python),'-B','-m','unittest','discover','-s','tests','-v'],'Python funksional testlari',180)
                match=re.search(r'Ran (\d+) tests?',output)
                if not match or int(match[1])==0: raise ValueError('Hech qanday test bajarilmadi')
                tests='passed'
            elif profile=='android':
                import xml.etree.ElementTree as ET
                gradle=shutil.which('gradle')
                if not gradle: raise ValueError('Gradle PATH orqali topilishi kerak. JDK va Android SDK ni sozlang.')
                self.command([gradle,'--no-daemon',':app:clean',':app:testDebugUnitTest',':app:assembleDebug'],'Android test va APK',900)
                report=safe_path(self.w.root,'app/build/test-results/testDebugUnitTest')
                passed=0
                for xml in report.glob('TEST-*.xml'):
                    root=ET.parse(safe_path(report,xml.name)).getroot()
                    for case in root.iter('testcase'):
                        if case.find('failure') is not None or case.find('error') is not None:
                            raise ValueError('Android testi muvaffaqiyatsiz')
                        if case.find('skipped') is None: passed+=1
                if not passed: raise ValueError('Kamida bitta bajarilgan Android unit testi kerak')
                apk=safe_path(self.w.root,'app/build/outputs/apk/debug/app-debug.apk')
                with zipfile.ZipFile(apk) as built:
                    if not {'classes.dex','AndroidManifest.xml'}.issubset(built.namelist()):
                        raise ValueError('APK ichida manifest yoki classes.dex topilmadi')
                tests=f'{passed} Android unit testi'
            else:
                package=json.loads(self.w.read('package.json')); scripts=package.get('scripts',{})
                if not scripts.get('build') or not scripts.get('test'): raise ValueError('package.json da build va test skriptlari kerak; test bir marta bajarilib chiqsin')
                npm=shutil.which('npm'); node=shutil.which('node')
                if not npm or not node: raise ValueError('Node.js/npm topilmadi. Node.js LTS o‘rnating va botni qayta oching.')
                if (self.w.root/'node_modules').is_symlink(): raise ValueError('node_modules symlink taqiqlangan')
                # Use node + npm JS entry point on Windows instead of a shell command string.
                npm_cmd=[npm]
                if os.name=='nt':
                    cli=Path(npm).parent/'node_modules'/'npm'/'bin'/'npm-cli.js'
                    if not cli.is_file(): raise ValueError('Standart Node.js npm-cli.js topilmadi; Node.js LTS ni qayta o‘rnating')
                    npm_cmd=[node,str(cli)]
                install='ci' if (self.w.root/'package-lock.json').exists() else 'install'
                self.command(npm_cmd+[install,'--no-audit','--no-fund'],'Node kutubxonalarini o‘rnatish',600)
                self.command(npm_cmd+['run','test'],'Web funksional testlari',180)
                dist=safe_path(self.w.root,'dist')
                if dist.exists():
                    if not dist.is_dir(): raise ValueError('dist papka bo‘lishi kerak')
                    shutil.rmtree(dist)
                self.command(npm_cmd+['run','build'],'Web build',300)
                dist=self.w.root/'dist'
                if dist.is_symlink() or not dist.is_dir() or not any(p.is_file() for p in dist.rglob('*')):
                    raise ValueError('Build tugadi, lekin dist/ da haqiqiy natija yo‘q; build chiqishini dist/ ga sozlang')
                tests='passed_script_exit'
            if self.cancel.is_set(): raise InterruptedError()
            digest=source_digest(self.w)
            archive=self.archive(profile)
            return {'ok':True,'profile':profile,'tests':tests,'source_digest':digest,
                    'archive':str(archive),'archive_digest':hashlib.sha256(archive.read_bytes()).hexdigest(),
                    'logs':self.logs,'verified_at':time.time(),
                    'note':'Actual local command results. Does not prove full correctness or visual browser behavior.'}
        except InterruptedError: raise
        except Exception as exc: return {'ok':False,'profile':profile,'error':str(exc)[-10000:],'logs':self.logs}

    def archive(self,profile):
        self.exports.mkdir(parents=True,exist_ok=True)
        target=self.exports/(self.w.root.name+'_build.zip'); temp=target.with_suffix('.tmp')
        entries=[(p,'source/'+name) for p,name in source_entries(self.w)]
        if profile=='android':
            entries.append((safe_path(self.w.root,'app/build/outputs/apk/debug/app-debug.apk'),'app-debug.apk'))
        if profile=='web':
            root=self.w.root/'dist'
            for base,dirs,files in os.walk(root,followlinks=False):
                dirs[:]=[d for d in dirs if not (Path(base)/d).is_symlink()]
                for name in files:
                    p=Path(base)/name
                    if p.is_symlink(): raise ValueError('Build chiqishida symlink bor')
                    rel=p.relative_to(root).as_posix(); safe_path(root,rel)
                    entries.append((p,'dist/'+rel))
        if len(entries)>4000 or sum(p.stat().st_size for p,_ in entries)>40*1024*1024:
            raise ValueError('Build chiqishi 40 MiB/4000 fayl limitidan katta')
        with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
            for p,name in entries: z.write(p,name)
            z.writestr('BUILD_REPORT.json',json.dumps({'profile':profile,'commands':self.logs},ensure_ascii=False,indent=2))
        if temp.stat().st_size>15*1024*1024:
            temp.unlink(); raise ValueError('ZIP Telegram yuborish uchun 15 MiB dan katta; loyiha kompyuterda saqlandi')
        temp.replace(target); return target
