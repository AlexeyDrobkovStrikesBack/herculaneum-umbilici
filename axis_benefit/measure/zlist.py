"""The pre-registered slice list: 30 z per scroll, evenly spaced over the
annotated z-range, endpoints included, snapped down to an even level-0 index."""
import json
SC=json.load(open('/home/alexr/vesuvius/_axisdemo/scroll_meta.json'))
N=30
def zs(s):
    m=SC[s]; a,b=m['zmin'],m['zmax']
    out=[]
    for k in range(N):
        z=round(a+k*(b-a)/(N-1))
        z-= z%2
        out.append(int(z))
    return out
if __name__=='__main__':
    for s in sorted(SC):
        L=zs(s); print(s, len(set(L)), L)
