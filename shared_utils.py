# Copyright 2016 Adobe. All rights reserved.

"""
Module that contains shared functionality.
"""

from __future__ import print_function

import re
import os
import sys


FONTTOOLS_URL = 'https://github.com/fonttools/fonttools'
MIN_FT_VERSION = '3.0'

RE_VERSION_STRING = re.compile(r"^[0-9]+(\.[0-9]+)?")


def _verStr2Num(verStr):
    v = RE_VERSION_STRING.match(verStr)
    if v:
        return eval(v.group(0))
    return 0


try:
    from fontTools import version as ftversion
except ImportError:
    print("ERROR: FontTools Python module is not installed.\n"
          "Get the latest version at {}".format(FONTTOOLS_URL),
          file=sys.stderr)
    sys.exit(1)

minVersion = _verStr2Num(MIN_FT_VERSION)
curVersion = _verStr2Num(ftversion)

if curVersion < minVersion:
    print("ERROR: The FontTools module version must be {} or higher.\n"
          "You have version {} installed.\n"
          "Get the latest version at {}".format(
              MIN_FT_VERSION, ftversion, FONTTOOLS_URL),
          file=sys.stderr)
    sys.exit(1)


def readFile(filePath):
    f = open(filePath, "rt")
    data = f.read()
    f.close()
    return data


def writeFile(fileName, data):
    outfile = open(fileName, 'w')
    outfile.write(data)
    outfile.close()


def getFontFormat(fontFilePath):
    f = open(fontFilePath, "rb")
    head = f.read(4).decode()
    f.close()
    if head == "OTTO":
        return "OTF"
    elif head in ("\0\1\0\0", "true"):
        return "TTF"
    elif head == "wOFF":
        return "WOFF"
    elif head == "wOF2":
        return "WOFF2"
    return None


def validateFontPaths(pathsList):
    validatedPathsList = []
    for path in pathsList:
        path = os.path.realpath(path)
        if (os.path.isfile(path) and getFontFormat(path) in
           ['OTF', 'TTF', 'WOFF', 'WOFF2']):
            validatedPathsList.append(path)
        else:
            print("ERROR: %s is not a valid font file path." % path,
                  file=sys.stderr)
    return validatedPathsList
