#!/usr/bin/env python

from __future__ import print_function

__doc__="""\
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

#-----------------------------------------------------------------------------------------

import os
import sys
import re
import getopt

fontToolsURL = 'https://github.com/fonttools/fonttools'

try:
	from fontTools import ttLib
	from fontTools import version as ftversion
except ImportError:
	print("ERROR: FontTools Python module is not installed.\n\
       Get the latest version at %s" % fontToolsURL, file=sys.stderr)
	sys.exit(1)

reVerStr = re.compile(r"^[0-9]+(\.[0-9]+)?")
def verStr2Num(verStr):
	v = reVerStr.match(verStr)
	if v:
		return eval(v.group(0))
	return 0

minFTversion = '3.0'
minVersion = verStr2Num(minFTversion)
curVersion = verStr2Num(ftversion)

if curVersion < minVersion:
	print("ERROR: The FontTools module version must be %s or higher.\n\
       You have version %s installed.\n\
       Get the latest version at %s" % (minFTversion, ftversion, fontToolsURL),
	file=sys.stderr)
	sys.exit(1)


def writeFile(fileName, data):
	outfile = open(fileName, 'w')
	outfile.write(data)
	outfile.close()


reViewBox = re.compile(r"viewBox=[\"|\']([\d, ])+?[\"|\']", re.DOTALL)

def resetViewBox(svgDoc):
	viewBox = reViewBox.search(svgDoc)
	if not viewBox:
		return svgDoc
	viewBoxPartsList = viewBox.group().split()
	viewBoxPartsList[1] = 0
	svgDocChanged = re.sub(viewBox.group(), ' '.join(map(str, viewBoxPartsList)), svgDoc)
	return svgDocChanged


def processFont(fontPath, outputFolderPath, options):
	font = ttLib.TTFont(fontPath)
	glyphOrder = font.getGlyphOrder()
	svgTag = 'SVG '

	if svgTag not in font:
		print("ERROR: The font does not have the %s table." % svgTag.strip(), file=sys.stderr)
		sys.exit(1)

	svgTable = font[svgTag]

	if not len(svgTable.docList):
		print("ERROR: The %s table has no data that can be output." % svgTag.strip(), file=sys.stderr)
		sys.exit(1)

	# Define the list of glyph names to convert to SVG
	if options.glyphNamesToGenerate:
		glyphNamesList = sorted(options.glyphNamesToGenerate)
	else:
		glyphNamesList = sorted(glyphOrder)

	# Confirm that there's something to process
	if not glyphNamesList:
		print("The fonts and options provided can't produce any SVG files.", file=sys.stdout)
		return

	# Define the list of glyph names to skip
	glyphNamesToSkipList = [".notdef"]
	if options.glyphNamesToExclude:
		glyphNamesToSkipList.extend(options.glyphNamesToExclude)

	# On case-insensitive systems the SVG files cannot be all saved to the same folder
	# otherwise a.svg and A.svg would be written over each other, for example. So,
	# pre-process the list of glyph names to find which ones step on each other, and
	# save half of them in a nested folder. This approach won't handle the case where
	# a.svg and A.svg are NOT generated on the same run, but that's fine; the user will
	# have to handle that. Also, the process below assumes that there are no more
	# than 2 conflicts per name, i.e. it will handle "the/The" but not "the/The/THE/...";
	# this shouldn't be a problem in 99% of the time.
	uniqueNamesSet = set()
	glyphNamesToSaveInNestedFolder = []
	for gName in glyphNamesList:
		if gName.lower() in uniqueNamesSet:
			glyphNamesToSaveInNestedFolder.append(gName)
		uniqueNamesSet.add(gName.lower())

	nestedFolderPath = None
	filesSaved = 0
	unnamedNum = 1

	# Write the SVG files by iterating over the entries in the SVG table.
	# The process assumes that each SVG document contains only one 'id' value, i.e. the
	# artwork for two or more glyphs is not included in a single SVG.
	for svgItemsList in svgTable.docList:
		svgItemData, startGID, endGID = svgItemsList

		if options.resetViewBox:
			svgItemData = resetViewBox(svgItemData)

		while(startGID != endGID + 1):
			try:
				gName = glyphOrder[startGID]
			except IndexError:
				gName = "_unnamed%s" % unnamedNum
				glyphNamesList.append(gName)
				unnamedNum += 1
				print("WARNING: The SVG table references a glyph ID (#%s) which the " \
				      "font does not contain.\n" \
				      "         The artwork will be saved as '%s.svg'." % \
				                                       (startGID, gName), file=sys.stderr)

			if gName not in glyphNamesList or gName in glyphNamesToSkipList:
				startGID += 1
				continue

			# Create the output folder (this may be necessary if the folder was not provided)
			# (The folder is made this late in the process because only now it's clear that's needed)
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
			writeFile(svgFilePath, svgItemData)
			filesSaved += 1
			startGID += 1

	font.close()

	if filesSaved == 0:
		filesSaved = 'No'
	print("%s SVG files saved." % filesSaved, file=sys.stdout)


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
		if os.path.isfile(path) and getFontFormat(path) in ['OTF','TTF', 'WOFF', 'WOFF2']:
			validatedPathsList.append(path)
		else:
			print("ERROR: %s is not a valid font file path." % path, file=sys.stderr)
	return validatedPathsList


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
						print("ERROR: %s is not a valid folder path." % path, file=sys.stderr)
						sys.exit(1)


def parseOptions(args):
	try:
		rawOptions, files = getopt.getopt(args, "g:ho:rx:")
	except getopt.GetoptError as err:
		print("ERROR:", err, file=sys.stderr)
		sys.exit(2)

	return validateFontPaths(files), Options(rawOptions)


def run():
	fontPathsList, options = parseOptions(sys.argv[1:])

	if not len(fontPathsList):
		print("ERROR: No valid font file path was provided.", file=sys.stderr)
		sys.exit(1)

	# If the path to the output folder was not provided, create a folder
	# named 'SVGs' in the same directory where the first font is.
	outputFolderPath = options.outputFolderPath
	if not outputFolderPath:
		outputFolderPath = os.path.join(os.path.dirname(fontPathsList[0]), "SVGs")

	processFont(fontPathsList[0], outputFolderPath, options)


if __name__ == "__main__":
	if len(sys.argv) == 1:
		print(__doc__)
	else:
		run()
