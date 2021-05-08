# Copyright 2021 Adobe. All rights reserved.

import pytest

from opentypesvg.dumpsvg import main


def test_font_without_svg_table(base_font_path, capsys):
    with pytest.raises(SystemExit):
        main([base_font_path])
    captured = capsys.readouterr()
    assert captured.err == "ERROR: The font does not have the SVG table.\n"
