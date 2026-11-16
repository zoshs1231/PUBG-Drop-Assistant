"""Instructional drop phases; do not mistake these for physics-derived optimal controls."""
from empirical import OBSERVATIONS, SHIFT_START_S, PARACHUTE_START_S
from maps import PROFILES

def make_guidance(map_name, exit_distance_m, terrain_altitude_m, start_altitude_m=1499):
    if exit_distance_m < 0: raise ValueError('distance must be nonnegative')
    if terrain_altitude_m >= start_altitude_m: raise ValueError('착륙 지형 고도가 이탈 고도 이상입니다.')
    profile=PROFILES[map_name]
    switch=profile['switch']
    lines=[f'지도: {map_name} / 이탈→목표: {exit_distance_m:.0f}m',
           f'참고 전략: {profile["source"]}',
           '※ 속도는 HUD 목표값(수평 속도 아님); 실측 최적 제어값이 아닙니다.']
    if exit_distance_m <= 900:
        lines += [f'① 이탈 직후: 목표 방향으로 접근, HUD 약 {profile["speed"]}km/h (커뮤니티 참고)',
                  f'② 목표까지 수평 약 {switch}m: Shift 급강하 전환 후보',
                  '③ 낙하산 전개 후: Shift로 빠른 하강, 목표를 지나칠 때 Ctrl 활공']
    else:
        lines += ['① 장거리: 수평 이동을 우선하며 접근 (정확한 목표 속도 미검증)',
                  '② 낙하산 전개 후: Ctrl 활공으로 목표까지 도달 가능성 확인',
                  '③ 충분히 가까워지면 Shift 하강; 최적 전환 고도는 미측정']
    if map_name=='Erangel':
        lines += ['[에란겔 1회 실측 궤적: 동일 조작·지형일 때만 참고]',
                  '0~22초: HUD 고도 1499→484m / 수평 0→930m / HUD 속도 대체로 165~177km/h',
                  '23~25초: Shift 급강하 / HUD 고도 457→290m / 최대 232km/h',
                  '26~39초: 낙하산 전개 이후 / HUD 고도 268→49m / 수평 995→1125m']
    else:
        lines.append('해당 지도 실측 고도·속도 궤적 없음. 에란겔 39초 기록을 전용 공식으로 사용하지 않음.')
    if abs(terrain_altitude_m-49)>1:
        lines.append('목표 지면 고도가 에란겔 실측 착륙 고도(49m)와 다름: 절대 고도 전환값 산출 불가.')
    lines.append('주의: 400m 고도에서 무조건 급강하 같은 규칙은 현재 데이터로 검증되지 않음.')
    return '\n'.join(lines)
