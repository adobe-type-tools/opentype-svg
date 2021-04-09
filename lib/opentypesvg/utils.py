# Copyright 2016 Adobe. All rights reserved.

"""
Module that contains shared functionality.
"""

import os
import sys


SVG_FOLDER_NAME = "SVGs"
NESTED_FOLDER_NAME = "_moreSVGs_"


def read_file(file_path):
    with open(file_path, "r") as f:
        return f.read()


def write_file(file_path, data):
    with open(file_path, "w") as f:
        f.write(data)


def get_font_format(font_file_path):
    with open(font_file_path, "rb") as f:
        head = f.read(4).decode()

    if head == "OTTO":
        return "OTF"
    elif head in ("\x00\x01\x00\x00", "true"):
        return "TTF"
    elif head == "wOFF":
        return "WOFF"
    elif head == "wOF2":
        return "WOFF2"
    return None


def validate_font_paths(paths_list):
    validated_paths_list = []
    for path in paths_list:
        path = os.path.realpath(path)
        if (os.path.isfile(path) and get_font_format(path) in
                ['OTF', 'TTF', 'WOFF', 'WOFF2']):
            validated_paths_list.append(path)
        else:
            print("ERROR: {} is not a valid font file path.".format(path),
                  file=sys.stderr)
    return validated_paths_list


def split_comma_sequence(comma_str):
    return [item.strip() for item in comma_str.split(',')]


def final_message(num_files_saved):
    if not num_files_saved:
        num_files_saved = 'No'
    plural = 's' if num_files_saved != 1 else ''
    print("{} SVG file{} saved.".format(num_files_saved, plural),
          file=sys.stdout)


def create_folder(folder_path):
    try:
        os.makedirs(folder_path)
    except OSError:
        if not os.path.isdir(folder_path):
            raise


def create_nested_folder(nested_folder_path, main_folder_path):
    """
    Creates a nested folder and returns its path.
    This additional folder is created when file names conflict.
    """
    if not nested_folder_path:
        nested_folder_path = os.path.join(main_folder_path, NESTED_FOLDER_NAME)
        create_folder(nested_folder_path)
    return nested_folder_path


def validate_folder_path(folder_path):
    """
    Validates that the path is a folder.
    Returns the complete path.
    """
    path = os.path.realpath(folder_path)
    if os.path.isdir(path):
        return path
    else:
        print("ERROR: {} is not a valid folder path.".format(path),
              file=sys.stderr)
        sys.exit(1)


def get_output_folder_path(provided_folder_path, first_font_path):
    """
    If the path to the output folder was NOT provided, create
    a folder in the same directory where the first font is.
    If the path was provided, validate it.
    Returns a valid output folder.
    """
    if provided_folder_path:
        return validate_folder_path(provided_folder_path)
    return os.path.join(os.path.dirname(first_font_path), SVG_FOLDER_NAME)


def get_gnames_to_save_in_nested_folder(gnames_list):
    """
    On case-insensitive systems the SVG files cannot be all saved to the
    same folder otherwise a.svg and A.svg would be written over each other,
    for example. So, pre-process the list of glyph names to find which ones
    step on each other, and save half of them in a nested folder. This
    approach won't handle the case where a.svg and A.svg are NOT generated
    on the same run, but that's fine; the user will have to handle that.
    Also, the process below assumes that there are no more than 2 conflicts
    per name, i.e. it will handle "the/The" but not "the/The/THE/...";
    this shouldn't be a problem in 99% of the time.
    Returns list of glyph names that need to be saved in a nested folder.
    """
    unique_names_set = set()
    gnames_to_save_in_nested_folder = []
    for gname in gnames_list:
        if gname.lower() in unique_names_set:
            gnames_to_save_in_nested_folder.append(gname)
        unique_names_set.add(gname.lower())
    return gnames_to_save_in_nested_folder
