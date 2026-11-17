#!/usr/bin/env python3
"""Export five aggregate/anonymized article figures as vector PDFs and 300 dpi PNGs."""
import argparse
from datetime import datetime, timedelta
import html
import json
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, MaxNLocator
from export_feedback_table import export_table

PURPLE='#6956a5';TEAL='#147d78';INK='#24222b';MUTED='#625d6a'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':INK,'text.color':INK,'xtick.color':MUTED,'ytick.color':MUTED,'axes.edgecolor':'#c8c4cd','pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white'})


def save(fig,path,title,footnote):
    fig.suptitle(title,x=.09,y=.965,ha='left',fontsize=19,fontweight='medium')
    if footnote: fig.text(.09,.025,footnote,fontsize=8.5,color=MUTED,va='bottom')
    fig.savefig(path.with_suffix('.pdf'),metadata={'Title':title,'Author':'Applied Overthinking'})
    fig.savefig(path.with_suffix('.png'),dpi=300)
    plt.close(fig)


def plot_base(height=5.5):
    fig,ax=plt.subplots(figsize=(11,height));fig.subplots_adjust(left=.09,right=.94,bottom=.20,top=.84)
    ax.grid(axis='y',color='#e9e6ed',linewidth=.7);ax.set_axisbelow(True)
    return fig,ax


def calendar_axis(ax,dates):
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.TH))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.set_xlim(dates[0]-timedelta(days=.5),dates[-1]+timedelta(days=1.4))
    ax.set_xlabel('Date (2026, Pacific time)',labelpad=10)


