"""Offline SDK generator/shape smoke using fake clients; makes no AWS calls."""
import asyncio
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from botocore.session import get_session
from botocore.validate import validate_parameters
from runtime_v1 import main
from runtime_v1.core import DecisionEngine


class FakeModel:
    def converse(self, **request):
        shape = get_session().get_service_model('bedrock-runtime').operation_model('Converse').input_shape
        validate_parameters(request, shape)
        facts = json.loads(request['messages'][0]['content'][0]['text'])
        choice = next(o['index'] for o in facts['options'] if o['command']['commandType'] == 'SHOOT')
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
    os.environ['MEMORY_SAMPLE_EVERY'] = 'invalid-value-tests-safe-default'
    case = json.loads((Path(__file__).resolve().parents[1] /
                       'research/v3/selective-autonomy/fixtures.json').read_text())['cases'][1]
    context = SimpleNamespace(session_id='00000000-0000-0000-0000-000000000001')
    with patch('boto3.client', side_effect=AssertionError('Unexpected AWS client creation')), \
            patch.object(main.app.logger, 'info'):
        chunks = [chunk async for chunk in main.invoke(json.loads(case['modelText']), context)]
    assert len(chunks) == 1
    command = json.loads(chunks[0])
    assert command[0]['teamId'] == 1 and command[0]['commandType'] == 'SHOOT'
    assert len(main._memory.calls) == 1
    assert main._memory.calls[0]['sessionId'] == context.session_id
    stored = main._memory.calls[0]['payload'][1]['conversational']
    assert stored['role'] == 'ASSISTANT'
    assert json.loads(stored['content']['text'])['audit']['outcome'] == 'model_choice'
    print('OFFLINE fake-client SDK smoke passed: one streamed AWAY command and shape-valid sampled event; no AWS calls')


if __name__ == '__main__':
    asyncio.run(smoke())
