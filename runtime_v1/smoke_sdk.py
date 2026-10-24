"""Offline SDK response-readiness/SSE shape smoke; no AWS calls."""
import asyncio
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from botocore.session import get_session
from botocore.validate import validate_parameters
from starlette.requests import Request
from runtime_v1 import main
from runtime_v1.core import DecisionEngine


class FakeModel:
    def __init__(self):
        self.completed = 0

    def converse(self, **request):
        shape = get_session().get_service_model('bedrock-runtime').operation_model('Converse').input_shape
        validate_parameters(request, shape)
        facts = json.loads(request['messages'][0]['content'][0]['text'])
        choice = next(o['index'] for o in facts['options'] if o['command']['commandType'] == 'SHOOT')
        self.completed += 1
        return {'output': {'message': {'content': [{'text': json.dumps({'choice': choice})}]}},
                'usage': {'inputTokens': 100, 'outputTokens': 5}}


class FakeMemory:
    def __init__(self):
        self.calls = []

    def create_event(self, **request):
        shape = get_session().get_service_model('bedrock-agentcore').operation_model('CreateEvent').input_shape
        validate_parameters(request, shape)
        self.calls.append(request)


async def smoke():
    main._engine = DecisionEngine(FakeModel(), 'test-model')
    main._memory = FakeMemory()
    os.environ['MEMORY_ID'] = 'TestOnly-0123456789'
    os.environ['WIRE_TEAM_SCOPE'] = 'explicit'
    os.environ['MEMORY_SAMPLE_EVERY'] = 'invalid-value-tests-safe-default'
    case = json.loads((Path(__file__).resolve().parents[1] /
                       'research/v3/selective-autonomy/fixtures.json').read_text())['cases'][1]
    context = SimpleNamespace(session_id='00000000-0000-0000-0000-000000000001')
    with patch('boto3.client', side_effect=AssertionError('Unexpected AWS client creation')), \
            patch.object(main.app.logger, 'info'):
        chunks = list(await main.invoke(json.loads(case['modelText']), context))
    assert len(chunks) == 1
    command = json.loads(chunks[0])
    assert command[0]['teamId'] == 1 and command[0]['commandType'] == 'SHOOT'
    assert len(main._memory.calls) == 1
    assert main._memory.calls[0]['sessionId'] == context.session_id
    stored = main._memory.calls[0]['payload'][1]['conversational']
    assert stored['role'] == 'ASSISTANT'
    assert json.loads(stored['content']['text'])['audit']['outcome'] == 'model_choice'
    async def receive():
        return {'type': 'http.request', 'body': case['modelText'].encode(), 'more_body': False}
    request = Request({'type': 'http', 'method': 'POST', 'path': '/invocations',
                       'headers': [(b'content-type', b'application/json'),
                                   (b'x-amzn-bedrock-agentcore-runtime-session-id', context.session_id.encode())]},
                      receive)
    completed_before = main._engine.client.completed
    with patch('boto3.client', side_effect=AssertionError('Unexpected AWS client creation')), \
            patch.object(main.app.logger, 'info'):
        response = await main.app._handle_invocation(request)
        # The previous outer async-generator implementation returned response
        # headers with no model work completed. This assertion catches that.
        assert main._engine.client.completed == completed_before + 1
        assert response.status_code == 200 and response.media_type == 'text/event-stream'
        raw = b''.join([part async for part in response.body_iterator])
    expected = ('data: ' + json.dumps(chunks[0], ensure_ascii=False) + '\n\n').encode()
    assert raw == expected
    with patch.dict(os.environ, {'WIRE_TEAM_SCOPE': 'bound', 'MEMORY_SAMPLE_EVERY': '1'}), \
            patch('boto3.client', side_effect=AssertionError('Unexpected AWS client creation')), \
            patch.object(main.app.logger, 'info'):
        response = await main.app._handle_invocation(request)
        bound_raw = b''.join([part async for part in response.body_iterator])
    bound_commands = json.loads(json.loads(bound_raw.decode().split('data: ', 1)[1].strip()))
    assert len(bound_commands) == 1 and bound_commands[0]['playerId'] == 3
    assert bound_commands[0]['commandType'] == 'SHOOT' and 'teamId' not in bound_commands[0]
    stored_bound = json.loads(main._memory.calls[-1]['payload'][1]['conversational']['content']['text'])
    assert 'teamId' not in stored_bound['commands'][0]
    assert stored_bound['audit']['teamId'] == 1
    assert stored_bound['audit']['wireTeamScope'] == 'bound'
    print('OFFLINE SDK smoke passed: decision complete before response, byte-identical SSE command, valid sampled event; no AWS calls')


if __name__ == '__main__':
    asyncio.run(smoke())
