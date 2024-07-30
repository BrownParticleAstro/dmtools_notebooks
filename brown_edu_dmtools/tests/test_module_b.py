import unittest
from package_b.module_b import add_two 

class TestAddTwo(unittest.TestCase):
  	def test_add_two(self):
  		  self.assertEqual(add_two(1), 3)

unittest.main()
