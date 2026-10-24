"""AgentCore streaming entrypoint. No IAM provisioning or tool execution."""
import asyncio
from datetime import datetime, timezone
import json
import os
import threading
import uuid

import boto3
from botocore.config import Config
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from runtime_v1.core import DecisionEngine, unwrap

app = BedrockAgentCoreApp()
_engine = None
_memory = None
_lock = threading.Lock()
_counts = {}


def engine():
    global _engine
    with _lock:
        if _engine is None:
            client = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'us-east-1'),
                                  config=Config(connect_timeout=2, read_timeout=4,
                                                retries={'max_attempts': 0}))
            _engine = DecisionEngine(client, os.getenv('MODEL_ID', 'global.amazon.nova-2-lite-v1:0'),
                                     player_id=int(os.getenv('PLAYER_ID', '3')))
        return _engine


def memory_sample(payload, commands, audit, session_id):
    global _memory
    memory_id = os.getenv('MEMORY_ID')
    if not memory_id:
        return 'not_configured'
    with _lock:
        count = _counts.get(session_id, 0) + 1
        _counts[session_id] = count
        if len(_counts) > 64:
            oldest = next(iter(_counts))
            if oldest != session_id:
                del _counts[oldest]
    try:
        every = max(1, min(1000, int(os.getenv('MEMORY_SAMPLE_EVERY', '10'))))
    except (TypeError, ValueError):
        every = 10
    if (count - 1) % every:
        return 'not_sampled'
    try:
        if _memory is None:
            _memory = boto3.client('bedrock-agentcore', region_name=os.getenv('AWS_REGION', 'us-east-1'),
                                  config=Config(connect_timeout=2, read_timeout=2,
                                                retries={'max_attempts': 0}))
        _memory.create_event(memoryId=memory_id,
                             actorId=os.getenv('MEMORY_ACTOR_ID', 'r1_fwd1'),
                             sessionId=session_id, eventTimestamp=datetime.now(timezone.utc),
                             payload=[{'conversational': {'role': 'USER', 'content': {
                                 'text': json.dumps({'input': unwrap(payload)}, separators=(',', ':'))}}},
                                      {'conversational': {'role': 'ASSISTANT', 'content': {
                                 'text': json.dumps({'commands': commands, 'audit': audit}, separators=(',', ':'))}}}])
        return 'written'
    except Exception as error:
        return 'error_' + type(error).__name__


@app.entrypoint
async def invoke(payload, context):
    # A single decision needs one JSON array, not an SSE frame containing a
    # second JSON string. Keep model work before the completed HTTP response.
    session_id = getattr(context, 'session_id', None) or str(uuid.uuid4())
    try:
        commands, audit = await asyncio.to_thread(engine().choose, payload, session_id)
    except ValueError as error:
        root = unwrap(payload)
        rejected = {'adapter': 'r1', 'outcome': 'rejected_input', 'modelAttempted': False,
                    'error': str(error), 'rootKeys': sorted(root),
                    'unlockedCommands': root.get('unlockedCommands'), 'teamId': root.get('teamId'),
                    'myPlayers': root.get('myPlayers'), 'buildCommit': os.getenv('BUILD_COMMIT', 'local')}
        rejected['memoryOutcome'] = await asyncio.to_thread(memory_sample, payload, [], rejected, session_id)
        app.logger.error('NHITL_INPUT_REJECTED ' + json.dumps(rejected, separators=(',', ':')))
        raise
    audit['memoryOutcome'] = await asyncio.to_thread(memory_sample, payload, commands, audit, session_id)
    audit['buildCommit'] = os.getenv('BUILD_COMMIT', 'local')
    app.logger.info('NHITL_DECISION ' + json.dumps(audit, separators=(',', ':')))
    return commands


if __name__ == '__main__':
    app.run()
