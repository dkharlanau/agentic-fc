"""MID-only experimental Runtime entrypoint. Never invokes a foundation model."""
import json
import os
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mid_fast_v1.engine import MidEngine

if os.environ.get('PLAYER_ID','2') != '2':
    raise ValueError('L01 can only control MID/player 2')
app = BedrockAgentCoreApp()
engine = MidEngine()


def stream(commands):
    yield json.dumps(commands,separators=(',',':'),allow_nan=False)


@app.entrypoint
async def invoke(payload, context):
    commands, audit = engine.choose(payload, getattr(context,'session_id',None))
    if os.environ.get('MID_AUDIT','0') == '1':
        # Optional compact diagnostics; never logs payload, raw positions or IDs.
        audit['commandType'] = commands[0]['commandType']
        audit['buildCommit'] = os.environ.get('BUILD_COMMIT','local')
        try:
            app.logger.info('MID_L01 '+json.dumps(audit,separators=(',',':'),allow_nan=False))
        except Exception:
            pass
    return stream(commands)


if __name__ == '__main__':
    app.run()
