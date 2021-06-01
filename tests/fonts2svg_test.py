# Copyright 2021 Adobe. All rights reserved.

from opentypesvg.fonts2svg import viewbox_settings


import os
import pytest


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
])
def test_adjust_to_viewbox(file_name, expected, fixtures_dir):
    font_path = os.path.join(fixtures_dir, file_name)
    viewbox = viewbox_settings(font_path, True)
    assert viewbox == expected


def test_adjust_to_viewbox_default(base_font_path):
    viewbox = viewbox_settings(base_font_path, False)
    assert viewbox == "0 -1000 1000 1000"
