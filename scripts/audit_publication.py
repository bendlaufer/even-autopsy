#!/usr/bin/env python3
"""Check the release tree, including PDF text/metadata and nested ZIP entries.

--private-reference may point to an unpublished coding file for an additional
name check. Neither that file nor its contents are written to the release tree.
"""
import argparse
import io
import json
from pathlib import Path
import re
import zipfile
from PIL import Image
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
EMAIL=re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
UUID=re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',re.I)
LOCAL_HOME=re.compile(r'/(?:Users|home)/[^/\s]+')
PRIVATE_KEYS={'name','email','recipient_name','session_id','page_id','event_id','request_id','transcript','excerpts','relationship','channel','feedback','support_hearts','support_withdrawals','tables','sessions_detail','recent_sessions'}
TEXT_SUFFIXES={'.py','.json','.md','.txt','.html','.yml','.yaml','.csv'}
ALLOWED_ROOT={'README.md','LICENSE','requirements.txt','requirements-dev.txt','.gitignore'}
ALLOWED_DIRS={'scripts','data','figures','tests','.github'}

def inspect_text(text,label,names=()):
    issues=[]
    for pattern,kind in [(EMAIL,'email address'),(UUID,'opaque UUID'),(LOCAL_HOME,'local home-directory path')]:
        if pattern.search(text):issues.append(label+': '+kind)
    for name in names:
        if re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',text,re.I):issues.append(label+': private respondent name')
    return issues

def inspect_json(value,label):
    issues=[]
    if isinstance(value,dict):
        for key,item in value.items():
            if key in PRIVATE_KEYS:issues.append(label+': forbidden data field '+key)
            issues+=inspect_json(item,label)
    elif isinstance(value,list):
        for item in value:issues+=inspect_json(item,label)
    return issues

def inspect_bytes(content,label,names=()):
    suffix=Path(label).suffix.lower();issues=[]
    if suffix in TEXT_SUFFIXES or Path(label).name in ALLOWED_ROOT:
        text=content.decode('utf-8');issues+=inspect_text(text,label,names)
        if suffix=='.json':issues+=inspect_json(json.loads(text),label)
    elif suffix=='.pdf':
        pdf=PdfReader(io.BytesIO(content))
        issues+=inspect_text('\n'.join(p.extract_text() or '' for p in pdf.pages),label,names)
        issues+=inspect_text(str(pdf.metadata),label+' metadata',names)
    elif suffix=='.png':
        image=Image.open(io.BytesIO(content));image.verify()
        issues+=inspect_text(str(image.info),label+' metadata',names)
    elif suffix=='.zip':
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            if z.testzip():issues.append(label+': ZIP integrity failure')
            for entry in z.namelist():
                p=Path(entry)
                if len(p.parts)!=1 or p.suffix not in {'.pdf','.png','.json'}:issues.append(label+': unexpected ZIP entry')
                else:issues+=inspect_bytes(z.read(entry),label+'/'+entry,names)
    else:issues.append(label+': unexpected file format')
    return issues

def audit(root,names=()):
    root=Path(root);issues=[];files=[]
    for path in sorted(root.rglob('*')):
        rel=path.relative_to(root)
        if any(part in {'.git','__pycache__','.venv'} for part in rel.parts) or not path.is_file():continue
        if rel.parts[0] not in ALLOWED_DIRS and str(rel) not in ALLOWED_ROOT:issues.append(str(rel)+': unexpected release path')
        files.append(str(rel));issues+=inspect_bytes(path.read_bytes(),str(rel),names)
    coding=json.loads((root/'data/qualitative-coding.json').read_text())
    if set(coding)!={'participants','learnings'}:issues.append('Unexpected qualitative top-level fields')
    if any(set(r)!={'id'} for r in coding['participants']):issues.append('Respondents must have only an anonymous ID')
    if any(set(r)!={'learning','participants','takeaway'} for r in coding['learnings']):issues.append('Unexpected qualitative row fields')
    return files,issues

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--private-reference',type=Path)
    args=p.parse_args();names=[]
    if args.private_reference:
        private=json.loads(args.private_reference.read_text());names=[r['name'] for r in private['participants']]
    files,issues=audit(args.root,names)
    if issues:raise SystemExit('\n'.join(issues))
    print('PASS: inspected '+str(len(files))+' release files, including PDF text/metadata, PNG metadata, and ZIP contents.')
