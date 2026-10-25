"""Measurement integrity and candidate wire compatibility; no hosted calls."""
import asyncio
import copy
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import lab
import candidate_check
from fast_path_v2.engine import FastEngine


class FakeApp:
    def __init__(self):
        self.lines=[]
        self.logger=types.SimpleNamespace(info=self.lines.append)
    def entrypoint(self, fn):
        return fn


def entrypoint_module(path, trace=False):
    sdk=types.ModuleType('bedrock_agentcore.runtime')
    sdk.BedrockAgentCoreApp=FakeApp
    spec=importlib.util.spec_from_file_location('candidate_under_test',path)
    module=importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules,{'bedrock_agentcore.runtime':sdk}), patch.dict('os.environ',{'TRACE_TIMING':'1' if trace else '0','PLAYER_ID':'4','FWD2_MODE':'stance'}):
        spec.loader.exec_module(module)
    return module


def run(module,payload,session='offline'):
    generator=asyncio.run(module.invoke(copy.deepcopy(payload),types.SimpleNamespace(session_id=session)))
    return list(generator)


class EvidenceTests(unittest.TestCase):
    def test_candidate_gate_accepts_complete_safe_receipts_but_not_clear_only(self):
        cases={c['id']:c for c in candidate_check.evaluation_cases()}
        receipts=[]
        for request in candidate_check.plan():
            name=cases[request['case']]['expected'].get('types',['CLEAR_OVERRIDE'])[0]
            parameters={'PASS':{'target_player_id':2,'type':'GROUND'},
                        'SHOOT':{'aim_location':'TR','power':.8},'CLEAR_OVERRIDE':{}}[name]
            receipts.append({'key':request['key'],'modelId':request['modelId'],
                             'requestSha256':request['requestSha256'],'requestWallMs':500,
                             'complete':True,'responseText':json.dumps([{'commandType':name,
                             'playerId':3,'parameters':parameters,'duration':0}])})
        report=candidate_check.grade(receipts)
        self.assertTrue(report['offlineGatePassed'])
        self.assertFalse(report['eligibleForRankedPromotion'])
        for receipt in receipts:
            if ':P01:' in receipt['key']:
                receipt['responseText']='[{"commandType":"CLEAR_OVERRIDE","playerId":3,"parameters":{},"duration":0}]'
        self.assertFalse(candidate_check.grade(receipts)['offlineGatePassed'])

    def test_candidate_gate_cannot_pass_missing_or_incomplete_or_mismatched_receipts(self):
        report=candidate_check.grade([])
        self.assertFalse(report['offlineGatePassed'])
        self.assertIsNone(report['summary']['P01']['requestWallMs']['p95'])
        request=candidate_check.plan()[0]
        receipt={'key':request['key'],'modelId':request['modelId'],
                 'requestSha256':request['requestSha256'],'requestWallMs':1,'complete':False,
                 'responseText':'[{"commandType":"CLEAR_OVERRIDE","playerId":3,"parameters":{},"duration":0}]'}
        report=candidate_check.grade([receipt])
        self.assertFalse(report['rows'][0]['contractValid'])
        self.assertFalse(report['eligibleForRankedPromotion'])
        receipt['requestSha256']='wrong'
        with self.assertRaises(ValueError):candidate_check.grade([receipt])

    def test_null_and_small_sample_quantiles(self):
        self.assertEqual(lab.distribution([]),{'n':0,'p50':None,'p95':None,'max':None})
        self.assertEqual(lab.percentile([1,2,3,4],.95),3.85)
        self.assertEqual(lab.percentile([4],.95),4)
        self.assertEqual(lab.distribution([None,False,float('nan')])['n'],0)

    def test_contract_does_not_confuse_tactics_with_wire_validity(self):
        c={'commandType':'SHOOT','playerId':3,'parameters':{'power':.9,'aim_location':'TR'},'duration':0}
        self.assertEqual(lab.command_errors(json.dumps([c]),'fwd1'),[])
        case={'expected':{'types':['PASS']}}
        self.assertEqual(lab.decision_errors(case,c),['wrong_action'])
        c['duration']=False
        self.assertIn('duration',lab.command_errors(json.dumps([c]),'fwd1'))
        c['duration']=0;c['parameters']['power']=float('nan')
        self.assertIn('parameter_values',lab.command_errors(json.dumps([c]),'fwd1'))
        c['parameters']['power']=.8;c['playerId']=4
        self.assertIn('player',lab.command_errors(json.dumps([c]),'fwd1'))

    def test_extra_text_duplicate_keys_reset_and_malformed_values_fail(self):
        good='[{"commandType":"CLEAR_OVERRIDE","playerId":3,"parameters":{},"duration":0}]'
        for text in ('```json\n'+good+'\n```',good+' explanation',good.replace('"duration":0','"duration":1,"duration":0'),good.replace('CLEAR_OVERRIDE','RESET'),good.replace('CLEAR_OVERRIDE','[]'),good.replace('"CLEAR_OVERRIDE"','[]')):
            with self.subTest(text=text):self.assertTrue(lab.command_errors(text,'fwd1'))

    def test_new_role_suite_mirrors_and_hides_oracles(self):
        cases=lab.suite()
        self.assertEqual(len(cases),100)
        for case in cases:
            self.assertEqual(lab.mirrored(lab.mirrored(case))['input'],case['input'])
            request=lab.model_request(case,'prompt')
            self.assertEqual(set(request),{'system','messages','inferenceConfig'})
            self.assertNotIn('expected',json.dumps(request))
            self.assertNotIn(case['id'],json.dumps(request))
        self.assertEqual({c['role'] for c in cases},set(lab.ROLES))

    def test_archived_labels_prompt_hashes_and_pairing_reproduce(self):
        report=lab.replay()
        self.assertEqual(len(report['rows']),155)
        paired=report['pairedPromptGroups']
        for role in lab.ROLES:
            groups=[g for g in paired if g['role']==role]
            self.assertEqual(len({g['n'] for g in groups}),1)
        blank=next(c for c in report['coverage'] if c['role']=='gk' and c['prompt']=='schema-clean')
        self.assertEqual(blank['status'],'not_measured')
        self.assertIsNone(blank['p95Ms'])
        self.assertFalse(report['promotion']['eligible'])
        group=next(g for g in report['groups'] if g['prompt']=='compact-r2' and g['model']=='nova2')
        self.assertIsNone(group['usableLatencyMs']['p50'])

    def test_report_averages_never_become_invocation_percentiles(self):
        report=lab.latency_report()
        self.assertEqual(report['rootCause'],'not_identifiable_from_available_evidence')
        self.assertTrue(all(all(v is None for v in r['stageTimingsMs'].values()) for r in report['rows']))
        self.assertEqual(report['controlTeamAverageMs']['n'],7)


