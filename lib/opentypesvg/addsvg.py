#!/usr/bin/env python

# Copyright 2016 Adobe. All rights reserved.

"""
Adds an SVG table to a font, using SVG files provided.
The font format can be either OpenType or TrueType.
"""

import argparse
import os
import re
import sys
from shutil import copy2

from fontTools import ttLib

from opentypesvg.__version__ import version as __version__
from opentypesvg.utils import (
    read_file,
    split_comma_sequence,
    validate_folder_path,
    validate_font_paths,
)


def getGlyphNameFromFileName(filePath):
    fontFileName = os.path.split(filePath)[1]
    return os.path.splitext(fontFileName)[0]


reIDvalue = re.compile(r"<svg[^>]+?(id=\".*?\").+?>", re.DOTALL)


def setIDvalue(data, gid):
    id_value = reIDvalue.search(data)
    if id_value:
        return re.sub(id_value.group(1), 'id="glyph{}"'.format(gid), data)
    return re.sub('<svg', '<svg id="glyph{}"'.format(gid), data)


# The value of the viewBox attribute is a list of four numbers min-x, min-y,
# width and height, separated by whitespace and/or a comma
reViewBox = re.compile(
    r"(<svg.+?)(\s*viewBox=[\"|\'](?:[-\d,. ]+)[\"|\'])(.+?>)", re.DOTALL)


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


reCopyCounter = re.compile(r"#\d+$")


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

        if gName in options.gnames_to_exclude:
            continue

        try:
            gid = font.getGlyphID(gName)
        except KeyError:
            print("WARNING: Could not find a glyph named {} in the font "
                  "{}".format(gName, os.path.split(fontPath)[1]),
                  file=sys.stderr)
            continue

        if gName in gNamesSeenAlreadyList:
            print("WARNING: Skipped a duplicate file named {}.svg at "
                  "{}".format(gName, svgFilePath), file=sys.stderr)
            continue
        else:
            gNamesSeenAlreadyList.append(gName)

        svgItemData = read_file(svgFilePath)

        # Set id value
        svgItemData = setIDvalue(svgItemData, gid)

        # Remove the viewBox parameter
        if options.strip_viewbox:
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
    svgTable.compressed = options.compress_svgs
    svgTable.docList = svgDocsList
    svgTable.colorPalettes = None
    font['SVG '] = svgTable

    # Make copy of the original font
    if options.make_font_copy:
        fontCopyPath = makeFontCopyPath(fontPath)
        copy2(fontPath, fontCopyPath)

    font.save(fontPath)

    if options.generate_woffs:
        # WOFF files are smaller if SVG table is uncompressed
        font['SVG '].compressed = False
        for ext in ['woff', 'woff2']:
            woffFontPath = os.path.splitext(fontPath)[0] + '.' + ext
            font.flavor = ext
            font.save(woffFontPath)

    font.close()

    plural = 's were' if svgGlyphsAdded != 1 else ' was'
    print("{} SVG glyph{} successfully added to {}".format(
        svgGlyphsAdded, plural, os.path.split(fontPath)[1]), file=sys.stdout)


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

        if not os.path.isfile(filePath):
            raise AssertionError("Not a valid file path: {}".format(filePath))
        data = read_file(filePath)

        # Find <svg> blob
        svg = reSVGelement.search(data)
        if not svg:
            print("WARNING: Could not find <svg> element in the file. "
                  "Skiping {}".format(filePath))
            continue

        # Warn about <text> elements
        text = reTEXTelement.search(data)
        if text:
            print("WARNING: Found <text> element in the file. "
                  "Skiping {}".format(filePath))
            continue

        validatedPaths.append(filePath)

    return validatedPaths


def get_options(args):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
        '--version',
        action='version',
        version=__version__
    )
    parser.add_argument(
        '-m',
        action='store_false',
        dest='make_font_copy',
        help='do not make a copy of the input font.'
    )
    parser.add_argument(
        '-k',
        action='store_false',
        dest='strip_viewbox',
        help="do not strip the 'viewBox' parameter."
    )
    parser.add_argument(
        '-w',
        action='store_true',
        dest='generate_woffs',
        help='generate WOFF and WOFF2 formats.'
    )
    parser.add_argument(
        '-x',
        metavar='GLYPH_NAMES',
        dest='gnames_to_exclude',
        type=split_comma_sequence,
        default=[],
        help='comma-separated sequence of glyph names to exclude.'
    )
    parser.add_argument(
        '-z',
        action='store_true',
        dest='compress_svgs',
        help='compress the SVG table.'
    )
    parser.add_argument(
        'svg_folder_path',
        metavar='FOLDER_PATH',
        type=validate_folder_path,
        help='path to folder containing SVG files.\n'
             'The file names MUST match the names of the\n'
             "glyphs they're meant to be associated with."
    )
    parser.add_argument(
        'input_path',
        metavar='FONT',
        help='OTF/TTF font file.',
    )
    options = parser.parse_args(args)

    options.font_paths_list = validate_font_paths([options.input_path])
    return options


def main(args=None):
    opts = get_options(args)

    if not opts.font_paths_list:
        return 1

    # Collect the paths to SVG files
    svgFilePathsList = []
    for dirName, _, fileList in os.walk(opts.svg_folder_path):
        # Support nested folders
        for file in fileList:
            svgFilePathsList.append(os.path.join(dirName, file))

    # Validate the SVGs
    svgFilePathsList = validateSVGfiles(svgFilePathsList)

    if not svgFilePathsList:
        print("No SVG files were found.", file=sys.stdout)
        return 1

    processFont(opts.font_paths_list[0], svgFilePathsList, opts)


if __name__ == "__main__":
    sys.exit(main())
