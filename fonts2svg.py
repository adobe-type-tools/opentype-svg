#!/usr/bin/env python

from __future__ import division, print_function

__doc__ = """\
Generates a set of SVG glyph files from one or more fonts and hex colors
for each of them. The fonts' format can be either OpenType or TrueType.

Usage:
  python fonts2svg.py -c RRGGBB[,RRGGBB...] font [font...]

Options:
  -c  comma-separated list of hex colors in RRGGBBAA format.
      (The alpha value 'AA' is optional)
  -o  path to folder for outputting the SVG files to.
  -g  comma-separated list of glyph names to make SVG files from.
  -a  comma-separated list of glyph names to add.
  -x  comma-separated list of glyph names to exclude.
  -u  do union (instead of intersection) of the fonts' glyph sets.
"""

# ---------------------------------------------------------------------------

import os
import sys
import re
import getopt

from shared_utils import validateFontPaths, writeFile

from fontTools import ttLib
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen


class SVGPen(BasePen):

    def __init__(self, glyphSet):
        BasePen.__init__(self, glyphSet)
        self.d = u''
        self._lastX = self._lastY = None

    def _moveTo(self, pt):
        ptx, pty = self._isInt(pt)
        self.d += u'M%s %s' % (ptx, pty)
        self._lastX, self._lastY = pt

    def _lineTo(self, pt):
        ptx, pty = self._isInt(pt)
        if (ptx, pty) == (self._lastX, self._lastY):
            return
        elif ptx == self._lastX:
            self.d += u'V%s' % (pty)
        elif pty == self._lastY:
            self.d += u'H%s' % (ptx)
        else:
            self.d += u'L%s %s' % (ptx, pty)
        self._lastX, self._lastY = pt

    def _curveToOne(self, pt1, pt2, pt3):
        pt1x, pt1y = self._isInt(pt1)
        pt2x, pt2y = self._isInt(pt2)
        pt3x, pt3y = self._isInt(pt3)
        self.d += u'C%s %s %s %s %s %s' % (pt1x, pt1y, pt2x, pt2y, pt3x, pt3y)
        self._lastX, self._lastY = pt3

    def _qCurveToOne(self, pt1, pt2):
        pt1x, pt1y = self._isInt(pt1)
        pt2x, pt2y = self._isInt(pt2)
        self.d += u'Q%s %s %s %s' % (pt1x, pt1y, pt2x, pt2y)
        self._lastX, self._lastY = pt2

    def _closePath(self):
        self.d += u'Z'
        self._lastX = self._lastY = None

    def _endPath(self):
        self._closePath()

    def _isInt(self, tup):
        return [int(flt) if (flt).is_integer() else flt for flt in tup]


def processFonts(fontPathsList, hexColorsList, outputFolderPath, options):
    glyphSetsList = []
    allGlyphNamesList = []

    # Load the fonts and collect their glyph sets
    for fontPath in fontPathsList:
        font = ttLib.TTFont(fontPath)
        gSet = font.getGlyphSet()
        glyphSetsList.append(gSet)
        allGlyphNamesList.append(gSet.keys())
        font.close()

    assert(len(glyphSetsList) > 0)

    # Define the list of glyph names to convert to SVG
    if options.glyphNamesToGenerate:
        glyphNamesList = sorted(options.glyphNamesToGenerate)
    else:
        if options.glyphsetsUnion:
            glyphNamesList = sorted(
                list(set.union(*map(set, allGlyphNamesList))))
        else:
            glyphNamesList = sorted(
                list(set.intersection(*map(set, allGlyphNamesList))))
            # Extend the list with additional glyph names
            if options.glyphNamesToAdd:
                glyphNamesList.extend(options.glyphNamesToAdd)
                # Remove any duplicates and sort
                glyphNamesList = sorted(list(set(glyphNamesList)))

    # Confirm that there's something to process
    if not glyphNamesList:
        print("The fonts and options provided can't produce any SVG files.",
              file=sys.stdout)
        return

    # Define the list of glyph names to skip
    glyphNamesToSkipList = [".notdef"]
    if options.glyphNamesToExclude:
        glyphNamesToSkipList.extend(options.glyphNamesToExclude)

    # On case-insensitive systems the SVG files cannot be all saved to the
    # same folder otherwise a.svg and A.svg would be written over each other,
    # for example. So, pre-process the list of glyph names to find which ones
    # step on each other, and save half of them in a nested folder. This
    # approach won't handle the case where a.svg and A.svg are NOT generated
    # on the same run, but that's fine; the user will have to handle that.
    # Also, the process below assumes that there are no more than 2 conflicts
    # per name, i.e. it will handle "the/The" but not "the/The/THE/...";
    # this shouldn't be a problem in 99% of the time.
    uniqueNamesSet = set()
    glyphNamesToSaveInNestedFolder = []
    for gName in glyphNamesList:
        if gName.lower() in uniqueNamesSet:
            glyphNamesToSaveInNestedFolder.append(gName)
        uniqueNamesSet.add(gName.lower())

    # Gather the fonts' UPM. For simplicity, it's assumed that all fonts have
    # the same UPM value. If fetching the UPM value fails, default to 1000.
    try:
        upm = ttLib.TTFont(fontPathsList[0])['head'].unitsPerEm
    except KeyError:
        upm = 1000

    nestedFolderPath = None
    filesSaved = 0

    # Generate the SVGs
    for gName in glyphNamesList:
        svgStr = (u"""<svg xmlns="http://www.w3.org/2000/svg" """
                  u"""viewBox="0 -%s %s %s">\n""" % (upm, upm, upm))

        for index, gSet in enumerate(glyphSetsList):
            # Skip glyphs that don't exist in the current font,
            # or that were requested to be skipped
            if gName not in gSet.keys() or gName in glyphNamesToSkipList:
                continue

            pen = SVGPen(gSet)
            tpen = TransformPen(pen, (1.0, 0.0, 0.0, -1.0, 0.0, 0.0))
            glyph = gSet[gName]
            glyph.draw(tpen)
            d = pen.d
            # Skip glyphs with no contours
            if not len(d):
                continue

            hex = hexColorsList[index]
            opc = ''
            if len(hex) != 6:
                opcHex = hex[6:]
                hex = hex[:6]
                if opcHex.lower() != 'ff':
                    opc = ' opacity="%.2f"' % (int(opcHex, 16) / 255)

            svgStr += u'\t<path%s fill="#%s" d="%s"/>\n' % (opc, hex, d)
        svgStr += u'</svg>'

        # Skip saving files that have no paths
        if '<path' not in svgStr:
            continue

        # Create the output folder.
        # This may be necessary if the folder was not provided. The folder
        # is made this late in the process because only now it's clear
        # that's needed.
        try:
            os.makedirs(outputFolderPath)
        except OSError:
            if not os.path.isdir(outputFolderPath):
                raise

        if gName in glyphNamesToSaveInNestedFolder:
            # Create the nested folder
            if not nestedFolderPath:
                nestedFolderPath = os.path.join(outputFolderPath, "_moreSVGs_")
                try:
                    os.makedirs(nestedFolderPath)
                except OSError:
                    if not os.path.isdir(nestedFolderPath):
                        raise
            folderPath = nestedFolderPath
        else:
            folderPath = outputFolderPath

        svgFilePath = os.path.join(folderPath, gName + '.svg')
        writeFile(svgFilePath, svgStr)
        filesSaved += 1

    if filesSaved == 0:
        filesSaved = 'No'
    print("%s SVG files saved." % filesSaved, file=sys.stdout)


