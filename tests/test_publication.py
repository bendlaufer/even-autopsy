import json
from pathlib import Path
import sys
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from aggregate_usage import aggregate
from audit_publication import inspect_json,inspect_text

class PublicationTests(unittest.TestCase):
    def test_sensitive_tables_and_identifiers_never_leave_aggregation(self):
        sid=str(uuid.uuid4());pid=str(uuid.uuid4());private_email='private'+'@'+'example.invalid'
        fixture={'exported_at':'2026-10-03T12:00:00Z','tables':{
            'events':[{'session_id':sid,'page_id':pid,'event_id':str(uuid.uuid4()),'sequence':1,'event':'page_view','elapsed_ms':1000,'received_at':'2026-10-01T12:00:00Z','properties':'{"layout":"mobile"}'}],
            'feedback':[{'message':private_email}],
            'support_hearts':[{'recipient_name':'Unpublished respondent'}]}}
        result=aggregate(fixture);payload=json.dumps(result)
        self.assertNotIn(sid,payload);self.assertNotIn(pid,payload);self.assertNotIn(private_email,payload)
        self.assertNotIn('Unpublished respondent',payload);self.assertEqual(inspect_json(result,'fixture'),[])
        self.assertEqual([r['events'] for r in result['usage_calendar']],[1,0,0])

    def test_privacy_checks_catch_identifiers_and_unexpected_data(self):
        self.assertTrue(inspect_text('private'+'@'+'example.invalid','fixture'))
        self.assertTrue(inspect_text(str(uuid.uuid4()),'fixture'))
        self.assertTrue(inspect_text('A known person','fixture',['known person']))
        self.assertTrue(inspect_json({'participants':[{'name':'private'}]},'fixture'))

    def test_published_aggregate_invariants(self):
        data=json.loads((ROOT/'data/aggregate-report.json').read_text());u=data['usage']
        self.assertEqual(sum(r['sessions_started'] for r in data['usage_calendar']),60)
        self.assertEqual(sum(r['events'] for r in data['usage_calendar']),1004)
        self.assertEqual(sum(r['non_heartbeat_events'] for r in data['usage_calendar']),575)
        self.assertEqual(sum(r['sessions'] for r in u['cohorts']),60)
        self.assertEqual(u['reach']['search_completed'],27)
        self.assertEqual(u['reach']['matches_viewed'],25)
        self.assertEqual(u['reach']['comparison_ready'],12)
        self.assertEqual(u['median_seconds_to_matches'],8.54)

    def test_anonymous_coding_preserves_approved_matrix(self):
        data=json.loads((ROOT/'data/qualitative-coding.json').read_text())
        self.assertTrue(all(set(p)=={'id'} for p in data['participants']))
        self.assertEqual([p['id'] for p in data['participants']],['P01','P02','P03','P04','P05'])
        self.assertEqual(len(data['learnings']),8)
        self.assertEqual(data['learnings'][0]['participants'],['P01','P02','P03','P04','P05'])
        self.assertEqual(data['learnings'][0]['takeaway'],'')
        self.assertEqual([len(r['participants']) for r in data['learnings']],[5,1,3,2,2,2,2,1])

if __name__=='__main__':unittest.main()
