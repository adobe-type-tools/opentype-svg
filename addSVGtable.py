#!/usr/bin/env python

from __future__ import print_function

__doc__ = """\
Adds an SVG table to a font, using SVG files provided.
The font format can be either OpenType or TrueType.

Usage:
  python addSVGtable.py [options] -s <folder_path> font

Options:
  -s  path to folder containing SVG files.
      (the file names MUST match the names of the
      glyphs they're meant to be associated with)
  -m  do not make a copy of the input font.
  -k  do not strip the 'viewBox' parameter.
  -w  generate WOFF and WOFF2 formats.
  -x  comma-separated list of glyph names to exclude.
  -z  compress the SVG table.
"""

# ---------------------------------------------------------------------------

import os
import sys
import re
import getopt
from shutil import copy2

from shared_utils import validateFontPaths, readFile

from fontTools import ttLib


def getGlyphNameFromFileName(filePath):
    fontFileName = os.path.split(filePath)[1]
    return os.path.splitext(fontFileName)[0]


reIDvalue = re.compile(r"<svg[^>]+?(id=\".*?\").+?>", re.DOTALL)


def setIDvalue(data, gid):
    id = reIDvalue.search(data)
    if id:
        newData = re.sub(id.group(1), 'id="glyph%s"' % gid, data)
    else:
        newData = re.sub('<svg', '<svg id="glyph%s"' % gid, data)
    return newData


# The value of the viewBox attribute is a list of four numbers min-x, min-y,
# width and height, separated by whitespace and/or a comma
reViewBox = re.compile(r"(<svg.+?)(\s*viewBox=[\"|\'](?:[-\d,. ]+)[\"|\'])(.+?>)", re.DOTALL)


def stripViewBox(svgItemData):
    """
    Removes the viewBox parameter from the <svg> element.
    """
    vb = reViewBox.search(svgItemData)
    if vb:
        svgItemData = reViewBox.sub(r"\g<1>\g<3>", svgItemData)
    return svgItemData


reXMLheader = re.compile(r"<\?xml .*\?>")
reEnableBkgrd = re.compile(r"( enable-background=[\"|\'][new\d, ]+[\"|\'])")
reWhiteSpaceBtween = re.compile(r">\s+<", re.MULTILINE)
reWhiteSpaceWithin = re.compile(r"\s+", re.MULTILINE)


def cleanupSVGdoc(svgItemData):
    # Remove XML header
    svgItemData = reXMLheader.sub('', svgItemData)

    # Remove all 'enable-background' parameters
    for enableBkgrd in reEnableBkgrd.findall(svgItemData):
        svgItemData = svgItemData.replace(enableBkgrd, '')

    # Remove all white space BETWEEN elements
    for whiteSpace in reWhiteSpaceBtween.findall(svgItemData):
        svgItemData = svgItemData.replace(whiteSpace, '><')

    # Replace all white space WITHIN elements with a single space
    for whiteSpace2 in reWhiteSpaceWithin.findall(svgItemData):
        svgItemData = svgItemData.replace(whiteSpace2, ' ')

    return svgItemData


reCopyCounter = re.compile("#\d+$")


def makeFontCopyPath(fontPath):
    dirName, fileName = os.path.split(fontPath)
    fileName, fileExt = os.path.splitext(fileName)
    fileName = reCopyCounter.split(fileName)[0]
    fontCopyPath = os.path.join(dirName, fileName + fileExt)
    n = 0
    while os.path.exists(fontCopyPath):
        newPath = fileName + "#" + repr(n) + fileExt
        fontCopyPath = os.path.join(dirName, newPath)
        n += 1
    return fontCopyPath


