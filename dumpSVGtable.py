#!/usr/bin/env python

# Copyright 2016 Adobe. All rights reserved.

"""
Saves the contents of a font's SVG table as individual SVG files.
The font's format can be either OpenType, TrueType, WOFF, or WOFF2.

Usage:
  python dumpSVGtable.py [options] font

Options:
  -o  path to folder for outputting the SVG files to.
  -r  reset viewBox values.
  -g  comma-separated list of glyph names to make SVG files from.
  -x  comma-separated list of glyph names to exclude.
"""

from __future__ import division, print_function

__version__ = '1.0.0'

import getopt
import os
import re
import sys

from shared_utils import (write_file, final_message, get_output_folder_path,
                          validate_font_paths, split_comma_sequence,
                          create_folder, create_nested_folder,
                          get_gnames_to_save_in_nested_folder,)

from fontTools import ttLib


reViewBox = re.compile(r"viewBox=[\"|\']([\d, ])+?[\"|\']", re.DOTALL)


def resetViewBox(svgDoc):
    viewBox = reViewBox.search(svgDoc)
    if not viewBox:
        return svgDoc
    viewBoxPartsList = viewBox.group().split()
    viewBoxPartsList[1] = 0
    replacement = ' '.join(map(str, viewBoxPartsList))
    svgDocChanged = re.sub(viewBox.group(), replacement, svgDoc)
    return svgDocChanged


def processFont(fontPath, outputFolderPath, options):
    font = ttLib.TTFont(fontPath)
    glyphOrder = font.getGlyphOrder()
    svgTag = 'SVG '

    if svgTag not in font:
        print("ERROR: The font does not have the {} table.".format(
            svgTag.strip()), file=sys.stderr)
        sys.exit(1)

    svgTable = font[svgTag]

    if not len(svgTable.docList):
        print("ERROR: The {} table has no data that can be output.".format(
            svgTag.strip()), file=sys.stderr)
        sys.exit(1)

    # Define the list of glyph names to convert to SVG
    if options.glyphNamesToGenerate:
        glyphNamesList = sorted(options.glyphNamesToGenerate)
    else:
        glyphNamesList = sorted(glyphOrder)

    # Confirm that there's something to process
    if not glyphNamesList:
        print("The fonts and options provided can't produce any SVG files.",
              file=sys.stdout)
        return

    # Define the list of glyph names to skip
    glyphNamesToSkipList = [".notdef"]
    if options.glyphNamesToExclude:
        glyphNamesToSkipList.extend(options.glyphNamesToExclude)

    # Determine which glyph names need to be saved in a nested folder
    glyphNamesToSaveInNestedFolder = get_gnames_to_save_in_nested_folder(
        glyphNamesList)

    nestedFolderPath = None
    filesSaved = 0
    unnamedNum = 1

    # Write the SVG files by iterating over the entries in the SVG table.
    # The process assumes that each SVG document contains only one 'id' value,
    # i.e. the artwork for two or more glyphs is not included in a single SVG.
    for svgItemsList in svgTable.docList:
        svgItemData, startGID, endGID = svgItemsList

        if options.resetViewBox:
            svgItemData = resetViewBox(svgItemData)

        while(startGID != endGID + 1):
            try:
                gName = glyphOrder[startGID]
            except IndexError:
                gName = "_unnamed{}".format(unnamedNum)
                glyphNamesList.append(gName)
                unnamedNum += 1
                print("WARNING: The SVG table references a glyph ID (#{}) "
                      "which the font does not contain.\n"
                      "         The artwork will be saved as '{}.svg'.".format(
                          (startGID, gName)), file=sys.stderr)

            if gName not in glyphNamesList or gName in glyphNamesToSkipList:
                startGID += 1
                continue

            # Create the output folder.
            # This may be necessary if the folder was not provided.
            # The folder is made this late in the process because
            # only now it's clear that's needed.
            create_folder(outputFolderPath)

            # Create the nested folder, if there are conflicting glyph names.
            if gName in glyphNamesToSaveInNestedFolder:
                outputFolderPath = create_nested_folder(nestedFolderPath,
                                                        outputFolderPath)

            svgFilePath = os.path.join(outputFolderPath, gName + '.svg')
            write_file(svgFilePath, svgItemData)
            filesSaved += 1
            startGID += 1

    font.close()
    final_message(filesSaved)



class Options(object):
    outputFolderPath = None
    resetViewBox = False
    glyphNamesToGenerate = None
    glyphNamesToExclude = None

    def __init__(self, rawOptions):
        for option, value in rawOptions:
            if option == "-h":
                print(__doc__)
                sys.exit(0)
            elif option == "-r":
                self.resetViewBox = True
            elif option == "-g":
                if value:
                    self.glyphNamesToGenerate = value.split(',')
            elif option == "-x":
                if value:
                    self.glyphNamesToExclude = value.split(',')
            elif option == "-o":
                if value:
                    path = os.path.realpath(value)
                    if os.path.isdir(path):
                        self.outputFolderPath = path
                    else:
                        print("ERROR: {} is not a valid folder path.".format(
                            path), file=sys.stderr)
                        sys.exit(1)


def parseOptions(args):
    try:
        rawOptions, files = getopt.getopt(args, "g:ho:rx:")
    except getopt.GetoptError as err:
        print("ERROR:", err, file=sys.stderr)
        sys.exit(2)

    return validateFontPaths(files), Options(rawOptions)


def main(args=None):
    fontPathsList, options = parseOptions(sys.argv[1:])

    if not len(fontPathsList):
        print("ERROR: No valid font file path was provided.", file=sys.stderr)
        return 1

    # If the path to the output folder was not provided, create a folder
    # named 'SVGs' in the same directory where the first font is.
    outputFolderPath = options.outputFolderPath
    if not outputFolderPath:
        outputFolderPath = os.path.join(os.path.dirname(fontPathsList[0]),
                                        "SVGs")

    processFont(fontPathsList[0], outputFolderPath, options)


if __name__ == "__main__":
    sys.exit(main())
