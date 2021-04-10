#!/usr/bin/env python

# Copyright 2016 Adobe. All rights reserved.

"""
Saves the contents of a font's SVG table as individual SVG files.
The font's format can be either OpenType, TrueType, WOFF, or WOFF2.
"""

import argparse
import os
import re
import sys

from fontTools import ttLib

from opentypesvg.__version__ import version as __version__
from opentypesvg.utils import (
    create_folder,
    create_nested_folder,
    final_message,
    get_gnames_to_save_in_nested_folder,
    get_output_folder_path,
    split_comma_sequence,
    validate_font_paths,
    write_file,
)


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
    if options.gnames_to_generate:
        glyphNamesList = sorted(options.gnames_to_generate)
    else:
        glyphNamesList = sorted(glyphOrder)

    # Confirm that there's something to process
    if not glyphNamesList:
        print("The fonts and options provided can't produce any SVG files.",
              file=sys.stdout)
        return

    # Define the list of glyph names to skip
    glyphNamesToSkipList = [".notdef"]
    if options.gnames_to_exclude:
        glyphNamesToSkipList.extend(options.gnames_to_exclude)

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

        if options.reset_viewbox:
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
                          startGID, gName), file=sys.stderr)

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
                folderPath = create_nested_folder(nestedFolderPath,
                                                  outputFolderPath)
            else:
                folderPath = outputFolderPath

            svgFilePath = os.path.join(folderPath, gName + '.svg')
            write_file(svgFilePath, svgItemData)
            filesSaved += 1
            startGID += 1

    font.close()
    final_message(filesSaved)


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
        '-o',
        metavar='FOLDER_PATH',
        dest='output_folder_path',
        help='path to folder for outputting the SVG files to.'
    )
    parser.add_argument(
        '-r',
        action='store_true',
        dest='reset_viewbox',
        help='reset viewBox values.'
    )
    parser.add_argument(
        '-g',
        metavar='GLYPH_NAMES',
        dest='gnames_to_generate',
        type=split_comma_sequence,
        default=[],
        help='comma-separated sequence of glyph names to make SVG files from.'
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
        'input_path',
        metavar='FONT',
        help='OTF/TTF/WOFF/WOFF2 font file.',
    )
    options = parser.parse_args(args)

    options.font_paths_list = validate_font_paths([options.input_path])
    return options


def main(args=None):
    opts = get_options(args)

    if not opts.font_paths_list:
        return 1

    first_font_path = opts.font_paths_list[0]

    output_folder_path = get_output_folder_path(opts.output_folder_path,
                                                first_font_path)

    processFont(first_font_path, output_folder_path, opts)


if __name__ == "__main__":
    sys.exit(main())