class CandidateTests(unittest.TestCase):
    def test_trace_preserves_actual_response_bytes_across_cases_and_history(self):
        # Same engine, same sessions, wrappers, malformed states and real fixtures.
        baseline=entrypoint_module(lab.ROOT/'fast_path_v2/main.py')
        candidate=entrypoint_module(HERE/'candidate/main.py',True)
        cases=lab.suite()
        for case in cases:
            sid=case['id']
            for message in case.get('history',[]):
                if message['role']=='user':
                    old=json.loads(message['content'][0]['text'])
                    self.assertEqual(run(baseline,old,sid),run(candidate,old,sid))
            for payload in (case['input'],{'prompt':json.dumps(case['input'])}):
                self.assertEqual(run(baseline,payload,sid),run(candidate,payload,sid))
        for payload in (None,[],{},'{broken',{'gameState':None}):
            self.assertEqual(run(baseline,payload),run(candidate,payload))
        for file in ('observed-fwd1-fitness-kickoff.json','observed-live-away-open-play.json'):
            payload=json.loads((lab.V3/'fixtures'/file).read_text())['decodedState']
            payload['myPlayers']=[4]
            self.assertEqual(run(baseline,payload,file),run(candidate,payload,file))

    def test_trace_events_distinguish_yield_from_delivery_and_tolerate_logger_failure(self):
        candidate=entrypoint_module(HERE/'candidate/main.py',True)
        payload=next(c for c in lab.suite() if c['role']=='fwd2')['input']
        result=run(candidate,payload)
        decision=json.loads(candidate.app.lines[0].split(' ',1)[1])['timing']
        yielded=json.loads(candidate.app.lines[1].split(' ',1)[1])
        self.assertEqual(decision['traceId'],yielded['traceId'])
        self.assertGreaterEqual(yielded['beforeYieldAfterEntryMs'],decision['chooseWallMs'])
        self.assertIsNone(yielded['serverAppliedUnixNs'])
        self.assertNotIn('sessionId',yielded)
        def broken(_):raise OSError('logger unavailable')
        candidate.app.logger.info=broken
        self.assertEqual(result,run(candidate,payload))

    def test_timing_is_opt_in_and_first_yield_does_not_claim_completion(self):
        candidate=entrypoint_module(HERE/'candidate/main.py',False)
        run(candidate,{})
        self.assertNotIn('timing',json.loads(candidate.app.lines[0].split(' ',1)[1]))
        candidate=entrypoint_module(HERE/'candidate/main.py',True)
        gen=asyncio.run(candidate.invoke({},types.SimpleNamespace(session_id='offline')))
        next(gen)
        self.assertEqual(len(candidate.app.lines),1)
        gen.close()
        self.assertEqual(len(candidate.app.lines),1)


if __name__=='__main__':unittest.main()
