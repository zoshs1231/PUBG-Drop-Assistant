import unittest
from engine import Parameters, calculate, project_to_route

class EngineTests(unittest.TestCase):
    def test_straight_route(self):
        r = calculate((0, 4000), (8000, 4000), (4000, 4000))
        self.assertGreaterEqual(r['fraction'], 0)
        self.assertLessEqual(r['fraction'], 1)
        self.assertGreater(r['total_seconds'], 0)
    def test_project(self):
        self.assertAlmostEqual(project_to_route((0,0),(10,0),(5,4)),.5)
    def test_bad_speed(self):
        with self.assertRaises(ValueError):
            calculate((0,0),(10,0),(5,0),Parameters(0,35,38))

if __name__ == '__main__':
    unittest.main()
