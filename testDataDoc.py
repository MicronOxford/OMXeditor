import datadoc
import unittest


class TestDataDoc(unittest.TestCase):
    """
    Class for testing the Editor DataDoc and its methods.
    """

    def setUp(self):
        self.testFilePath = '/Users/graemeb/Documents/testData/OMX_SIM/' + \
                            'tetraspec_01_SIR_CRP_CRP.dv'
        self.dataDoc = datadoc.DataDoc(self.testFilePath)

    def test_bind(self):
        self.assertEqual(self.testFilePath, self.dataDoc.filePath)

if __name__ == '__main__':
    unittest.main()
