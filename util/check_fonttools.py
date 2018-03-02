# Copyright 2016 Adobe. All rights reserved.

"""
Snippet to check if fontTools is installed and
is at least a certain version.
"""

from __future__ import print_function

import sys
from distutils.version import LooseVersion


FONTTOOLS_URL = 'https://github.com/fonttools/fonttools'
MIN_FT_VERSION = '3.0'

try:
    from fontTools import version as ftversion
except ImportError:
    print("ERROR: FontTools Python module is not installed.\n"
          "Get the latest version at {}".format(FONTTOOLS_URL),
          file=sys.stderr)
    sys.exit(1)

if LooseVersion(ftversion) < LooseVersion(MIN_FT_VERSION):
    print("ERROR: The FontTools module version must be {} or higher.\n"
          "You have version {} installed.\n"
          "Get the latest version at {}".format(
              MIN_FT_VERSION, ftversion, FONTTOOLS_URL),
          file=sys.stderr)
    sys.exit(1)
