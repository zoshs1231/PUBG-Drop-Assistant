"""Offline PUBG drop timing estimator. All coordinates are meters, origin NW."""
from dataclasses import dataclass
from math import hypot

MAP_SIZE_M = 8000.0

@dataclass
class Parameters:
    plane_speed_mps: float = 100.0
    descent_seconds: float = 35.0
    horizontal_speed_mps: float = 38.0
    # Simplified, configurable estimates, NOT verified PUBG physics.


def distance(a, b):
    return hypot(a[0] - b[0], a[1] - b[1])


def calculate(start, end, target, params=None, samples=1201):
    """Minimize total time from plane at start to estimated touchdown.

    The simple model treats post-exit movement as fixed descent time plus
    any extra horizontal travel beyond reachable distance. This is a
    planning approximation, not an in-game physics simulation.
    """
    p = params or Parameters()
    if p.plane_speed_mps <= 0 or p.horizontal_speed_mps <= 0 or p.descent_seconds < 0:
        raise ValueError('Speeds must be positive and descent time nonnegative')
    length = distance(start, end)
    if length < 1:
        raise ValueError('Plane route must have nonzero length')
    reach = p.descent_seconds * p.horizontal_speed_mps
    best = None
    for i in range(samples):
        t = i / (samples - 1)
        pos = (start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t)
        lateral = distance(pos, target)
        plane_time = t * length / p.plane_speed_mps
        flight_time = p.descent_seconds + max(0.0, lateral - reach) / p.horizontal_speed_mps
        total = plane_time + flight_time
        if best is None or total < best['total_seconds']:
            best = {'exit': pos, 'fraction': t, 'plane_seconds': plane_time,
                    'flight_seconds': flight_time, 'total_seconds': total,
                    'target_distance_m': lateral, 'reachable_m': reach}
    return best


def project_to_route(start, end, point):
    dx, dy = end[0] - start[0], end[1] - start[1]
    denom = dx * dx + dy * dy
    if denom == 0:
        return 0.0
    return max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / denom))
