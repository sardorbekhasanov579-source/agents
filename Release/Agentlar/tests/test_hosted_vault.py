import json
import re
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from hosted_vault import accepted_text
from zaxira.receiver import Server
from zaxira.store import Vault

class HostedTest(unittest.TestCase):
    def test_cloud_restore_after_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            vault=Vault(Path(temp),432)
            vault.add("Diplom.txt",b"ilmiy diplom")
            for iteration in range(2):
                with Server(vault,0) as server:
                    thread=threading.Thread(target=server.serve_forever)
                    thread.start()
                    try:
                        root='http://127.0.0.1:'+str(server.server_port)
                        def post(path,**fields):
                            with urlopen(root+path,data=urlencode(fields).encode(),timeout=5) as result:
                                return result.read()
                        if iteration==0:
                            server.enroll.send=lambda method,fields: {'status':'approved'}
                            grant=server.enroll.issue()
                            html=post('/register/start',grant=grant,phone='+998000000000',email='test@gmail.com')
                            nonce=re.search(b'name=nonce value="([^"]+)',html)[1].decode()
                            code=re.search(b'<code>([^<]+)',post('/register/finish',nonce=nonce,sms='000',emailcode='000',
                                                                password='testpassword123'))[1].decode()
                        with urlopen(root+'/health') as health: self.assertTrue(json.load(health)['ok'])
                        rows=json.loads(post('/restore.json',phone='+998000000000',password='testpassword123',code=code,
                                             query='diplomimni topib ber'))
                        self.assertEqual(post('/download',ticket=rows[0]['ticket']),b'ilmiy diplom')
                    finally:
                        server.shutdown();thread.join()
    def test_private_owner(self):
        message={'from':{'id':1},'chat':{'type':'private','id':1},'text':'/zpair'}
        self.assertEqual(accepted_text(message,1),'/zpair')
        self.assertEqual(accepted_text(message,2),'')
        message['chat']['type']='group'
        self.assertEqual(accepted_text(message,1),'')

    def test_documents(self):
        from io import BytesIO
        from zipfile import ZipFile
        from zaxira.document_text import extract
        doc=BytesIO()
        with ZipFile(doc,'w') as archive:
            archive.writestr('word/document.xml','<w:document xmlns:w="urn:word"><w:t>Diplom</w:t></w:document>')
        self.assertEqual(extract('a.docx',doc.getvalue()),'Diplom')
        self.assertEqual(extract('broken.pdf',b'%PDF'),'')

    def test_android_artifact(self):
        import zipfile
        from unittest.mock import patch
        from agentlar.build import LocalBuilder
        from agentlar.core import Workspace
        with tempfile.TemporaryDirectory() as path:
            root=Path(path)/'sample';root.mkdir()
            workspace=Workspace(root,{})
            workspace.write('settings.gradle',"include ':app'")
            builder=LocalBuilder(workspace,Path(path)/'out',threading.Event(),lambda _:None)
            def simulate(argv,label,timeout):
                report=root/'app/build/test-results/testDebugUnitTest'
                report.mkdir(parents=True)
                (report/'TEST-app.xml').write_text('<testsuite><testcase name="sample"/></testsuite>')
                apk=root/'app/build/outputs/apk/debug/app-debug.apk';apk.parent.mkdir(parents=True)
                with zipfile.ZipFile(apk,'w') as z:
                    z.writestr('classes.dex','stub');z.writestr('AndroidManifest.xml','stub')
            with patch('shutil.which',return_value='/gradle'),patch.object(builder,'command',side_effect=simulate):
                built=builder.build('android')
            self.assertTrue(built['ok'],built)
            with zipfile.ZipFile(built['archive']) as archive:self.assertIn('app-debug.apk',archive.namelist())
