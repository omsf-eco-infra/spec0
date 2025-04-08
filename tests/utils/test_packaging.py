from packaging.version import Version
from packaging.specifiers import SpecifierSet

import pytest

from spec0.utils.packaging import *


@pytest.mark.parametrize(
    "pkg_info, include_upper_bound, expected",
    [
        # Single release: only one version provided.
        (
            {"releases": [{"version": Version("1.2.3")}]},
            True,
            ">=1.2.3,<2.0",
        ),
        (
            {"releases": [{"version": Version("1.2.3")}]},
            False,
            ">=1.2.3",
        ),
        # Multiple releases with the same major version.
        (
            {
                "releases": [
                    {"version": Version("1.2.3")},
                    {"version": Version("1.3.0")},
                ]
            },
            True,
            ">=1.2.3,<2.0",
        ),
        (
            {
                "releases": [
                    {"version": Version("1.2.3")},
                    {"version": Version("1.3.0")},
                ]
            },
            False,
            ">=1.2.3",
        ),
        # Multiple releases with different major versions.
        (
            {
                "releases": [
                    {"version": Version("1.2.3")},
                    {"version": Version("2.0.0")},
                ]
            },
            True,
            ">=1.2.3,<3.0",
        ),
        (
            {
                "releases": [
                    {"version": Version("1.2.3")},
                    {"version": Version("2.0.0")},
                ]
            },
            False,
            ">=1.2.3",
        ),
        # Releases with a nonzero epoch.
        (
            {
                "releases": [
                    {"version": Version("2!1.0")},
                    {"version": Version("2!3.0")},
                ]
            },
            True,
            ">=2!1.0,<2!4.0",
        ),
        (
            {
                "releases": [
                    {"version": Version("2!1.0")},
                    {"version": Version("2!3.0")},
                ]
            },
            False,
            ">=2!1.0",
        ),
    ],
)
def test_make_specifier(pkg_info, include_upper_bound, expected):
    spec = make_specifier(pkg_info, include_upper_bound)
    assert spec == SpecifierSet(expected)


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
