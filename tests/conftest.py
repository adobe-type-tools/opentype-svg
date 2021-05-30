# Copyright 2021 Adobe. All rights reserved.

import os
import pytest


@pytest.fixture
def fonts_dir():
    root_dir = os.path.dirname(os.path.dirname(__file__))
    yield os.path.join(root_dir, 'fonts')


@pytest.fixture
def base_font_path(fonts_dir):
    yield os.path.join(fonts_dir, 'Zebrawood.otf')


@pytest.fixture
def fixtures_dir():
    yield os.path.join(os.path.dirname(__file__), 'fixtures')
