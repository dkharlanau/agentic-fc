"""Integration regressions against the real synthetic plan; no AWS calls."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from mid_fast_v1.engine import MidEngine
from mid_fast_v1.evaluate import plan, digest
from mid_fast_v1.grade_native import grade

ROOT=Path(__file__).resolve().parents[1]


class AdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        engine=MidEngine();p=plan();manifest=json.loads((ROOT/'mid_fast_v1/artifact.json').read_text())
        cls.receipts=[]
        for row in p:
            commands,_=engine.choose(row['request'],row['sessionKey'])
            cls.receipts.append({k:row[k] for k in ('key','sessionKey','sequence','requestSha256')} | {
                'planSha256':digest(p),'archiveSha256':manifest['archiveSha256'],
                'requestWallMs':100.,'complete':True,'streamError':None,
                'rawResponse':'data: '+json.dumps(json.dumps(commands))+'\n\n',
                'receiptSchemaVersion':2,'sessionCallIndex':row['sequence'],
                'sessionFingerprint':hashlib.sha256(row['sessionKey'].encode()).hexdigest(),
                'httpStatus':200,'retryAttempts':0,'responseSessionMatches':True})

    def test_full_plan_with_session_telemetry_passes_but_never_promotes(self):
        result=grade(self.receipts,1000,'synthetic deadline')
        self.assertTrue(result['nativeGatePassed']);self.assertEqual(result['failureReasons'],[])
        self.assertFalse(result['eligibleForRankedPromotion'])
        self.assertFalse(result['gameServerDeadlineVerified'])

    def test_real_cli_cold_failure_exits_one_despite_good_p95(self):
        rows=copy.deepcopy(self.receipts)
        for row in rows:
            if row['sequence']==0:row['requestWallMs']=1300.
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'synthetic.json';output=Path(directory)/'grade.json'
            source.write_text(json.dumps(rows))
            run=subprocess.run([sys.executable,str(ROOT/'mid_fast_v1/grade_native.py'),str(source),
                                '--deadline-ms','1000','--deadline-source','synthetic',
                                '--output',str(output)],capture_output=True,text=True)
            self.assertEqual(run.returncode,1,run.stderr)
            report=json.loads(output.read_text())
        self.assertLess(report['fullRequestMs']['p95'],800)
        self.assertEqual(report['firstCalls']['late'],6)
        self.assertEqual(report['laterCalls']['late'],0)
        self.assertIn('first_session_call_deadline_exceeded',report['failureReasons'])

    def test_session_mismatch_blocks_even_fast_valid_response(self):
        rows=copy.deepcopy(self.receipts);rows[0]['responseSessionMatches']=False
        result=grade(rows,1000,'synthetic')
        self.assertFalse(result['nativeGatePassed'])
        self.assertIn('response_session_mismatch',result['failureReasons'])

    def test_later_timeout_is_not_labelled_cold_start(self):
        rows=copy.deepcopy(self.receipts)
        next(row for row in rows if row['sequence']>0)['requestWallMs']=1300.
        result=grade(rows,1000,'synthetic')
        self.assertFalse(result['nativeGatePassed'])
        self.assertEqual(result['firstCalls']['late'],0)
        self.assertEqual(result['laterCalls']['late'],1)
        self.assertIn('later_session_call_deadline_exceeded',result['failureReasons'])

    def test_boolean_timing_is_rejected(self):
        rows=copy.deepcopy(self.receipts);rows[0]['requestWallMs']=True
        with self.assertRaises(ValueError):grade(rows,1000,'synthetic')

    def test_unexpected_retry_cannot_look_like_single_attempt(self):
        rows=copy.deepcopy(self.receipts);rows[0]['retryAttempts']=1
        result=grade(rows,1000,'synthetic')
        self.assertFalse(result['nativeGatePassed'])
        self.assertIn('unexpected_retry_metadata',result['failureReasons'])


if __name__=='__main__':unittest.main()
