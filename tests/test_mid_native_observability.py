"""Offline transport and admission regressions; no AWS calls or credentials."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from mid_fast_v1 import grade_native as grader
from mid_fast_v1.native_probe import collect, save
from mid_fast_v1.native_telemetry import observe_invoke, session_diagnostics, gate_diagnostics


class Body:
    def __init__(self, data=b'data: "[]"\n\n', read_error=None, close_error=None):
        self.data=data;self.read_error=read_error;self.close_error=close_error;self.closed=False

    def read(self):
        if self.read_error:raise self.read_error
        return self.data

    def close(self):
        self.closed=True
        if self.close_error:raise self.close_error


class Client:
    def __init__(self, body=None):
        self.body=body;self.calls=[];self.stops=[]

    def invoke_agent_runtime(self, **kwargs):
        self.calls.append(kwargs)
        return {'response':self.body or Body(),'runtimeSessionId':kwargs['runtimeSessionId'],
                'ResponseMetadata':{'HTTPStatusCode':200,'RetryAttempts':0,'RequestId':'PRIVATE_REQUEST_ID'}}

    def stop_runtime_session(self, **kwargs):
        self.stops.append(kwargs['runtimeSessionId'])


def receipt(key='a', index=0, token='a'*64, **extra):
    return dict(receiptSchemaVersion=2,sessionKey=key,sequence=index,sessionCallIndex=index,
                sessionFingerprint=token,responseSessionMatches=True,httpStatus=200,retryAttempts=0,**extra)


class ObserverTests(unittest.TestCase):
    def observe(self,client,clock=None):
        return observe_invoke(client,'PRIVATE_ARN','PRIVATE_SESSION',b'{}',b'unit-test-salt',0,clock)

    def test_full_response_timing_and_close(self):
        body=Body();clock=iter([0,1_300_000_000,1_301_000_000])
        row=self.observe(Client(body),lambda:next(clock))
        self.assertEqual(row['headersMs'],1300)
        self.assertEqual(row['requestWallMs'],1301)
        self.assertEqual(row['bodyAfterHeadersMs'],1)
        self.assertTrue(row['complete']);self.assertTrue(body.closed)
        self.assertTrue(row['responseSessionMatches']);self.assertEqual(row['retryAttempts'],0)

    def test_no_raw_identifiers_and_run_scoped_pseudonyms(self):
        row=self.observe(Client());text=json.dumps(row)
        for secret in ('PRIVATE_ARN','PRIVATE_SESSION','PRIVATE_REQUEST_ID'):
            self.assertNotIn(secret,text)
        other=observe_invoke(Client(),'arn','PRIVATE_SESSION',b'{}',b'other-salt',0)
        self.assertNotEqual(row['sessionFingerprint'],other['sessionFingerprint'])

    def test_read_failure_closes_stream(self):
        body=Body(read_error=OSError('PRIVATE_DETAIL'))
        row=self.observe(Client(body))
        self.assertFalse(row['complete']);self.assertEqual(row['streamError'],'OSError')
        self.assertTrue(body.closed);self.assertNotIn('PRIVATE_DETAIL',json.dumps(row))

    def test_decode_failure_closes_stream(self):
        body=Body(data=b'\xff');row=self.observe(Client(body))
        self.assertFalse(row['complete']);self.assertEqual(row['streamError'],'UnicodeDecodeError')
        self.assertTrue(body.closed)

    def test_close_failure_is_not_hidden(self):
        body=Body(close_error=OSError('PRIVATE_DETAIL'));row=self.observe(Client(body))
        self.assertTrue(row['complete']);self.assertEqual(row['streamCloseError'],'OSError')

    def test_exception_keeps_status_and_retries_without_message(self):
        class ServiceError(Exception):
            response={'ResponseMetadata':{'HTTPStatusCode':503,'RetryAttempts':1}}
        client=Client();client.invoke_agent_runtime=mock.Mock(side_effect=ServiceError('SECRET'))
        row=self.observe(client)
        self.assertFalse(row['complete']);self.assertIsNone(row['headersMs'])
        self.assertEqual(row['httpStatus'],503);self.assertEqual(row['retryAttempts'],1)
        self.assertNotIn('SECRET',json.dumps(row));self.assertEqual(client.invoke_agent_runtime.call_count,1)

    def test_absent_metadata_is_unknown_not_zero(self):
        client=Client();client.invoke_agent_runtime=mock.Mock(return_value={'response':Body()})
        row=self.observe(client)
        self.assertIsNone(row['httpStatus']);self.assertIsNone(row['retryAttempts'])
        self.assertIsNone(row['responseSessionMatches'])


class SessionTests(unittest.TestCase):
    def test_stable_interleaved_sessions(self):
        rows=[receipt(),receipt('b',0,'b'*64),receipt(index=1)]
        result=session_diagnostics(rows)
        self.assertEqual(result['issues'],[]);self.assertEqual(result['observedLogicalSessions'],2)
        self.assertFalse(result['serverSessionLifecycleVerified'])
        self.assertNotIn('a'*64,json.dumps(result))

    def test_changed_session_is_detected(self):
        result=session_diagnostics([receipt(),receipt(index=1,token='b'*64)])
        self.assertIn('session_changed_within_logical_session',result['issues'])

    def test_shared_sessions_are_detected(self):
        self.assertIn('session_shared_between_logical_sessions',
                      session_diagnostics([receipt(),receipt('b')])['issues'])

    def test_wrong_sequence_is_detected(self):
        self.assertIn('session_call_index_mismatch',session_diagnostics([receipt(index=1)])['issues'])

    def test_invalid_or_missing_v2_telemetry_is_not_accepted(self):
        for token in (None,'raw-session','g'*64):
            with self.subTest(token=token):
                self.assertIn('invalid_session_telemetry',session_diagnostics([receipt(token=token)])['issues'])

    def test_legacy_receipts_are_unknown_not_verified(self):
        result=session_diagnostics([{'sessionKey':'a','sequence':0}])
        self.assertEqual(result['status'],'not_recorded');self.assertEqual(result['issues'],[])
        self.assertFalse(result['serverSessionLifecycleVerified'])

    def test_partial_telemetry_is_detected(self):
        self.assertIn('partial_session_telemetry',session_diagnostics([receipt(),{'sessionKey':'b'}])['issues'])

    def test_bad_transport_metadata_fails(self):
        for field,value,issue in [('retryAttempts',1,'unexpected_retry_metadata'),
                                  ('retryAttempts',True,'unexpected_retry_metadata'),
                                  ('httpStatus',503,'unsuccessful_http_status'),
                                  ('responseSessionMatches',False,'response_session_mismatch'),
                                  ('streamCloseError','OSError','stream_cleanup_failed')]:
            with self.subTest(field=field,value=value):
                row=receipt();row[field]=value
                self.assertIn(issue,session_diagnostics([row])['issues'])


class CollectorTests(unittest.TestCase):
    def plan(self):
        return [{'key':str(i),'sessionKey':key,'sequence':index,'requestSha256':'synthetic',
                 'request':{'synthetic':i}} for i,(key,index) in enumerate([('a',0),('b',0),('a',1)])]

    def test_reuses_one_client_and_one_id_per_session(self):
        client=Client();checkpoints=[];session_checkpoints=[]
        rows,stopped=collect(client,'PRIVATE_ARN','L02',{'archiveSha256':'synthetic'},self.plan(),'synthetic',
                             lambda r:checkpoints.append(len(r)),session_checkpoints.append)
        ids=[r['runtimeSessionId'] for r in client.calls]
        self.assertEqual(ids[0],ids[2]);self.assertNotEqual(ids[0],ids[1])
        self.assertEqual(set(ids),set(client.stops));self.assertTrue(all(stopped.values()))
        self.assertEqual(checkpoints,[1,2,3]);self.assertEqual([r['sessionCallIndex'] for r in rows],[0,0,1])
        self.assertEqual(session_diagnostics(rows)['issues'],[])
        self.assertEqual(len(session_checkpoints[0]['sessions']),1)
        self.assertEqual(session_checkpoints[-1]['stopped'],stopped)

    def test_failure_stops_only_created_sessions_and_aborts_collection(self):
        client=Client(Body(read_error=OSError()))
        rows,stopped=collect(client,'arn','L02',{'archiveSha256':'x'},self.plan(),'p',lambda _:None,lambda _:None)
        self.assertEqual(len(rows),1);self.assertEqual(len(client.calls),1)
        self.assertEqual(set(stopped),{'a'});self.assertEqual(len(client.stops),1)

    def test_checkpoint_failure_still_stops_owned_session(self):
        client=Client()
        with self.assertRaises(OSError):
            collect(client,'arn','L02',{'archiveSha256':'x'},self.plan(),'p',
                    mock.Mock(side_effect=OSError()),lambda _:None)
        self.assertEqual(len(client.stops),1)

    def test_cleanup_failure_is_recorded(self):
        client=Client();client.stop_runtime_session=mock.Mock(side_effect=OSError())
        _,stopped=collect(client,'arn','L02',{'archiveSha256':'x'},self.plan(),'p',lambda _:None,lambda _:None)
        self.assertFalse(any(stopped.values()))

    def test_checkpoint_is_atomic_and_private(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'receipt.json'
            save(path,{'complete':False})
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            with self.assertRaises(ValueError):save(path,{'bad':float('nan')})
            self.assertEqual(json.loads(path.read_text()),{'complete':False})
            self.assertEqual(len(list(Path(directory).iterdir())),1)


class GateDiagnosticTests(unittest.TestCase):
    def summarize(self,rows,deadline=1000,p95=150,full=True):
        return gate_diagnostics(rows,full,deadline,p95,None if deadline is None else 800,session_diagnostics([]))

    def test_six_slow_first_calls_cannot_hide_in_good_p95(self):
        rows=[{'firstInSession':i<6,'late':i<6,'errors':[]} for i in range(224)]
        result=self.summarize(rows)
        self.assertEqual(result['failureReasons'],['first_session_call_deadline_exceeded'])
        self.assertEqual(result['firstCalls'],{'count':6,'invalid':0,'late':6})
        self.assertEqual(result['laterCalls'],{'count':218,'invalid':0,'late':0})

    def test_later_timeout_is_separate(self):
        result=self.summarize([{'firstInSession':False,'late':True,'errors':[]}])
        self.assertEqual(result['failureReasons'],['later_session_call_deadline_exceeded'])

    def test_missing_deadline_never_becomes_success(self):
        result=self.summarize([{'firstInSession':True,'late':None,'errors':[]}],deadline=None)
        self.assertIn('deadline_not_verified',result['failureReasons'])
        self.assertIsNone(result['firstCalls']['late'])

    def test_all_failures_remain_visible(self):
        result=self.summarize([{'firstInSession':True,'late':True,'errors':['bad']}],p95=1200,full=False)
        self.assertIn('incomplete_or_reordered_plan',result['failureReasons'])
        self.assertIn('invalid_or_incomplete_response',result['failureReasons'])
        self.assertIn('overall_p95_target_exceeded',result['failureReasons'])


class GradeCliTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.source=Path(self.temp.name)/'source.json';self.source.write_text('[]')
        self.target=Path(self.temp.name)/'grade.json'
        self.argv=[str(self.source),'--output',str(self.target)]

    def run_main(self):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            return grader.main(self.argv)

    def test_pass_exit_zero(self):
        with mock.patch.object(grader,'grade',return_value={'nativeGatePassed':True}):
            self.assertEqual(self.run_main(),0)

    def test_failed_gate_exit_one(self):
        with mock.patch.object(grader,'grade',return_value={'nativeGatePassed':False}):
            self.assertEqual(self.run_main(),1)
        self.assertFalse(json.loads(self.target.read_text())['nativeGatePassed'])

    def test_bad_input_replaces_stale_pass_and_exits_two(self):
        self.source.write_text('INVALID PRIVATE PAYLOAD')
        self.target.write_text('{"nativeGatePassed": true}')
        self.assertEqual(self.run_main(),2)
        text=self.target.read_text()
        self.assertFalse(json.loads(text)['nativeGatePassed']);self.assertNotIn('PRIVATE PAYLOAD',text)

    def test_grader_exception_exits_two(self):
        with mock.patch.object(grader,'grade',side_effect=ValueError('PRIVATE DETAIL')):
            self.assertEqual(self.run_main(),2)
        self.assertNotIn('PRIVATE DETAIL',self.target.read_text())

    def test_input_never_overwritten(self):
        self.argv=[str(self.source),'--output',str(self.source)]
        self.assertEqual(self.run_main(),2);self.assertEqual(self.source.read_text(),'[]')

    def test_real_subprocess_error_exit(self):
        self.source.write_text('not json')
        process=subprocess.run([sys.executable,str(Path(grader.__file__)),*self.argv],capture_output=True,text=True)
        self.assertEqual(process.returncode,2);self.assertFalse(json.loads(self.target.read_text())['nativeGatePassed'])


if __name__=='__main__':unittest.main()
