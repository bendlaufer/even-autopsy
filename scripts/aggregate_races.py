#!/usr/bin/env python3
"""Count public race entries by year without exporting athlete-level rows."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

def summarize(directory):
    years=Counter();editions=Counter();races=set();size=0;fields=Counter();statuses=Counter();headers=set();files=sorted(Path(directory).glob('*.csv'))
    for path in files:
        race,year=path.stem.rsplit('_',1);races.add(race);editions[year]+=1;size+=path.stat().st_size
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);headers.update(reader.fieldnames or [])
            for row in reader:
                if not any(row.values()):continue
                years[year]+=1;statuses[row.get('Status','not recorded')]+=1
                for key in ['Athlete Name','City','State','Country','Gender','Division','Bib Number']:
                    if (row.get(key) or '').strip():fields[key]+=1
    annual=[]
    for year,count in sorted(years.items()):
        previous=years.get(str(int(year)-1))
        annual.append({'year':year,'entries':count,'race_editions':editions[year],'entries_per_edition':round(count/editions[year],1),'year_over_year_percent':round(100*(count/previous-1),1) if previous else None})
    return {'csv_files':len(files),'race_series':len(races),'result_rows':sum(years.values()),'csv_bytes':size,'years':dict(sorted(years.items())),'annual':annual,'nonempty_fields':dict(fields),'statuses':dict(statuses),'headers':sorted(headers)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.write_text(json.dumps(summarize(a.results),indent=2)+'\n')
