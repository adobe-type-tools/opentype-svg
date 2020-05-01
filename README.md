[![Codecov Badge](https://codecov.io/gh/adobe-type-tools/opentype-svg/branch/master/graph/badge.svg)](https://codecov.io/gh/adobe-type-tools/opentype-svg)

# Tools for making OpenType-SVG fonts

- `addsvg`
	adds an SVG table to a font, using SVG files provided. The font's format can be either OpenType or TrueType.

- `dumpsvg`
	saves the contents of a font's SVG table as individual SVG files. The font's format can be either OpenType, TrueType, WOFF, or WOFF2.

- `fonts2svg`
	generates a set of SVG glyph files from one or more fonts and hex colors for each of them. The fonts' format can be either OpenType, TrueType, WOFF, or WOFF2.


### Dependencies

- Python 3.6 or higher

- [FontTools](https://github.com/fonttools/fonttools) 3.1.0 or higher


### Installation instructions

- Make sure you have Python 3.6 (or higher) installed.

- Clone this repository.

- `cd` into the repository folder.

- Setup a virtual environment:

		$ python3 -m venv venv

- Activate the environment:

		$ source venv/bin/activate

- Update `pip`:

		$ pip install -U pip

- Install `opentypesvg`:

		$ pip install .


# How to make OpenType-SVG fonts?

### Step 1
#### Generate a set of SVG files from a series of fonts and color values.

![step1](imgs/step1.png "step 1")

	fonts2svg -c 99ccff,ff0066,cc0066 fonts/Zebrawood-Shadow.otf fonts/Zebrawood-Fill.otf fonts/Zebrawood-Dots.otf

### Step 2
#### Add a set of SVG files to an existing OpenType (or TrueType) font.

![step2](imgs/step2.png "step 2")

	addsvg -s fonts/SVGs fonts/Zebrawood.otf

You can use **Step 2** without doing **Step 1**, but there are a few things you need to be aware of when using the `addsvg` tool:

* After the SVG files are saved with the authoring application (e.g. Adobe Illustrator, CorelDRAW!, Inkscape) they should be put thru a process that optimizes and cleans up the SVG code; this will slim down the file size while keeping the resulting artwork the same. For this step you can use one of these tools:
	* [SVG Cleaner](https://github.com/RazrFalcon/svgcleaner-gui/releases) (GUI version)
	* [SVG Cleaner](https://github.com/RazrFalcon/svgcleaner) (command line version)
	* [SVG Optimizer](https://github.com/svg/svgo)
	* [Scour](https://github.com/scour-project/scour)

* The tool requires the SVG files to be named according to the glyphs which they are meant to be associated with. For example, if the glyph in the font is named **ampersand**, the SVG file needs to be named `ampersand.svg`.

* The tool expects the color artwork to have been designed at the same size as the glyphs in the font, usually 1000 or 2048 UPM. This means 1 point (pt) in the authoring app equals 1 unit in font coordinates.
