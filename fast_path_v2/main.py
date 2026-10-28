"""Low-latency experimental role executor. No foundation-model call in request path."""
import json
import os
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from fast_path_v2.engine import FastEngine
app=BedrockAgentCoreApp()
engine=FastEngine(int(os.environ.get('PLAYER_ID','4')),os.environ.get('FWD2_MODE','stance'),os.environ.get('FWD2_SHOT_MODE','baseline'),os.environ.get('GK_MODE','baseline'))

def stream(commands):
    yield json.dumps(commands,separators=(',',':'),allow_nan=False)

@app.entrypoint
async def invoke(payload,context):
    commands,audit=engine.choose(payload,getattr(context,'session_id',None) or 'default')
    # Diagnostics are opt-in; avoid audit serialization on the game path.
    if os.environ.get('FAST_AUDIT', '0') == '1':
        audit['buildCommit']=os.environ.get('BUILD_COMMIT','local')
        audit['command']=commands[0]
        app.logger.info('NHITL_FAST '+json.dumps(audit,separators=(',',':')))
    return stream(commands)

if __name__=='__main__':app.run()
