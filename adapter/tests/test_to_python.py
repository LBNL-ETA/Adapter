import unittest
from adapter.to_python import Excel, Db

import logging
logging.basicConfig(level=logging.DEBUG)

class ExcelTests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        """
        """
        
