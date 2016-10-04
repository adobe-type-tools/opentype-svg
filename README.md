#Tools for making OpenType-SVG fonts

Dependencies:

- python 2.7 or higher
- [fontTools 3.0](https://github.com/fonttools/fonttools)

## How to make OpenType-SVG fonts?

### Step 1

![step1](imgs/step1.png "step 1")

Use `fonts2svg.py` to generate SVG files from a set of fonts and color values.

```sh
$ python fonts2svg.py -c 99ccff,ff0066,cc0066 fonts/Zebrawood-Shadow.otf fonts/Zebrawood-Fill.otf fonts/Zebrawood-Dots.otf
```

### Step 2

![step2](imgs/step2.png "step 2")

Use `addSVGtable.py` to add a set of SVG files to a font.

```sh
$ python addSVGtable.py -s fonts/SVGs fonts/Zebrawood.otf
```
