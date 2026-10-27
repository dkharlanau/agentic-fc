"""Same SDK response transport as the installed FWD5; no new model calls."""
import json
import os
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from fwd_power_v1.candidate import PowerEngine

if os.environ.get('PLAYER_ID', '4') != '4':
    raise ValueError('Finishing candidate is FWD5 only')
app = BedrockAgentCoreApp()
engine = PowerEngine()


def stream(commands):
    yield json.dumps(commands, separators=(',', ':'), allow_nan=False)


@app.entrypoint
async def invoke(payload, context):
    commands, audit = engine.choose(payload, getattr(context, 'session_id', None) or 'default')
    audit['buildCommit'] = os.environ.get('BUILD_COMMIT', 'local')
    audit['command'] = commands[0]
    app.logger.info('NHITL_FAST ' + json.dumps(audit, separators=(',', ':')))
    return stream(commands)


if __name__ == '__main__':
    app.run()
