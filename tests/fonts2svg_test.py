# Copyright 2021 Adobe. All rights reserved.

from opentypesvg.fonts2svg import viewbox_settings


def test_adjust_to_viewbox(base_font_path, capsys):
    viewbox = viewbox_settings(base_font_path, True)
    assert viewbox == "-168 -850 998 1151"


def test_adjust_to_viewbox_default(base_font_path, capsys):
    viewbox = viewbox_settings(base_font_path, False)
    assert viewbox == "0 -1000 1000 1000"