def export(report,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    archive=report['archive'];u=report['usage'];calendar=report['usage_calendar']
    if not u['available']:raise ValueError('Production usage data is required')
    assert sum(archive['years'].values())==archive['result_rows']
    assert sum(r['events'] for r in calendar)==u['events']
    assert sum(r['sessions_started'] for r in calendar)==u['sessions']
    figures=[]

    fig,ax=plot_base()
    years=[int(y) for y in archive['years']];counts=list(archive['years'].values())
    ax.bar(years,counts,width=.78,color=PURPLE)
    ax.set_xticks(years,[f"'{year % 100:02d}" for year in years]);ax.set_xlabel('Race year',labelpad=10);ax.set_ylabel('Race entries')
    ax.tick_params(axis='x',labelsize=10)
    fig.subplots_adjust(bottom=.15)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{int(v):,}'));ax.set_ylim(0,max(counts)*1.12)
    save(fig,out/'01-race-results-by-year','Race entries in the data by year','')
    figures.append(('PLOT OF RESULT DATES','01-race-results-by-year','Annual counts of archived race entries; these are race years, not collection dates.'))

    dates=[datetime.fromisoformat(r['day']) for r in calendar]
    total=other=0;all_events=[];non_heartbeat=[]
    for r in calendar:
        total+=r['events'];other+=r['non_heartbeat_events'];all_events.append(total);non_heartbeat.append(other)
    assert total==u['events'] and other==u['events']-u['actions'].get('engagement',0)
    fig,ax=plot_base()
    ax.plot(dates,all_events,color=PURPLE,linewidth=2.5)
    calendar_axis(ax,dates);ax.set_xlabel('Date (2026)',labelpad=10)
    ax.set_ylabel('Cumulative recorded events');ax.set_ylim(0,1120)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{int(v):,}'))
    fig.subplots_adjust(bottom=.15)
    save(fig,out/'02-cumulative-recorded-events','Recorded activity over time','')
    figures.append(('CUMULATIVE RECORDED EVENTS','02-cumulative-recorded-events','1,004 recorded events, including 429 engagement heartbeats; 575 other events.'))

    fig,ax=plot_base()
    starts=[r['sessions_started'] for r in calendar]
    ax.plot(dates,starts,color=PURPLE,linewidth=2,marker='o',markersize=4)
    ax.fill_between(dates,starts,color=PURPLE,alpha=.09)
    calendar_axis(ax,dates);ax.set_xlabel('Date (2026)',labelpad=10)
    ax.set_ylabel('Sessions first observed that day');ax.set_ylim(0,14)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    fig.subplots_adjust(bottom=.15)
    save(fig,out/'03-daily-sessions','Daily session starts','')
    figures.append(('SESSIONS OVER TIME','03-daily-sessions','Daily first-observed session IDs, including dates with zero recorded starts.'))

    cohorts=[r for r in u['cohorts'] if r['kind']=='week'];assert sum(r['sessions'] for r in cohorts)==u['sessions']
    columns=['Week starting','Sessions','Reached\nmatches','Opened\ncomparison','Loaded\ncomparison','Sent\nheart','Clicked\nShare','Median active\nseconds']
    body=[]
    outcome_keys=['matches_viewed','comparison_opened','comparison_ready','support_sent','share_clicked']
    for i,r in enumerate(cohorts):
        label=datetime.fromisoformat(r['cohort']).strftime('%b %d')+(' *' if i in [0,len(cohorts)-1] else '')
        body.append([label,str(r['sessions'])]+[f'{r[k]} ({100*r[k]/r["sessions"]:.1f}%)' for k in outcome_keys]+[f'{r["median_active_seconds"]:.2f}'])
    fig=plt.figure(figsize=(12,5.2));ax=fig.add_axes([.035,.25,.93,.56]);ax.axis('off')
    widths=[.125,.075,.135,.135,.135,.115,.115,.125]
    table=ax.table(cellText=body,colLabels=columns,cellLoc='center',colWidths=widths,bbox=[0,0,1,1]);table.auto_set_font_size(False);table.set_fontsize(10)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor('#d8d3de');cell.set_linewidth(.5)
        if r==0:cell.set_facecolor('#eae5f1');cell.set_text_props(weight='bold',color=INK)
        elif 2<=c<=6:
            rate=cohorts[r-1][outcome_keys[c-2]]/cohorts[r-1]['sessions'];cell.set_facecolor((.412,.337,.647,.04+.32*rate))
        else:cell.set_facecolor('white')
    save(fig,out/'04-weekly-session-cohorts','How weekly session cohorts progressed','October 31, 2026 export. *First and last weeks are partial.')
    figures.append(('COHORT ANALYSIS TABLE','04-weekly-session-cohorts','Weekly first-observed session cohorts, outcome counts/percentages, and median recorded active time.'))

    export_table(Path(__file__).resolve().parents[1]/'data/qualitative-coding.json',out/'05-qualitative-feedback.pdf')
    figures.append(('TABLE OF QUALITATIVE RESULTS','05-qualitative-feedback','Latest approved eight-row table, anonymous P01–P05 labels, positivity row, and one dot/blank note.'))

    cards=[]
    for placeholder,stem,caption in figures:
        cards.append(f'<section><h2>[{html.escape(placeholder)}]</h2><p><a href="{stem}.pdf">PDF</a> · <a href="{stem}.png">PNG</a></p><a href="{stem}.png"><img src="{stem}.png" alt="{html.escape(caption)}"></a><p>{html.escape(caption)}</p></section>')
    (out/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Applied Overthinking · Article figures</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font:16px/1.6 system-ui;max-width:1100px;margin:36px auto;padding:0 24px;background:#faf9f6;color:#24222b}img{max-width:100%;border:1px solid #e1dce7}a{color:#6956a5}section{margin:48px 0}h1{font-weight:500}</style><h1>Autopsy of a Startup Idea · Figures</h1><p>Five article figures, each supplied as a vector PDF and a high-resolution PNG. Usage data comes from the October 31, 2026 export.</p><p><a href="article-figures.zip">Download all figures (ZIP)</a></p>'+''.join(cards)+'</html>')
    (out/'figure-manifest.json').write_text(json.dumps({'usage_exported_at':u['exported_at'],'usage_sessions':u['sessions'],'usage_events':u['events'],'archive_rows':archive['result_rows'],'figures':[dict(placeholder=p,pdf=s+'.pdf',png=s+'.png',caption=c) for p,s,c in figures]},indent=2))
    with zipfile.ZipFile(out/'article-figures.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for _,stem,_ in figures:
            for suffix in ['.pdf','.png']:z.write(out/(stem+suffix),stem+suffix)
        z.write(out/'figure-manifest.json','figure-manifest.json')
    print('Exported five PDFs and five PNGs to',out)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,default=Path(__file__).resolve().parents[1]/'data/aggregate-report.json')
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'figures')
    args=parser.parse_args();export(json.loads(args.report.read_text()),args.out)
