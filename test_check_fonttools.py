# Copyright 2018 Adobe. All rights reserved.

from __future__ import print_function, division, absolute_import

import sys
import unittest

from test_shared_utils import StringIO

have_fonttools = False
try:
    import fontTools  # pylint: disable=unused-import
    have_fonttools = True
except ImportError:
    pass


class CheckFonttoolsTest(unittest.TestCase):

    def test_check_fonttools(self):
        stream = sys.stderr = StringIO()
        with self.assertRaises(SystemExit) as cm:
            import check_fonttools  # pylint: disable=unused-variable

            if not have_fonttools:
                self.assertEqual(
                    stream.getvalue().strip(),
                    'ERROR: FontTools Python module is not installed.\n'
                    'Get the latest version at https://github.com/fonttools'
                    '/fonttools')
            else:
                self.assertEqual(
                    stream.getvalue().strip(),
                    'ERROR: The FontTools module version must be 3.0 or '
                    'higher.\nYou have version 2.5 installed.\nGet the latest '
                    'version at https://github.com/fonttools/fonttools')

        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    sys.exit(unittest.main())
