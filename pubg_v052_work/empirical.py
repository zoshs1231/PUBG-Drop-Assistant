"""Single recorded Erangel drop. Observations, not universal PUBG physics."""
from dataclasses import dataclass
from math import hypot, sqrt

# Seconds since jump, absolute HUD altitude (m), cumulative horizontal path (m), HUD speed (km/h).
# Selected rows transcribed from the user's screenshot; intermediate values are interpolated.
OBSERVATIONS = [
 (0,1499,0,29),(1,1488,0,107),(2,1442,30,170),(3,1388,75,177),
 (4,1345,100,174),(5,1280,155,170),(6,1254,180,169),(7,1177,250,168),
 (8,1125,300,166),(11,1023,400,166),(13,919,500,165),(15,816,600,165),
 (17,714,700,165),(20,611,800,165),(22,484,930,165),
 (23,457,960,171),(24,398,980,217),(25,290,995,232),
 (26,268,995,218),(27,237,995,169),(28,178,1000,36),
 (29,173,1010,30),(30,167,1020,39),(31,161,1025,42),
 (32,147,1035,48),(33,132,1055,49),(34,124,1065,50),
 (35,101,1085,52),(36,85,1095,53),(37,76,1100,53),
 (38,60,1110,55),(39,49,1125,0),
]
SHIFT_START_S = 23
PARACHUTE_START_S = 26

def sample(t):
    if not 0 <= t <= OBSERVATIONS[-1][0]:
        raise ValueError('실측 시간 범위를 벗어났습니다 (0~39초).')
    for a,b in zip(OBSERVATIONS,OBSERVATIONS[1:]):
        if a[0] <= t <= b[0]:
            f=(t-a[0])/(b[0]-a[0])
            return tuple(a[i]+f*(b[i]-a[i]) for i in range(1,4))
    return OBSERVATIONS[-1][1:]

def recorded_summary():
    return {'duration_s':39,'start_altitude_m':1499,'land_altitude_m':49,
            'horizontal_path_m':1125,'shift_start_s':SHIFT_START_S,
            'parachute_start_s':PARACHUTE_START_S,'max_recorded_hud_speed_kmh':232}

def assess_route(start,end,target,plane_speed_mps=100,preferred_m=750,terrain_altitude_m=49):
    """Select a geometrically feasible community-distance exit; DO NOT claim optimality.

    Compare 600/750/900 m distance targets where route intersects circles.
    Prefer earliest crossing of preferred distance (plane wait), then other circles.
    A recorded 1125 m path is shown as context, not a guaranteed range.
    """
    if plane_speed_mps<=0: raise ValueError('비행기 속도는 양수여야 합니다.')
    if not 0<=terrain_altitude_m<1499: raise ValueError('착륙 지형 절대 고도는 0~1498m로 입력하세요.')
    vx,vy=end[0]-start[0],end[1]-start[1]
    length=hypot(vx,vy)
    if length<1: raise ValueError('비행 경로가 너무 짧습니다.')
    u=((target[0]-start[0])*vx+(target[1]-start[1])*vy)/length**2
    nearest_u=max(0,min(1,u))
    nearest_pos=(start[0]+nearest_u*vx,start[1]+nearest_u*vy)
    nearest=hypot(nearest_pos[0]-target[0],nearest_pos[1]-target[1])
    choices=[]
    for radius in sorted(set((600.,750.,900.,1125.,float(preferred_m)))):
        closest_infinite=(start[0]+u*vx,start[1]+u*vy)
        d2=(closest_infinite[0]-target[0])**2+(closest_infinite[1]-target[1])**2
        if d2>radius**2+1e-8: continue
        offset=sqrt(max(0,radius**2-d2))/length
        for f in (u-offset,u+offset):
            if 0<=f<=1:
                choices.append({'distance_m':radius,'fraction':f,'exit':(start[0]+f*vx,start[1]+f*vy),
                                'plane_wait_s':f*length/plane_speed_mps})
    # User-selected distance first, then nearest alternative, earlier crossing.
    choices.sort(key=lambda x:(abs(x['distance_m']-preferred_m),x['plane_wait_s']))
    chosen=choices[0] if choices else None
    if chosen is None:
        # no preset-circle crossing: nearest point only; mark it as geometric fallback
        chosen={'distance_m':nearest,'fraction':nearest_u,'exit':nearest_pos,
                'plane_wait_s':nearest_u*length/plane_speed_mps,'fallback':True}
    else:
        chosen['fallback']=False
    chosen['empirical_reference_m']=1125
    chosen['empirical_reference_s']=39
    chosen['terrain_matches_recording']=abs(terrain_altitude_m-49)<1e-6
    chosen['estimated_landing_s']=None  # No validated cross-strategy model exists.
    chosen['validated_optimal']=False
    return {'nearest_distance_m':nearest,'recommended':chosen,'candidates':choices,
            'warning':'기하학적 이탈 후보입니다. 39초/1125m 실측은 단일 궤적이며 이 위치의 착륙시간 또는 최적성을 보장하지 않습니다.'}
