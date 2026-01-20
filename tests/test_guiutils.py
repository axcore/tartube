import unittest

from tartube import guiutils


class FakePaned:

    def __init__(self):
        self.positions = []

    def set_position(self, posn):
        self.positions.append(posn)


class TestGuiUtils(unittest.TestCase):

    def test_nudge_paned_position_restores(self):
        paned = FakePaned()

        guiutils.nudge_paned_position(paned, 120)

        self.assertEqual(paned.positions, [121, 120])


if __name__ == '__main__':
    unittest.main()
