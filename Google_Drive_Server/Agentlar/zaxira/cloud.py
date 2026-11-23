"""Optional encrypted S3 copy; the vault key stays with the owner."""
import base64
import json
import os
import re

def archive(vault, ident, name, data):
    def pack(label,payload):
        return base64.b64encode(vault.seal(ident,label,payload)).decode()
    return json.dumps({'name':pack('name',name.encode()),'file':pack('file',data)}).encode()

def unpack(vault,ident,raw):
    fields=json.loads(raw)
    def decrypt(label):
        return vault.unseal(ident,label,base64.b64decode(fields[label],validate=True))
    return decrypt('name').decode(),decrypt('file')

def client():
    import boto3
    endpoint=os.environ.get('ZAXIRA_S3_ENDPOINT')
    if endpoint and not endpoint.startswith('https://'):
        raise ValueError('S3 manzili HTTPS bo‘lishi kerak')
    return boto3.client('s3',endpoint_url=endpoint)

def mirror(vault,ident,name,data):
    bucket=os.environ.get('ZAXIRA_S3_BUCKET')
    if bucket:
        client().put_object(Bucket=bucket,Key=f'zaxira/{vault.owner}/{ident}.json',
                            Body=archive(vault,ident,name,data),ContentType='application/json')

def restore_cloud():
    from .store import Vault
    from pathlib import Path
    from agentlar.config import load_config
    root=Path(__file__).resolve().parents[1]
    if not (root/'private_backup'/'vault.key').exists():
        raise ValueError('Avval asl vault.key nusxasini tiklang')
    vault=Vault(root/'private_backup',load_config(root)['owner_id'])
    s3=client();bucket=os.environ['ZAXIRA_S3_BUCKET'];prefix=f'zaxira/{vault.owner}/'
    count=0
    for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket,Prefix=prefix):
        for item in page.get('Contents',[]):
            key=item['Key'];match=re.fullmatch(re.escape(prefix)+r'([0-9a-f]{16})\.json',key)
            if match:
                body=s3.get_object(Bucket=bucket,Key=key)['Body']
                try: name,data=unpack(vault,match[1],body.read(16*1024*1024))
                finally: body.close()
                vault.add(name,data);count+=1
    print('Tekshirilgan va tiklangan nusxalar:',count)

if __name__=='__main__': restore_cloud()
