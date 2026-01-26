import unittest
from EVA.core.data_loading import load_data


class LoadComment(unittest.TestCase):
    """def test_something(self):
    #self.assertEqual(True, False)  # add assertion here
    print('hello')"""

    def test_loadcomment1(self):
        # print('loadcomment test')
        directory = "./test_data/"
        RunNum = "2630"
        rtnstr, flag = load_data.load_comment_brni(RunNum, directory)
        self.assertEqual(flag, 0, "did return flag")
        self.assertEqual(
            rtnstr,
            [
                "Start Time        :  Thu May 3 13:08:56 2018\n",
                "End   Time        :  Thu May 3 13:58:33 2018\n",
                "Number of Events  : 118466\n",
                "Comments : Mu- 40MeV/c Ti 40x40mm ISIS furnace sample holders\n",
            ],
            "didnt load commnet file",
        )

    def test_loadcomment2(self):
        # print('loadcomment2 test')
        directory = "./test_data/"
        RunNum = "999"
        rtnstr, flag = load_data.load_comment_brni(RunNum, directory)
        self.assertEqual(flag, 1, "did return flag")
        self.assertEqual(rtnstr, [" ", " ", " ", " "], "didnt load comment file")

    def test_loadcomment3(self):
        # print('loadcomment3 test')
        directory = "./"
        RunNum = "2631"
        rtnstr, flag = load_data.load_comment_brni(RunNum, directory)
        self.assertEqual(flag, 1, "did return flag")
        self.assertEqual(rtnstr, [" ", " ", " ", " "], "didnt load comment file")
