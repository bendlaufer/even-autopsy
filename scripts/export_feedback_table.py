#!/usr/bin/env python3
"""Export the learning table using anonymous participant IDs only."""
import argparse
import json
from pathlib import Path
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse


def export_table(annotations, output):
    data=json.loads(Path(annotations).read_text())
    ids=[p['id'] for p in data['participants']]
    rows=data['learnings']; width,height=12,8
    fig=plt.figure(figsize=(width,height),facecolor='#faf9f6')
    ink='#24222b';purple='#6956a5';muted='#625d6a'
    fig.text(.045,.935,'What five triathletes told me: Learnings from user correspondences',fontsize=18,fontweight='medium',color=ink)
    xs=[.045,.335,.392,.449,.506,.563,.62,.955]
    top=.85;header_h=.055;bottom=.11
    fig.patches.append(Rectangle((xs[0],top-header_h),xs[-1]-xs[0],header_h,transform=fig.transFigure,facecolor='#eae5f1',edgecolor='none'))
    fig.text(xs[0]+.012,top-.034,'Learning',fontsize=10.5,fontweight='bold',color=ink)
    for i,pid in enumerate(ids):fig.text((xs[i+1]+xs[i+2])/2,top-.034,pid,ha='center',fontsize=10.5,fontweight='bold',color=ink)
    fig.text(xs[6]+.012,top-.034,'Takeaway',fontsize=10.5,fontweight='bold',color=ink)
    wrapped=[(textwrap.wrap(r['learning'],37),textwrap.wrap(r['takeaway'],43)) for r in rows]
    weights=[max(len(a),len(b))+1.5 for a,b in wrapped]
    available=top-header_h-bottom;y=top-header_h
    for row,(left,right),weight in zip(rows,wrapped,weights):
        h=available*weight/sum(weights);cy=y-h/2
        fig.lines.append(plt.Line2D([xs[0],xs[-1]],[y-h,y-h],transform=fig.transFigure,color='#d8d3de',linewidth=.65))
        fig.text(xs[0]+.012,cy,'\n'.join(left),va='center',fontsize=10.3,linespacing=1.45,color=ink)
        fig.text(xs[6]+.012,cy,'\n'.join(right),va='center',fontsize=10.3,linespacing=1.45,color=ink)
        for i,pid in enumerate(ids):
            if pid in row['participants']:
                fig.patches.append(Ellipse(((xs[i+1]+xs[i+2])/2,cy),.007,.007*width/height,transform=fig.transFigure,facecolor=purple,edgecolor='none'))
        y-=h
    fig.text(.045,.06,'A dot indicates that a respondent contributed evidence to a learning; a blank means it was not documented in their extract.',fontsize=8.8,color=muted)
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(output,format='pdf',metadata={'Title':'What five triathletes told me: Learnings from user correspondences','Author':'Applied Overthinking','Subject':'Anonymous qualitative feedback table'})
    fig.savefig(output.with_suffix('.png'),dpi=300)
    plt.close(fig)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--annotations',type=Path,default=Path(__file__).resolve().parents[1]/'data/qualitative-coding.json')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();export_table(args.annotations,args.out)
    print(args.out)
