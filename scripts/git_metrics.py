#!/usr/bin/env python3
"""Recompute the published source-code metrics from an authorized app checkout."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

SOURCE={'.py','.js','.mjs','.css','.html'}

def code_history(root, commits):
    product=[c for c in commits if c['on_main'] and c['category']=='Even product']
    refs=[('539f9fd','2026-09-07','Inspected upstream baseline')]+[(c['sha'],c['day'],c['subject']) for c in product]
    trees=[]; wanted=set()
    for sha,day,subject in refs:
        result=subprocess.check_output(['git','-C',str(root),'ls-tree','-r','-l',sha],text=True)
        entries=[]
        for line in result.splitlines():
            meta,path=line.split('\t',1); mode,kind,oid,size=meta.split()
            if kind!='blob':continue
            category=('archive' if path.startswith('results/') else 'documentation' if path.startswith('docs/') or Path(path).suffix=='.md' else 'tests' if Path(path).name.startswith('test-') and Path(path).suffix in SOURCE else 'application' if Path(path).suffix in SOURCE else 'other')
            entries.append((path,oid,int(size),category))
            if category in ['application','tests']: wanted.add(oid)
        trees.append((sha,day,subject,entries))
    # Batch read unique source blobs once, without checking out or changing files.
    request=''.join(oid+'\n' for oid in sorted(wanted)).encode()
    response=subprocess.run(['git','-C',str(root),'cat-file','--batch'],input=request,stdout=subprocess.PIPE,check=True).stdout
    lines={}; pos=0
    while pos<len(response):
        stop=response.index(b'\n',pos); oid,kind,size=response[pos:stop].decode().split(); size=int(size);pos=stop+1
        content=response[pos:pos+size]; lines[oid]=len(content.splitlines()); pos+=size+1
    rows=[]
    for sha,day,subject,entries in trees:
        c=Counter();c['tracked_files']=len(entries)
        for path,oid,size,category in entries:
            c['tracked_bytes']+=size;c[category+'_bytes']+=size;c[category+'_files']+=1
            if category in ['application','tests']:c[category+'_lines']+=lines[oid]
        for category in ['application','tests','documentation','archive','other']:
            for suffix in ['files','bytes']+(['lines'] if category in ['application','tests'] else []): c.setdefault(category+'_'+suffix,0)
        rows.append(dict(day=day,sha=sha,subject=subject,**c))
    # Measure each product change against its prior product snapshot; the first
    # uses inspected upstream, avoiding the main branch's upstream reimport spike.
    changes=[]; previous='539f9fd'
    for commit in product:
        counters=Counter()
        raw=subprocess.check_output(['git','-C',str(root),'diff','--numstat',previous,commit['sha'],'--','.',':(exclude)results/**',':(exclude)screenshots/**'],text=True)
        for line in raw.splitlines():
            a,b,path=line.split('\t',2)
            if not a.isdigit() or not b.isdigit():continue
            counters['added_nonarchive']+=int(a);counters['removed_nonarchive']+=int(b)
            if Path(path).suffix in SOURCE and not path.startswith('docs/'):
                counters['added_source']+=int(a);counters['removed_source']+=int(b)
        changes.append(dict(day=commit['day'],sha=commit['sha'],subject=commit['subject'],**{k:counters[k] for k in ['added_nonarchive','removed_nonarchive','added_source','removed_source']}));previous=commit['sha']
    return dict(snapshots=rows,changes=changes,totals=dict(sum((Counter({k:r[k] for k in ['added_nonarchive','removed_nonarchive','added_source','removed_source']}) for r in changes),Counter())),definition='Application source = tracked Python, JS/MJS, CSS and HTML outside docs, results and test-* files. Tests reported separately. Line counts include blank lines/comments. Bytes are tracked Git blob sizes, not disk allocation or dependencies. First product diff is against inspected upstream 539f9fd; later diffs use the preceding product snapshot. Churn counts intermediate edits; net additions count only surviving differences. Commits are not deployment times and do not identify human vs agent authorship.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--manifest',type=Path,default=Path(__file__).resolve().parents[1]/'data/development.json')
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    manifest=json.loads(args.manifest.read_text())
    commits=[{'sha':r['sha'],'day':r['day'],'subject':r['subject'],'on_main':True,'category':'Even product'} for r in manifest['changes']]
    result=code_history(args.repo,commits)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
