#!/usr/bin/env python3
"""Read a PRIVATE collector export and write only aggregate statistics.

The input is never copied. Feedback, heart recipients and withdrawal rows are
never read. Session/page IDs are used in memory for grouping and never emitted.
"""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timedelta
import json
from pathlib import Path
import statistics
from zoneinfo import ZoneInfo

ZONE=ZoneInfo('America/Los_Angeles')
STAGES=['page_view','search_completed','athlete_selected','reference_ready','matches_viewed','comparison_opened','comparison_ready']
ALLOWED_EVENTS=set('page_view search_completed athlete_selected reference_selected reference_ready reference_unavailable filter_changed matches_viewed results_requested load_more comparison_opened comparison_ready comparison_closed share_clicked share_result shared_comparison_opened shared_comparison_unavailable photo_opened support_sent support_withdrawn ranking_changed opponent_search_completed opponent_selected error engagement'.split())

def timestamp(value):return datetime.fromisoformat(value.replace('Z','+00:00'))
def local_day(value):return timestamp(value).astimezone(ZONE).date()
def week(value):return (value-timedelta(days=value.weekday())).isoformat()
def median(values):return round(statistics.median(values),2) if values else None

def aggregate(snapshot):
    events=[]
    for raw in snapshot['tables'].get('events',[]):
        if raw['event'] not in ALLOWED_EVENTS:raise ValueError('Unexpected event type; review the collector schema before exporting')
        e={k:raw[k] for k in ['session_id','page_id','sequence','event','elapsed_ms','received_at']}
        e['properties']=json.loads(raw['properties']) if isinstance(raw['properties'],str) else raw['properties']
        events.append(e)
    by_session=defaultdict(list);daily=defaultdict(Counter)
    for e in events:
        by_session[e['session_id']].append(e)
        daily[local_day(e['received_at'])]['events']+=1
        if e['event']!='engagement':daily[local_day(e['received_at'])]['non_heartbeat_events']+=1
    cohorts=defaultdict(list);reach=Counter();funnel=Counter();active_values=[];times=[]
    for es in by_session.values():
        first=min(e['received_at'] for e in es);date=local_day(first);daily[date]['sessions_started']+=1
        starts={}
        for e in es:
            estimate=timestamp(e['received_at']).timestamp()-e['elapsed_ms']/1000
            starts[e['page_id']]=min(starts.get(e['page_id'],estimate),estimate)
        es.sort(key=lambda e:(starts[e['page_id']],e['sequence']))
        observed={e['event'] for e in es if e['event']!='engagement'};reach.update(observed);step=0
        for e in es:
            if step<len(STAGES) and e['event']==STAGES[step]:funnel[e['event']]+=1;step+=1
        active=sum(e['properties']['active_ms'] for e in es if e['event']=='engagement')/1000
        active_values.append(round(active,2))
        positive=any(e['event']=='matches_viewed' and e['properties']['result_count']>0 for e in es)
        cohorts[week(date)].append({'observed':observed,'positive':positive,'active':round(active,2)})
        views=[e for e in es if e['event']=='page_view']
        for e in es:
            if e['event']=='matches_viewed':
                pv=next((v for v in views if v['page_id']==e['page_id'] and v['sequence']<e['sequence']),None)
                if pv:times.append((e['elapsed_ms']-pv['elapsed_ms'])/1000);break
    rows=[]
    for label,sessions in sorted(cohorts.items()):
        row={'kind':'week','cohort':label,'sessions':len(sessions),'median_active_seconds':median([s['active'] for s in sessions])}
        for event in ['matches_viewed','comparison_opened','comparison_ready','support_sent','share_clicked']:
            row[event]=sum(event in s['observed'] for s in sessions)
        row['positive_matches']=sum(s['positive'] for s in sessions);rows.append(row)
    calendar=[]
    if events:
        start=min(local_day(e['received_at']) for e in events)
        end=local_day(snapshot['exported_at'])
        while start<=end:
            calendar.append({'day':start.isoformat(),**{k:daily[start][k] for k in ['sessions_started','events','non_heartbeat_events']}})
            start+=timedelta(days=1)
    # Explicitly construct all output fields. No private table/row is returned.
    return {'usage':{'available':True,'exported_at':snapshot['exported_at'],'sessions':len(by_session),'events':len(events),'actions':dict(Counter(e['event'] for e in events)),'reach':dict(reach),'ordered_funnel':{s:funnel[s] for s in STAGES},'median_active_seconds':median(active_values),'median_seconds_to_matches':median(times),'cohorts':rows},'usage_calendar':calendar}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='Private even-analysis-v1 JSON; keep outside this repository')
    p.add_argument('--archive',type=Path,default=Path(__file__).resolve().parents[1]/'data/archive-summary.json')
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    result=aggregate(json.loads(args.input.read_text()))
    result['archive']=json.loads(args.archive.read_text())
    args.out.write_text(json.dumps(result,indent=2)+'\n')
