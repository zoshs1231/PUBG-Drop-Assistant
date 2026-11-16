import unittest
from empirical import sample,recorded_summary,assess_route
class EmpiricalTests(unittest.TestCase):
 def test_endpoints(self):
  self.assertEqual(sample(0),(1499,0,29))
  self.assertEqual(sample(39),(49,1125,0))
 def test_interpolation(self):
  self.assertAlmostEqual(sample(0.5)[0],1493.5)
 def test_profile(self):
  self.assertEqual(recorded_summary()['horizontal_path_m'],1125)
 def test_out_of_range(self):
  with self.assertRaises(ValueError):sample(40)
 def test_no_600_intersection(self):
  r=assess_route((0,0),(8000,0),(4000,700),preferred_m=600)
  self.assertGreaterEqual(r['nearest_distance_m'],699)
  self.assertNotEqual(r['recommended']['distance_m'],600)
 def test_no_fabricated_eta(self):
  r=assess_route((0,0),(8000,0),(4000,500))
  self.assertIsNone(r['recommended']['estimated_landing_s'])
 def test_far_target(self):
  r=assess_route((0,0),(8000,0),(4000,2500))
  self.assertTrue(r['recommended']['fallback'])
if __name__=='__main__':unittest.main()
