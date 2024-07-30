import unittest
from package_a.module_a import add_one 

class TestAddOne(unittest.TestCase):

	def test_add_one(self):
		self.assertEqual(add_one(1), 2)

unittest.main()

