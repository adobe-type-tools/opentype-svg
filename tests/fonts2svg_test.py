# Copyright 2021 Adobe. All rights reserved.

import filecmp
import os
import pytest
import shutil

from opentypesvg.fonts2svg import viewbox_settings, main
from opentypesvg.utils import SVG_FOLDER_NAME, NESTED_FOLDER_NAME


@pytest.mark.parametrize('file_name, expected', [
    ("1.ttf", "309 -1108 360 638"),
    ("2.ttf", "-904 -1110 416 650"),
    ("3.ttf", "-824 310 420 662"),
    ("4.ttf", "197 342 452 638"),
    ("12.ttf", "-904 -1110 1573 650"),
    ("13.ttf", "-824 -1108 1493 2080"),
    ("14.ttf", "197 -1108 472 2088"),
    ("23.ttf", "-904 -1110 500 2082"),
    ("24.ttf", "-904 -1110 1553 2090"),
    ("34.ttf", "-824 310 1473 670"),
    ("1234.ttf", "-904 -1110 1573 2090"),
    ("no_head_table.ttf", "0 -1000 1000 1000"),
])
def test_adjust_to_viewbox(file_name, expected, fixtures_dir):
    font_path = os.path.join(fixtures_dir, file_name)
    viewbox = viewbox_settings(font_path, True)
    assert viewbox == expected


def test_adjust_to_viewbox_default(base_font_path):
    viewbox = viewbox_settings(base_font_path, False)
    assert viewbox == "0 -1000 1000 1000"


def test_main(shadow_font_path, fill_font_path, dots_font_path, fixtures_dir,
              tmp_path):
    """
    Generate SVG files to a temp folder and compare with expected fixtures.
    """
    output_folder = str(tmp_path)

    main(['-c', '99ccff77,ff0066aA,cc0066FF',
          shadow_font_path, fill_font_path, dots_font_path,
          '-o', output_folder])

    for gname in ('A', 'Y', 'Z'):
        svg_file_name = f'{gname}.svg'
        expected_svg_path = os.path.join(fixtures_dir, svg_file_name)
        test_svg_path = os.path.join(output_folder, svg_file_name)
        assert os.path.exists(test_svg_path)
        assert filecmp.cmp(test_svg_path, expected_svg_path)


def test_main_invalid_path(capsys):
    file_name = 'not_a_file'
    exit_val = main([file_name])
    captured = capsys.readouterr()
    assert captured.err == (f"ERROR: {os.path.realpath(file_name)} "
                            "is not a valid font file path.\n")
    assert exit_val == 1


def test_main_bad_font(fixtures_dir, capsys):
    font_path = os.path.join(fixtures_dir, 'no_glyf_table.ttf')
    exit_val = main(['-c', '00ff00', font_path])
    captured = capsys.readouterr()
    assert captured.err == (f"ERROR: {os.path.realpath(font_path)} "
                            "cannot be processed.\n")
    assert exit_val == 1


def test_main_svgs_folder(fixtures_dir, tmp_path):
    """
    Confirm that 'SVG_FOLDER_NAME' is created when output folder is not
    provided.
    """
    font_name = 'ab.ttf'
    temp_dir = str(tmp_path)
    fixt_font_path = os.path.join(fixtures_dir, font_name)
    temp_font_path = os.path.join(temp_dir, font_name)

    # copy test font to temp dir
    assert not os.path.exists(temp_font_path)
    shutil.copy2(fixt_font_path, temp_font_path)
    assert os.path.exists(temp_font_path)

    # confirm that SVG_FOLDER_NAME doesn't exist
    svgs_dir = os.path.join(temp_dir, SVG_FOLDER_NAME)
    assert not os.path.exists(svgs_dir)

    main(['-c', '009900', temp_font_path])

    assert os.path.isdir(svgs_dir)
    assert os.path.exists(os.path.join(temp_dir, SVG_FOLDER_NAME, 'a.svg'))

    # test that overlapping contour points are skipped when the glyph is
    # written to SVG path
    svg_file_name = 'b.svg'
    test_svg_path = os.path.join(temp_dir, SVG_FOLDER_NAME, svg_file_name)
    assert os.path.exists(test_svg_path)
    expected_svg_path = os.path.join(fixtures_dir, svg_file_name)
    assert filecmp.cmp(test_svg_path, expected_svg_path)


def test_main_nested_folder(fixtures_dir, tmp_path):
    """
    Confirm that 'NESTED_FOLDER_NAME' is created when there are glyph names
    that can produce conflicting files in case-insensitive systems.
    """
    font_name = 'aA.ttf'
    temp_dir = str(tmp_path)
    fixt_font_path = os.path.join(fixtures_dir, font_name)

    # confirm that NESTED_FOLDER_NAME doesn't exist
    more_svgs_dir = os.path.join(temp_dir, NESTED_FOLDER_NAME)
    assert not os.path.exists(more_svgs_dir)

    main(['-c', '009900', fixt_font_path, '-o', temp_dir])

    assert os.path.isdir(more_svgs_dir)
    assert os.path.exists(os.path.join(temp_dir, 'A.svg'))
    assert os.path.exists(os.path.join(temp_dir, NESTED_FOLDER_NAME, 'a.svg'))


def test_main_blank_glyph(fixtures_dir, tmp_path):
    """
    Confirm that SVG files are not generated for glyphs without outlines.
    """
    font_name = 'blank_glyph.ttf'
    temp_dir = str(tmp_path)
    fixt_font_path = os.path.join(fixtures_dir, font_name)

    main(['-c', '009900', fixt_font_path, '-o', temp_dir])

    assert os.path.exists(os.path.join(temp_dir, 'a.svg'))
    assert not os.path.exists(os.path.join(temp_dir, 'b.svg'))


