import unittest
from maps import MAPS,PROFILES
from guidance import make_guidance
from empirical import assess_route
class V04Tests(unittest.TestCase):
 def test_maps(self):
  self.assertEqual(MAPS['Sanhok'],4000)
  self.assertEqual(MAPS['Karakin'],2000)
  self.assertEqual(len(MAPS),10)
 def test_guidance(self):
  self.assertIn('Shift',make_guidance('Erangel',700,49))
  self.assertIn('실측 고도·속도 궤적 없음',make_guidance('Miramar',700,49))
 def test_preferred_custom(self):
  r=assess_route((0,0),(4000,0),(1500,500),preferred_m=1100)
  self.assertAlmostEqual(r['recommended']['distance_m'],1100)
if __name__=='__main__':unittest.main()
