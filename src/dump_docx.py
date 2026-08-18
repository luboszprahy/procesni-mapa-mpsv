import sys, zipfile, re
from xml.etree import ElementTree as ET
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
p=sys.argv[1]
z=zipfile.ZipFile(p)
x=ET.fromstring(z.read('word/document.xml'))
def txt(el):
    return ''.join(t.text or '' for t in el.iter(W+'t'))
body=x.find(W+'body')
out=[]
for el in body:
    if el.tag==W+'p':
        s=txt(el).strip()
        if s: out.append(s)
    elif el.tag==W+'tbl':
        out.append('--- TABULKA ---')
        for tr in el.findall(W+'tr'):
            cells=[txt(tc).strip().replace('\n',' ') for tc in tr.findall(W+'tc')]
            out.append(' | '.join(cells))
        out.append('--- /TABULKA ---')
print('\n'.join(out))
