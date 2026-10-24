#!/usr/bin/env python3
"""Compare invocation-only GK prompt/model overrides. Never update a Harness."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from agentic_fc.policy import valid_command
from runtime_v1.deploy import save_private


def assess(commands, case):
    expected = case['expected']
    if not isinstance(commands, list) or len(commands) != 1 or not isinstance(commands[0], dict):
        return {'formatPassed': False, 'candidateBehaviorAgreement': False}
    c = commands[0]
    known_side = c.get('teamId') if type(c.get('teamId')) is int else None
    fmt = valid_command(c, 0, known_side)
    agreement = fmt and c['commandType'] == expected['commandType']
    if 'targetHemisphere' in expected:
        agreement = agreement and c['parameters'].get('target_x', 0) * expected['targetHemisphere'] > 43
    if 'excludedTarget' in expected:
        agreement = agreement and c['parameters'].get('target_player_id') != expected['excludedTarget']
    if expected.get('teamIdAbsent'):
        agreement = agreement and 'teamId' not in c
    return {'formatPassed': fmt, 'candidateBehaviorAgreement': bool(agreement)}


def parse_answer(text):
    """Track strict JSON separately from a single Markdown code fence."""
    try:
        return json.loads(text), True
    except ValueError:
        fenced = re.fullmatch(r'\s*```(?:json)?\s*(.*?)\s*```\s*', text, re.S)
        if not fenced:
            raise
        return json.loads(fenced.group(1)), False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harness-file', type=Path, required=True, help='Private GetHarness backup for GK')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--region', default='us-east-1')
    parser.add_argument('--variant', choices=['baseline-nova', 'g1-nova', 'g1-haiku'], required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if '.local' not in args.output.resolve().parts:
        parser.error('Keep native receipts under .local')
    baseline = args.variant.startswith('baseline')
    prompt_path = ROOT / ('research/v3/schema-clean/gk.txt' if baseline else 'research/v3/keeper-g1/gk.txt')
    model_id = 'global.anthropic.claude-haiku-4-5-20251001-v1:0' if args.variant.endswith('haiku') \
        else 'global.amazon.nova-2-lite-v1:0'
    if not args.apply:
        print('Plan:10fresh synthetic sessions; invocation-only prompt/model overrides; stop own sessions.')
        return
    import boto3
    from botocore.config import Config
    client = boto3.client('bedrock-agentcore', region_name=args.region,
                          config=Config(connect_timeout=5, read_timeout=40, retries={'max_attempts': 0}))
    harness = json.loads(args.harness_file.read_text())['harness']
    cases = json.loads((Path(__file__).parent / 'fixtures.json').read_text())['cases']
    prompt = prompt_path.read_text()
    result = {'kind': 'Synthetic GK invocation overrides; no saved Harness changes',
              'variant': args.variant, 'model': model_id,
              'promptSha256': hashlib.sha256(prompt.encode()).hexdigest(),
              'limitations': ['Behavior agreement is the candidate policy target, not match strength.',
                              'Synthetic states add ownership fields not established in live inputs.'], 'results': []}
    for case in cases:
        sid = 'nhitl-g1-probe-' + str(uuid.uuid4())
        row = {'case': case['id'], 'sessionId': sid, 'stopped': False}
        result['results'].append(row)
        save_private(args.output, result)
        started = time.monotonic()
        try:
            response = client.invoke_harness(harnessArn=harness['arn'], qualifier='DEFAULT',
                runtimeSessionId=sid, messages=[{'role': 'user', 'content': [{'text': case['modelText']}]}],
                systemPrompt=[{'text': prompt}], model={'bedrockModelConfig': {
                    'modelId': model_id, 'apiFormat': 'converse_stream', 'maxTokens': 256, 'temperature': 0.0}},
                tools=[], allowedTools=[], skills=[], maxIterations=1, timeoutSeconds=20)
            text = ''
            for event in response['stream']:
                if 'contentBlockDelta' in event:
                    text += event['contentBlockDelta']['delta'].get('text', '')
                if 'metadata' in event:
                    row['metadata'] = event['metadata']
                for kind in ('internalServerException', 'validationException', 'runtimeClientError'):
                    if kind in event:
                        row['streamError'] = event[kind]
            row['elapsedMs'] = round((time.monotonic() - started) * 1000)
            row['modelText'] = text
            commands, strict = parse_answer(text)
            row['strictJSON'] = strict
            row['commands'] = commands
            row.update(assess(commands, case))
        except Exception as error:
            row['error'] = type(error).__name__ + ': ' + str(error)
        finally:
            try:
                client.stop_runtime_session(agentRuntimeArn=harness['arn'], runtimeSessionId=sid,
                                            qualifier='DEFAULT')
                row['stopped'] = True
            except Exception as error:
                row['stopError'] = type(error).__name__ + ': ' + str(error)
            save_private(args.output, result)
        print(json.dumps({k: row.get(k) for k in ('case', 'elapsedMs', 'formatPassed',
                          'candidateBehaviorAgreement', 'commands', 'stopped', 'error')}, default=str), flush=True)
        if not row['stopped']:
            raise SystemExit('Own session cleanup needs inspection before continuing probes.')


if __name__ == '__main__':
    main()
