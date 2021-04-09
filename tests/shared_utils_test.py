# Copyright 2018 Adobe. All rights reserved.

import os
import shutil
import sys
import tempfile
import unittest
from io import StringIO

from opentypesvg import utils as shared_utils


class SharedUtilsTest(unittest.TestCase):

    @staticmethod
    def write_binary_file(file_path, data):
        with open(file_path, "wb") as f:
            f.write(data)

    @staticmethod
    def reset_stream(stream):
        stream.seek(0)
        stream.truncate(0)
        return stream

# -----
# Tests
# -----

    def test_read_write_file(self):
        content = '1st line\n2nd line\n3rd line'
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shared_utils.write_file(tmp.name, content)
            result = shared_utils.read_file(tmp.name)
            self.assertEqual(result.splitlines()[1], '2nd line')

    def test_get_font_format(self):
        in_out = {"OTTO": "OTF",
                  "\x00\x01\x00\x00": "TTF",
                  "true": "TTF",
                  "wOFF": "WOFF",
                  "wOF2": "WOFF2",
                  "blah": None}
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            for key, val in in_out.items():
                data = bytearray(key, encoding="utf-8")
                self.write_binary_file(tmp.name, data)
                result = shared_utils.get_font_format(tmp.name)
                self.assertEqual(result, val)

    def test_final_message(self):
        stream = sys.stdout = StringIO()
        shared_utils.final_message(0)
        self.assertEqual(stream.getvalue().strip(), 'No SVG files saved.')

        self.reset_stream(stream)
        shared_utils.final_message(1)
        self.assertEqual(stream.getvalue().strip(), '1 SVG file saved.')

        self.reset_stream(stream)
        shared_utils.final_message(2)
        self.assertEqual(stream.getvalue().strip(), '2 SVG files saved.')

    def test_create_folder(self):
        folder_path = 'new_folder'
        shared_utils.create_folder(folder_path)
        self.assertTrue(os.path.isdir(folder_path))

        # change just-created folder to be unaccessible
        os.chmod(folder_path, 0o0)

        # try creating a folder inside the unaccessible one
        # NOTE: apparently there's no way to make a Windows folder
        # read-only programmatically, so first check if the parent
        # folder cannot be accessed. See Windows note in os.chmod()
        # https://docs.python.org/3/library/os.html#os.chmod
        blocked_folder_path = os.path.join(folder_path, 'blocked_folder')
        if not os.access(folder_path, os.W_OK):
            with self.assertRaises(OSError) as cm:
                shared_utils.create_folder(blocked_folder_path)
            self.assertEqual(cm.exception.errno, 13)

        # try creating a folder with the same name as an existing file
        file_path = 'new_file'
        with open(file_path, "w+"):
            with self.assertRaises(OSError) as cm:
                shared_utils.create_folder(file_path)
            self.assertEqual(cm.exception.errno, 17)

        # remove artifacts
        os.chmod(folder_path, 0o755)
        if os.path.exists(folder_path):
            os.rmdir(folder_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_create_nested_folder(self):
        nested_folder_path = 'folder_path'
        result = shared_utils.create_nested_folder(nested_folder_path, None)
        self.assertEqual(result, nested_folder_path)

        main_folder_path = 'main_folder'
        nested_folder_path = os.path.join(main_folder_path,
                                          shared_utils.NESTED_FOLDER_NAME)
        shared_utils.create_nested_folder(None, main_folder_path)
        self.assertTrue(os.path.isdir(nested_folder_path))
        # remove artifact
        if os.path.exists(nested_folder_path):
            shutil.rmtree(main_folder_path)

    def test_get_output_folder_path(self):
        folder_path = 'fonts'
        result = shared_utils.get_output_folder_path(folder_path, None)
        self.assertEqual(os.path.basename(result), folder_path)

        font_path = 'font'
        result = shared_utils.get_output_folder_path(None, font_path)
        self.assertEqual(os.path.basename(result),
                         shared_utils.SVG_FOLDER_NAME)

    def test_get_gnames_to_save_in_nested_folder(self):
        result = shared_utils.get_gnames_to_save_in_nested_folder(
            ['a', 'A', 'B', 'b', 'c'])
        self.assertEqual(result, ['A', 'b'])


if __name__ == "__main__":
    sys.exit(unittest.main())
