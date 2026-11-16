"""Offline community-route heuristic comparison; NOT calibrated PUBG physics."""
from dataclasses import dataclass
from math import hypot, sqrt

@dataclass(frozen=True)
class Strategy:
    name: str
    nominal_m: float
    dive_m: float
    approach_kmh: float
    glide_kmh: float
    base_fall_s: float
    max_range_m: float

# Community examples are hypotheses, not validated fastest timings.
STRATEGIES = (
    Strategy('600m / 200km/h',600,125,200,55,32,1300),
    Strategy('750m / 205km/h',750,175,205,55,33,1450),
    Strategy('900m / 185km/h curved',900,175,185,55,35,1600),
    Strategy('Long glide (experimental)',1600,250,126,27,43,2800),
)

def _distance(a,b): return hypot(a[0]-b[0],a[1]-b[1])

def _position(a,b,f): return (a[0]+f*(b[0]-a[0]), a[1]+f*(b[1]-a[1]))

def _intersections(a,b,target,r):
    vx,vy=b[0]-a[0],b[1]-a[1]
    length2=vx*vx+vy*vy
    if length2==0: raise ValueError('비행 경로 길이가 0입니다.')
    u=((target[0]-a[0])*vx+(target[1]-a[1])*vy)/length2
    closest=_position(a,b,u)
    delta=r*r-_distance(closest,target)**2
    if delta<0: return []
    offset=sqrt(max(0,delta)/length2)
    return [v for v in (u-offset,u+offset) if 0<=v<=1]

def evaluate(start,end,target,plane_speed_mps=100.0,samples=1001):
    """Rank candidate exit points by an explicitly uncalibrated proxy.

    Flight-time proxy is NOT a physical prediction. The nominal approach
    speed is only a label/reference; it is not treated as horizontal velocity.
    """
    if plane_speed_mps<=0: raise ValueError('비행기 속도는 양수여야 합니다.')
    length=_distance(start,end)
    if length<1: raise ValueError('비행 경로 길이가 너무 짧습니다.')
    vx,vy=end[0]-start[0],end[1]-start[1]
    projection=max(0,min(1,((target[0]-start[0])*vx+(target[1]-start[1])*vy)/(length*length)))
    nearest=_distance(_position(start,end,projection),target)
    results=[]
    for s in STRATEGIES:
        exact=_intersections(start,end,target,s.nominal_m)
        # Search full route as well: optimal exit need not be nearest point.
        candidates=sorted(set([i/(samples-1) for i in range(samples)] + exact))
        best=None
        for f in candidates:
            exit_pos=_position(start,end,f)
            d=_distance(exit_pos,target)
            if d>s.max_range_m: continue
            wait=f*length/plane_speed_mps
            # Deliberately heuristic: penalize distance deviations, extra glide,
            # and waiting; actual landing-time calibration is future work.
            approach_extra=max(0,d-s.nominal_m)
            shortfall=max(0,s.nominal_m-d)
            flight=s.base_fall_s+approach_extra/(s.glide_kmh/3.6)+shortfall/(s.approach_kmh/3.6)*0.18
            total=wait+flight
            if best is None or total<best['score_seconds']:
                best=dict(strategy=s.name,exit=exit_pos,fraction=f,
                    target_distance_m=d,plane_seconds=wait,
                    proxy_flight_seconds=flight,score_seconds=total,
                    dive_transition_m=s.dive_m,nominal_exit_m=s.nominal_m,
                    approximate=True)
        if best: results.append(best)
    results.sort(key=lambda r:r['score_seconds'])
    return {'nearest_distance_m':nearest,'candidates':results,
            'recommended':results[0] if results else None,
            'warning':'점수는 검증되지 않은 휴리스틱입니다. 실제 착륙시간이나 최적 경로를 의미하지 않습니다.'}