reHexColor = re.compile(r"^(?=[a-fA-F0-9]*$)(?:.{6}|.{8})$")


class Options(object):
    colorsList = []
    outputFolderPath = None
    glyphsetsUnion = False
    glyphNamesToGenerate = None
    glyphNamesToAdd = None
    glyphNamesToExclude = None

    def __init__(self, rawOptions):
        for option, value in rawOptions:
            if option == "-h":
                print(__doc__)
                sys.exit(0)
            elif option == "-u":
                self.glyphsetsUnion = True
            elif option == "-c":
                if value:
                    self.validateRawColorsStr(value)
            elif option == "-g":
                if value:
                    self.glyphNamesToGenerate = value.split(',')
            elif option == "-a":
                if value:
                    self.glyphNamesToAdd = value.split(',')
            elif option == "-x":
                if value:
                    self.glyphNamesToExclude = value.split(',')
            elif option == "-o":
                if value:
                    path = os.path.realpath(value)
                    if os.path.isdir(path):
                        self.outputFolderPath = path
                    else:
                        print("ERROR: %s is not a valid folder path." % path,
                              file=sys.stderr)
                        sys.exit(1)

    def validateRawColorsStr(self, rawColorsStr):
        rawColorsList = rawColorsStr.split(',')
        for hex in rawColorsList:
            if reHexColor.match(hex):
                self.colorsList.append(hex)
            else:
                print("ERROR: %s is not a valid hex color." % hex,
                      file=sys.stderr)


def parseOptions(args):
    try:
        rawOptions, files = getopt.getopt(args, "a:c:g:ho:ux:")
    except getopt.GetoptError as err:
        print("ERROR:", err, file=sys.stderr)
        sys.exit(2)

    return validateFontPaths(files), Options(rawOptions)


def main(args=None):
    fontPathsList, options = parseOptions(sys.argv[1:])

    if not len(fontPathsList):
        print("ERROR: No valid font file paths were provided.",
              file=sys.stderr)
        return 1

    hexColorsList = options.colorsList

    # Confirm that the number of colors is the same as the fonts. If it's not,
    # extend the list of colors using SVG's default color (black), or trim the
    # list of colors.
    if len(hexColorsList) < len(fontPathsList):
        numAddCol = len(fontPathsList) - len(hexColorsList)
        hexColorsList.extend(['000000'] * numAddCol)
        print("WARNING: The list of colors was extended with %s #000000 "
              "value(s)." % numAddCol, file=sys.stderr)
    elif len(hexColorsList) > len(fontPathsList):
        numXtrCol = len(hexColorsList) - len(fontPathsList)
        print("WARNING: The list of colors got the last %s value(s) truncated:"
              " %s" % (numXtrCol, ' '.join(hexColorsList[-numXtrCol:])),
              file=sys.stderr)
        del hexColorsList[len(fontPathsList):]

    # If the path to the output folder was not provided, create a folder
    # named 'SVGs' in the same directory where the first font is.
    outputFolderPath = options.outputFolderPath
    if not outputFolderPath:
        outputFolderPath = os.path.join(os.path.dirname(fontPathsList[0]),
                                        "SVGs")

    processFonts(fontPathsList, hexColorsList, outputFolderPath, options)


if __name__ == "__main__":
    sys.exit(main())