def test_main_g_opt_and_no_colors(shadow_font_path, capsys, tmp_path):
    """
    Only generate 'A.svg' and don't specify the hex color.
    """
    output_folder = str(tmp_path)

    main([shadow_font_path, '-g', 'A', '-o', output_folder])

    assert os.path.exists(os.path.join(output_folder, 'A.svg'))
    assert not os.path.exists(os.path.join(output_folder, 'Y.svg'))
    assert not os.path.exists(os.path.join(output_folder, 'Z.svg'))

    captured = capsys.readouterr()
    assert captured.err == (
        "WARNING: The list of colors was extended with 1 #000000 value(s).\n")


def test_main_x_opt_and_extra_colors(shadow_font_path, capsys, tmp_path):
    """
    Exclude generating 'A.svg' and specify too many hex colors.
    Also specify alpha parameter of hex colors.
    """
    output_folder = str(tmp_path)

    main([shadow_font_path, shadow_font_path,
          '-x', 'A', '-c', '99ccff,ff0066,cc0066',
          '-o', output_folder])

    assert not os.path.exists(os.path.join(output_folder, 'A.svg'))
    assert os.path.exists(os.path.join(output_folder, 'Y.svg'))
    assert os.path.exists(os.path.join(output_folder, 'Z.svg'))

    captured = capsys.readouterr()
    assert captured.err == ("WARNING: The list of colors got the last 1 "
                            "value(s) truncated: cc0066\n")


def test_main_exclude_all_glyphs(shadow_font_path, capsys, tmp_path):
    output_folder = str(tmp_path)

    exit_val = main([shadow_font_path, '-x', 'Z,Y,A', '-c', 'ff00ff',
                     '-o', output_folder])

    assert not os.path.exists(os.path.join(output_folder, 'A.svg'))
    assert not os.path.exists(os.path.join(output_folder, 'Y.svg'))
    assert not os.path.exists(os.path.join(output_folder, 'Z.svg'))

    captured = capsys.readouterr()
    assert captured.out == ("No SVG files saved.\n")

    assert exit_val == 0


def test_main_one_glyph_in_common(fixtures_dir, tmp_path):
    """
    The fonts have one glyph in common; the default is intersection of names,
    so only one SVG should be saved.
    """
    ab_font_path = os.path.join(fixtures_dir, 'ab.ttf')
    bc_font_path = os.path.join(fixtures_dir, 'bc.ttf')
    output_folder = str(tmp_path)

    main([ab_font_path, bc_font_path, '-c', 'ff00ff,00ff00',
          '-o', output_folder])

    assert not os.path.exists(os.path.join(output_folder, 'a.svg'))
    assert os.path.exists(os.path.join(output_folder, 'b.svg'))
    assert not os.path.exists(os.path.join(output_folder, 'c.svg'))


def test_main_u_opt_one_glyph_in_common(fixtures_dir, tmp_path):
    """
    The fonts have one glyph in common; the option is to use the union of
    names, so all three SVGs should be saved.
    """
    ab_font_path = os.path.join(fixtures_dir, 'ab.ttf')
    bc_font_path = os.path.join(fixtures_dir, 'bc.ttf')
    output_folder = str(tmp_path)

    main([ab_font_path, bc_font_path, '-c', 'ff00ff,00ff00', '-u',
          '-o', output_folder])

    assert os.path.exists(os.path.join(output_folder, 'a.svg'))
    assert os.path.exists(os.path.join(output_folder, 'b.svg'))
    assert os.path.exists(os.path.join(output_folder, 'c.svg'))


def test_main_a_opt_one_glyph_in_common(fixtures_dir, tmp_path):
    """
    The fonts have one glyph in common; the default is intersection of names,
    but one more name is added to the list, so two SVGs should be saved.
    """
    ab_font_path = os.path.join(fixtures_dir, 'ab.ttf')
    bc_font_path = os.path.join(fixtures_dir, 'bc.ttf')
    output_folder = str(tmp_path)

    main([ab_font_path, bc_font_path, '-c', 'ff00ff,00ff00', '-a', 'a',
          '-o', output_folder])

    assert os.path.exists(os.path.join(output_folder, 'a.svg'))
    assert os.path.exists(os.path.join(output_folder, 'b.svg'))
    assert not os.path.exists(os.path.join(output_folder, 'c.svg'))


def test_main_no_glyphs_in_common(fixtures_dir, capsys, tmp_path):
    """
    The fonts have no glyphs in common; the default is intersection of names,
    so no SVGs should be saved.
    """
    ab_font_path = os.path.join(fixtures_dir, 'ab.ttf')
    cd_font_path = os.path.join(fixtures_dir, 'cd.ttf')
    output_folder = str(tmp_path)

    exit_val = main([ab_font_path, cd_font_path, '-c', 'ff00ff,00ff00',
                     '-o', output_folder])

    assert not os.path.exists(os.path.join(output_folder, 'a.svg'))
    assert not os.path.exists(os.path.join(output_folder, 'b.svg'))
    assert not os.path.exists(os.path.join(output_folder, 'c.svg'))
    assert not os.path.exists(os.path.join(output_folder, 'd.svg'))

    captured = capsys.readouterr()
    assert captured.out == (
        "The fonts and options provided can't produce any SVG files.\n")

    assert exit_val == 1
