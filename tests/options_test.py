# Copyright 2018 Adobe. All rights reserved.

import os
import sys
import unittest

from opentypesvg import addsvg, dumpsvg, fonts2svg

have_brotli = False
try:
    import brotli  # noqa

    have_brotli = True
except ImportError:
    pass

# addsvg must be last because of the way some tests prepare the input
ALL_TOOLS = (dumpsvg, fonts2svg, addsvg)
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
# addsvg requires a path to a folder in addition to the path to the font
XTRA_ARG = os.path.join(ROOT_DIR, 'fonts')


class OptionsTest(unittest.TestCase):

    def setUp(self):
        self.font_path = os.path.join(ROOT_DIR, 'fonts', 'Zebrawood.otf')

    # -----
    # Tests
    # -----

    def test_get_options_no_args(self):
        for tool in ALL_TOOLS:
            with self.assertRaises(SystemExit) as cm:
                tool.get_options([])
            self.assertEqual(cm.exception.code, 2)

    def test_get_options_help(self):
        for tool in ALL_TOOLS:
            with self.assertRaises(SystemExit) as cm:
                tool.get_options(['-h'])
            self.assertEqual(cm.exception.code, 0)

    def test_get_options_version(self):
        for tool in ALL_TOOLS:
            with self.assertRaises(SystemExit) as cm:
                tool.get_options(['--version'])
            self.assertEqual(cm.exception.code, 0)

    def test_get_options_bogus_option(self):
        args = ['--bogus', 'xfont']
        for tool in ALL_TOOLS:
            if tool is addsvg:
                args.insert(len(args) - 1, XTRA_ARG)  # insert the folder path
            with self.assertRaises(SystemExit) as cm:
                tool.get_options(args)
            self.assertEqual(cm.exception.code, 2)

    def test_get_options_invalid_font_path(self):
        args = ['xfont']
        for tool in ALL_TOOLS:
            if tool is addsvg:
                args.insert(len(args) - 1, XTRA_ARG)  # insert the folder path
            opts = tool.get_options(args)
            self.assertEqual(opts.font_paths_list, [])

    def test_get_options_not_a_font_path(self):
        args = [os.path.join('fonts', 'test.html')]
        for tool in ALL_TOOLS:
            if tool is addsvg:
                args.insert(len(args) - 1, XTRA_ARG)  # insert the folder path
            opts = tool.get_options(args)
            self.assertEqual(opts.font_paths_list, [])

    def test_get_options_good_font_path(self):
        args = [self.font_path]
        for tool in ALL_TOOLS:
            if tool is addsvg:
                args.insert(len(args) - 1, XTRA_ARG)  # insert the folder path
            opts = tool.get_options(args)
            self.assertEqual(os.path.basename(opts.font_paths_list[0]),
                             os.path.basename(self.font_path))

    def test_get_options_addsvg_invalid_folder_path(self):
        with self.assertRaises(SystemExit) as cm:
            addsvg.get_options(['-s', 'xfolder', 'xfont'])
        self.assertEqual(cm.exception.code, 1)

    @unittest.skipIf(have_brotli, "brotli module is installed")
    def test_get_options_addsvg_brotli_missing(self):
        with self.assertRaises(SystemExit) as cm:
            addsvg.get_options([XTRA_ARG, '-w', self.font_path])
        self.assertEqual(cm.exception.code, 1)

    @unittest.skipIf(not have_brotli, "brotli module is not installed")
    def test_get_options_addsvg_store_true_opts(self):
        args = [XTRA_ARG, '-w', '-z', self.font_path]
        opts = addsvg.get_options(args)
        attr = ('make_font_copy', 'strip_viewbox',
                'generate_woffs', 'compress_svgs')
        result = list(set([getattr(opts, name) for name in attr]))[0]
        self.assertTrue(result)

    def test_get_options_addsvg_store_false_opts(self):
        args = [XTRA_ARG, '-m', '-k', self.font_path]
        opts = addsvg.get_options(args)
        attr = ('make_font_copy', 'strip_viewbox',
                'generate_woffs', 'compress_svgs')
        result = list(set([getattr(opts, name) for name in attr]))[0]
        self.assertFalse(result)

    def test_get_options_dumpsvg_store_true_opts(self):
        args = ['-r', self.font_path]
        opts = dumpsvg.get_options(args)
        result = getattr(opts, 'reset_viewbox')
        self.assertTrue(result)

    def test_get_options_fonts2svg_store_true_opts(self):
        args = ['-u', self.font_path]
        opts = fonts2svg.get_options(args)
        result = getattr(opts, 'glyphsets_union')
        self.assertTrue(result)

    def test_get_options_addsvg_opts_defaults(self):
        dflt = {'make_font_copy': True,
                'strip_viewbox': True,
                'generate_woffs': False,
                'gnames_to_exclude': [],
                'compress_svgs': False}
        args = [XTRA_ARG, self.font_path]
        opts = addsvg.get_options(args)
        for key, val in dflt.items():
            self.assertEqual(getattr(opts, key), val)

    def test_get_options_dumpsvg_opts_defaults(self):
        dflt = {'output_folder_path': None,
                'reset_viewbox': False,
                'gnames_to_generate': [],
                'gnames_to_exclude': []}
        args = [self.font_path]
        opts = dumpsvg.get_options(args)
        for key, val in dflt.items():
            self.assertEqual(getattr(opts, key), val)

    def test_get_options_fonts2svg_opts_defaults(self):
        dflt = {'colors_list': [],
                'output_folder_path': None,
                'gnames_to_generate': [],
                'gnames_to_add': [],
                'gnames_to_exclude': [],
                'glyphsets_union': False}
        args = [self.font_path]
        opts = fonts2svg.get_options(args)
        for key, val in dflt.items():
            self.assertEqual(getattr(opts, key), val)

    def test_get_options_fonts2svg_invalid_hex_color(self):
        invalid_hex_colors = ['xxx', 'xxxxxx', 'aaa', 'aaaxxx']
        for hex_col in invalid_hex_colors:
            with self.assertRaises(SystemExit) as cm:
                fonts2svg.get_options(['-c', hex_col, self.font_path])
            self.assertEqual(cm.exception.code, 2)

    def test_get_options_fonts2svg_valid_hex_color(self):
        valid_hex_colors = ['aaabbb', 'cccdddee', '000000', 'ffffff00']
        for hex_col in valid_hex_colors:
            opts = fonts2svg.get_options(['-c', hex_col, self.font_path])
            self.assertEqual(opts.colors_list, [hex_col])

    def test_get_options_split_comma_sequence(self):
        invalid_comma_seqs = ['a,b', 'a, b', 'a ,b', 'a , b']
        for seq in invalid_comma_seqs:
            opts = fonts2svg.get_options(['-g', seq, self.font_path])
            self.assertEqual(opts.gnames_to_generate, ['a', 'b'])

    def test_get_options_addsvg_multiple_fonts(self):
        args = [XTRA_ARG, self.font_path, self.font_path]
        with self.assertRaises(SystemExit) as cm:
            addsvg.get_options(args)
        self.assertEqual(cm.exception.code, 2)

    def test_get_options_dumpsvg_multiple_fonts(self):
        args = [self.font_path, self.font_path]
        with self.assertRaises(SystemExit) as cm:
            dumpsvg.get_options(args)
        self.assertEqual(cm.exception.code, 2)

    def test_get_options_fonts2svg_multiple_fonts(self):
        args = [self.font_path, self.font_path, self.font_path]
        opts = fonts2svg.get_options(args)
        self.assertEqual(len(opts.font_paths_list), 3)

    def test_get_options_adjust_viewbox(self):
        opts = fonts2svg.get_options(['-av', 'xfont'])
        self.assertTrue(opts.adjust_view_box_to_glyph)

    def test_get_options_adjust_viewbox_2(self):
        opts = fonts2svg.get_options(['--adjust-viewbox', 'xfont'])
        self.assertTrue(opts.adjust_view_box_to_glyph)

    def test_get_options_adjust_viewbox_not_passed(self):
        opts = fonts2svg.get_options(['xfont'])
        self.assertFalse(opts.adjust_view_box_to_glyph)


if __name__ == "__main__":
    sys.exit(unittest.main())
