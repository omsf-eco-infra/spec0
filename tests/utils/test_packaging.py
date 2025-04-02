from packaging.version import Version

import pytest

from spec0.utils.packaging import *


@pytest.mark.parametrize(
    "version_str,expected",
    [
        ("1.2", "1.2"),  # For "1.2", epoch is 0, so just "major.minor"
        ("1!1.2", "1!1.2"),  # For "1!1.2", non-zero epoch is included
        ("0.3.4", "0.3"),  # For "0.3.4", only major and minor are used
    ],
)
def test_major_minor_str(version_str, expected):
    v = Version(version_str)
    result = major_minor_str(v)
    assert result == expected
