from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

EXTENSIONS=('.txt','.md','.vcf','.csv','.pdf','.docx')

def extract(name, data):
    suffix=Path(name).suffix.lower()
    if suffix=='.pdf':
        try:
            from pypdf import PdfReader
            reader=PdfReader(BytesIO(data))
            parts=[]
            for page in reader.pages[:4]:
                parts.append((page.extract_text() or '')[:8192])
            return ' '.join(parts)
        except Exception:
            return ''
    if suffix=='.docx':
        try:
            with ZipFile(BytesIO(data)) as archive:
                info=archive.getinfo('word/document.xml')
                if info.file_size>1024*1024: return ''
                xml=ElementTree.fromstring(archive.read(info))
                return ' '.join(node.text or '' for node in xml.iter() if node.tag.endswith('}t'))[:32768]
        except Exception:
            return ''
    return data[:262144].decode('utf8',errors='replace')
