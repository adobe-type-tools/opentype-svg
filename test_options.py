from __future__ import print_function, division, absolute_import

import os
import sys
import unittest

import addSVGtable
import fonts2svg
import dumpSVGtable

have_brotli = False
try:
    import brotli
    have_brotli = True
except ImportError:
    pass


ALL_TOOLS = (dumpSVGtable, fonts2svg, addSVGtable)
XTRA_ARGS = ['-s', 'fonts']


class OptionsTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

    def setUp(self):
        self.font_path = os.path.join('fonts', 'Zebrawood.otf')

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

    def test_get_options_required_option(self):
        # -s option is required for addSVGtable
        with self.assertRaises(SystemExit) as cm:
            addSVGtable.get_options(['xfont'])
        self.assertEqual(cm.exception.code, 2)

    def test_get_options_invalid_folder_path(self):
        with self.assertRaises(SystemExit) as cm:
            addSVGtable.get_options(['-s', 'xfolder', 'xfont'])
        self.assertEqual(cm.exception.code, 1)

    def test_get_options_bogus_option(self):
        args = ['--bogus', 'xfont']
        for tool in ALL_TOOLS:
            # -s option is required for addSVGtable
            if tool is addSVGtable:
                args.extend(XTRA_ARGS)
            with self.assertRaises(SystemExit) as cm:
                tool.get_options(args)
            self.assertEqual(cm.exception.code, 2)

    def test_get_options_invalid_font_path(self):
        args = ['xfont']
        for tool in ALL_TOOLS:
            if tool is addSVGtable:
                args.extend(XTRA_ARGS)
            opts = tool.get_options(args)
            self.assertEqual(opts.font_paths_list, [])

    def test_get_options_not_a_font_path(self):
        not_a_font_path = os.path.join('fonts', 'test.html')
        args = [not_a_font_path]
        for tool in ALL_TOOLS:
            if tool is addSVGtable:
                args.extend(XTRA_ARGS)
            opts = tool.get_options(args)
            self.assertEqual(opts.font_paths_list, [])

    def test_get_options_good_font_path(self):
        args = [self.font_path]
        for tool in ALL_TOOLS:
            if tool is addSVGtable:
                args.extend(XTRA_ARGS)
            opts = tool.get_options(args)
            self.assertEqual(os.path.basename(opts.font_paths_list[0]),
                             os.path.basename(self.font_path))

    @unittest.skipIf(have_brotli, "brotli module is installed")
    def test_get_options_addSVGtable_brotli_missing(self):
        with self.assertRaises(SystemExit) as cm:
            addSVGtable.get_options(XTRA_ARGS + ['-w', self.font_path])
        self.assertEqual(cm.exception.code, 1)

    @unittest.skipIf(not have_brotli, "brotli module is not installed")
    def test_get_options_addSVGtable_store_true_opts(self):
        args = XTRA_ARGS + ['-w', '-z', self.font_path]
        opts = addSVGtable.get_options(args)
        attr = ('make_font_copy', 'strip_viewbox',
                'generate_woffs', 'compress_svgs')
        result = list(set([getattr(opts, name) for name in attr]))[0]
        self.assertEqual(result, True)

    def test_get_options_addSVGtable_store_false_opts(self):
        args = XTRA_ARGS + ['-m', '-k', self.font_path]
        opts = addSVGtable.get_options(args)
        attr = ('make_font_copy', 'strip_viewbox',
                'generate_woffs', 'compress_svgs')
        result = list(set([getattr(opts, name) for name in attr]))[0]
        self.assertEqual(result, False)

    def test_get_options_dumpSVGtable_store_true_opts(self):
        args = ['-r', self.font_path]
        opts = dumpSVGtable.get_options(args)
        result = getattr(opts, 'reset_viewbox')
        self.assertEqual(result, True)

    def test_get_options_fonts2svg_store_true_opts(self):
        args = ['-u', self.font_path]
        opts = fonts2svg.get_options(args)
        result = getattr(opts, 'glyphsets_union')
        self.assertEqual(result, True)

    def test_get_options_addSVGtable_opts_defaults(self):
        dflt = {'make_font_copy': True,
                'strip_viewbox': True,
                'generate_woffs': False,
                'gnames_to_exclude': [],
                'compress_svgs': False}
        args = XTRA_ARGS + [self.font_path]
        opts = addSVGtable.get_options(args)
        for key, val in dflt.items():
            self.assertEqual(getattr(opts, key), val)

    def test_get_options_dumpSVGtable_opts_defaults(self):
        dflt = {'output_folder_path': None,
                'reset_viewbox': False,
                'gnames_to_generate': [],
                'gnames_to_exclude': []}
        args = [self.font_path]
        opts = dumpSVGtable.get_options(args)
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

    def test_get_options_addSVGtable_multiple_fonts(self):
        args = XTRA_ARGS + [self.font_path, self.font_path]
        with self.assertRaises(SystemExit) as cm:
            addSVGtable.get_options(args)
        self.assertEqual(cm.exception.code, 2)

    def test_get_options_dumpSVGtable_multiple_fonts(self):
        args = [self.font_path, self.font_path]
        with self.assertRaises(SystemExit) as cm:
            dumpSVGtable.get_options(args)
        self.assertEqual(cm.exception.code, 2)

    def test_get_options_fonts2svg_multiple_fonts(self):
        args = [self.font_path, self.font_path, self.font_path]
        opts = fonts2svg.get_options(args)
        self.assertEqual(len(opts.font_paths_list), 3)


if __name__ == "__main__":
    sys.exit(unittest.main())
