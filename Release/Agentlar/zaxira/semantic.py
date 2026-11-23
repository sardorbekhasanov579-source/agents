from .document_text import EXTENSIONS, extract
import json
import math
from urllib.request import Request,urlopen
from pathlib import Path

def search(vault,query):
    def embed(text):
        request=Request('http://127.0.0.1:11434/api/embed',data=json.dumps(
            {'model':'bge-m3','input':text}).encode(),headers={'Content-Type':'application/json'})
        with urlopen(request,timeout=60) as response:
            vector=json.load(response)['embeddings'][0]
        length=math.sqrt(sum(v*v for v in vector))
        return [v/length for v in vector]
    target=embed(query)
    results=[]
    for row in vault.search('',limit=1000):
        ident,name,size,_=row
        snippet=name
        if size<=2*1024*1024 and Path(name).suffix.lower() in EXTENSIONS:
            snippet+=' '+extract(name,vault.get(ident)[1])
        vector=embed(snippet[:3000])
        results.append((sum(a*b for a,b in zip(target,vector)),row))
    return [row for _,row in sorted(results,reverse=True)[:5]]