def processFont(fontPath, svgFilePathsList, options):
    font = ttLib.TTFont(fontPath)

    svgDocsDict = {}
    gNamesSeenAlreadyList = []

    svgGlyphsAdded = 0

    for svgFilePath in svgFilePathsList:
        gName = getGlyphNameFromFileName(svgFilePath)

        if gName in options.glyphNamesToExclude:
            continue

        try:
            gid = font.getGlyphID(gName)
        except KeyError:
            print("WARNING: Could not find a glyph named %s in the font %s" %
                  (gName, os.path.split(fontPath)[1]), file=sys.stderr)
            continue

        if gName in gNamesSeenAlreadyList:
            print("WARNING: Skipped a duplicate file named %s.svg at %s" %
                  (gName, svgFilePath), file=sys.stderr)
            continue
        else:
            gNamesSeenAlreadyList.append(gName)

        svgItemData = readFile(svgFilePath)

        # Set id value
        svgItemData = setIDvalue(svgItemData, gid)

        # Remove the viewBox parameter
        if options.stripViewBox:
            svgItemData = stripViewBox(svgItemData)

        # Clean-up SVG document
        svgItemData = cleanupSVGdoc(svgItemData)

        svgDocsDict[gid] = [svgItemData.strip(), gid, gid]
        svgGlyphsAdded += 1

    # Don't do any changes to the input font if there's no SVG data
    if not svgDocsDict:
        print("Could not find any SVG files that can be added to the font.",
              file=sys.stdout)
        sys.exit(0)

    svgDocsList = [svgDocsDict[index] for index in sorted(svgDocsDict.keys())]

    svgTable = ttLib.newTable('SVG ')
    svgTable.compressed = options.compressSVGs
    svgTable.docList = svgDocsList
    svgTable.colorPalettes = None
    font['SVG '] = svgTable

    # Make copy of the original font
    if options.makeFontCopy:
        fontCopyPath = makeFontCopyPath(fontPath)
        copy2(fontPath, fontCopyPath)

    font.save(fontPath)

    if options.generateWOFFs:
        # WOFF files are smaller if SVG table is uncompressed
        font['SVG '].compressed = False
        for ext in ['woff', 'woff2']:
            woffFontPath = os.path.splitext(fontPath)[0] + '.' + ext
            font.flavor = ext
            font.save(woffFontPath)

    font.close()

    print("%s SVG glyphs were successfully added to %s" %
          (svgGlyphsAdded, os.path.split(fontPath)[1]), file=sys.stdout)


reSVGelement = re.compile(r"<svg.+?>.+?</svg>", re.DOTALL)
reTEXTelement = re.compile(r"<text.+?>.+?</text>", re.DOTALL)


def validateSVGfiles(svgFilePathsList):
    """
    Light validation of SVG files.
      - checks that there is an <svg> element.
      - skips files that have a <text> element.
    """
    validatedPaths = []

    for filePath in svgFilePathsList:
        # Skip hidden files (filenames that start with period)
        fileName = os.path.basename(filePath)
        if fileName.startswith('.'):
            continue

        # Skip files that don't end with SVG extension
        if not fileName.lower().endswith('.svg'):
            continue

        assert os.path.isfile(filePath), "Not a valid file path: %s" % filePath
        data = readFile(filePath)

        # Find <svg> blob
        svg = reSVGelement.search(data)
        if not svg:
            print("WARNING: Could not find <svg> element in the file. "
                  "Skiping %s" % (filePath))
            continue

        # Warn about <text> elements
        text = reTEXTelement.search(data)
        if text:
            print("WARNING: Found <text> element in the file. "
                  "Skiping %s" % (filePath))
            continue

        validatedPaths.append(filePath)

    return validatedPaths


class Options(object):
    svgFolderPath = None
    makeFontCopy = True
    generateWOFFs = False
    compressSVGs = False
    glyphNamesToExclude = []
    stripViewBox = True

    def __init__(self, rawOptions):
        for option, value in rawOptions:
            if option == "-h":
                print(__doc__)
                sys.exit(0)
            elif option == "-m":
                self.makeFontCopy = False
            elif option == "-w":
                self.generateWOFFs = True
            elif option == "-z":
                self.compressSVGs = True
            elif option == "-k":
                self.stripViewBox = False
            elif option == "-x":
                if value:
                    self.glyphNamesToExclude.extend(value.split(','))
            elif option == "-s":
                if value:
                    path = os.path.realpath(value)
                    if os.path.isdir(path):
                        self.svgFolderPath = path
                    else:
                        print("ERROR: %s is not a valid folder path." % path,
                              file=sys.stderr)
                        sys.exit(1)


def parseOptions(args):
    try:
        rawOptions, files = getopt.getopt(args, "hkms:wx:z")
    except getopt.GetoptError as err:
        print("ERROR:", err, file=sys.stderr)
        sys.exit(2)

    return validateFontPaths(files), Options(rawOptions)


def main(args=None):
    fontPathsList, options = parseOptions(sys.argv[1:])

    if not len(fontPathsList):
        print("ERROR: No valid font file path was provided.", file=sys.stderr)
        return 1

    if not options.svgFolderPath:
        print("ERROR: Path to folder containing SVG files was not provided.",
              file=sys.stderr)
        return 1
    else:
        svgFilePathsList = []
        # Support nested folders
        for dirName, subdirList, fileList in os.walk(options.svgFolderPath):
            for file in fileList:
                svgFilePathsList.append(os.path.join(dirName, file))

    # Validate the SVGs
    svgFilePathsList = validateSVGfiles(svgFilePathsList)

    if not svgFilePathsList:
        print("No SVG files were found.", file=sys.stdout)
        return 1

    processFont(fontPathsList[0], svgFilePathsList, options)


if __name__ == "__main__":
    sys.exit(main())
