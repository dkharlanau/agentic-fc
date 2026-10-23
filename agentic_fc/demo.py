"""Offline quick demo with a synthetic state."""
from .policy import decide_payload

def main():
    ps=[]
    for side in ("home","away"):
        sign=1 if side=="home" else -1
        for pid,x,y in ((0,-49,0),(1,-28,6),(2,0,0),(3,27,-12),(4,29,13)):
            ps.append({"agentId":f"agentId_{pid}","teamCode":side,
                       "position":{"x":x*sign,"y":y},"stamina":0.75,
                       "hasBall":side=="home" and pid==2})
    payload={"teamId":0,"gameState":{"gameTime":80,"score":{"home":0,"away":0},
       "ball":{"position":{"x":0,"y":0},"isFree":False,"possessionAgentId":"agentId_2"},
       "players":ps}}
    for p in range(5):
        d=decide_payload(payload,p)
        print(p,d.reason,d.json())

if __name__=="__main__":
    main()
