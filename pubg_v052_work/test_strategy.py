import unittest
from strategy import evaluate

class StrategyTests(unittest.TestCase):
    def test_near_route(self):
        r=evaluate((0,4000),(8000,4000),(4000,4400))
        self.assertAlmostEqual(r['nearest_distance_m'],400)
        self.assertTrue(r['candidates'])
    def test_no_600m_intersection(self):
        r=evaluate((0,4000),(8000,4000),(4000,5200))
        self.assertAlmostEqual(r['nearest_distance_m'],1200)
        self.assertTrue(all(c['target_distance_m']>=1200 for c in r['candidates']))
    def test_unreachable(self):
        r=evaluate((0,4000),(8000,4000),(4000,7900))
        self.assertIsNone(r['recommended'])
if __name__=='__main__': unittest.main()
