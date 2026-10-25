import copy
import json
from pathlib import Path
import unittest

from mid_fast_v1.engine import MidEngine
from mid_fast_v1.evaluate import plan, digest
from mid_fast_v1.grade_native import grade, decode_response

ROOT=Path(__file__).resolve().parents[1]


class NativeGradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        engine=MidEngine();p=plan();artifact=json.loads((ROOT/'mid_fast_v1/artifact.json').read_text());cls.receipts=[]
        for row in p:
            commands,_=engine.choose(row['request'],row['sessionKey'])
            cls.receipts.append({k:row[k] for k in ('key','sessionKey','sequence','requestSha256')} |
                {'planSha256':digest(p),'archiveSha256':artifact['archiveSha256'],'requestWallMs':100.,
                 'complete':True,'streamError':None,'rawResponse':'data: '+json.dumps(json.dumps(commands))+'\n\n'})

    def test_mock_native_pass_does_not_promote_and_missing_deadline_fails(self):
        self.assertTrue(grade(self.receipts,1000,'synthetic unit-test deadline')['nativeGatePassed'])
        self.assertFalse(grade(self.receipts,1000,'synthetic unit-test deadline')['eligibleForRankedPromotion'])
        self.assertFalse(grade(self.receipts)['nativeGatePassed'])

    def test_first_call_and_stream_failure_count(self):
        for field,value in [('requestWallMs',1200),('complete',False),('streamError','Error')]:
            rows=copy.deepcopy(self.receipts);rows[0][field]=value
            self.assertFalse(grade(rows,1000,'synthetic')['nativeGatePassed'])
        self.assertFalse(grade(self.receipts[1:],1000,'synthetic')['nativeGatePassed'])
        self.assertFalse(grade(list(reversed(self.receipts)),1000,'synthetic')['nativeGatePassed'])

    def test_exact_hash_and_unique_receipts(self):
        rows=copy.deepcopy(self.receipts);rows[0]['archiveSha256']='wrong'
        with self.assertRaises(ValueError):grade(rows)
        with self.assertRaises(ValueError):grade(self.receipts+self.receipts[:1])

    def test_full_body_must_have_only_one_command_event(self):
        self.assertEqual(json.loads(decode_response(self.receipts[0]['rawResponse']))[0]['commandType'],'PASS')
        for extra in ('explanation','data: []','event: error'):
            with self.assertRaises(ValueError):decode_response(self.receipts[0]['rawResponse']+extra)


if __name__=='__main__':unittest.main()
